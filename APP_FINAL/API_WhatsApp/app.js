const { Client, MessageMedia, LocalAuth } = require("whatsapp-web.js");
const { body, validationResult } = require("express-validator");
const { formatoNumeroTelefono } = require("./config/formatoNumero");

// Imports
const express = require("express");
const socketIo = require("socket.io");
const qrcode = require("qrcode");
const http = require("http");
const fs = require("fs");
const fileUpload = require("express-fileupload");
const axios = require("axios");
const mime = require("mime-types");

//Declarations of variables
const app = express();
const server = http.createServer(app);
const io = socketIo(server);

const port = process.env.PORT || 5001;

app.use(express.json());
app.use(
  express.urlencoded({
    extended: true,
  }),
);

app.use(
  fileUpload({
    debug: false,
  }),
);

app.get("/", (req, res) => {
  res.sendFile("/public/index.html", {
    root: __dirname,
  });
});

const client = new Client({
  restartOnAuthFail: true,
  puppeteer: {
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-accelerated-2d-canvas",
      "--disable-gpu",
    ],
  },
  // session: sessionCfg,
  authStrategy: new LocalAuth(),
});

client.on("message", async (msg) => {
  const contact = await msg.getContact();
  const nombre = contact.pushname || contact.name;
  const telefono = msg.from.replace("@c.us", "");

  // console.log(`📱 Número: ${telefono}`);
  // console.log(`👤 Nombre: ${nombre}`);
  // console.log(`💬 Mensaje: ${msg.body}`);

  console.log(`👤 Nombre: ${nombre} - 📱 Número: ${telefono}`);
  console.log(`💬 Mensaje: ${msg.body}`);

  if (msg.body === "Hola") {
    msg.reply("Hola, muy buen día en que puedo ayudarte");
    client.getChats().then((chats) => {
      console.log(chats[0]);
    });
  } else if (msg.body === "Buenos días") {
    // msg.sendMessage(msg.from, "Buenos días en que puedo ayudarte");
    msg.reply("Buenos días en que puedo ayudarte");

    // si es en grupos donde se verifica el numero de telefono
  } else if (msg.body === "!groups") {
    client
      .getChats()
      .then((chats) => {
        const grupos = chats.filter((m) => m.isGroup);

        if (grupos.length === 0) {
          msg.reply("No hay grupos");
        } else {
          let responderMensaje = `📋 *TUS GRUPOS* (${grupos.length} encontrados)\n\n`;

          grupos.forEach((grupo, i) => {
            responderMensaje += `*${i + 1}. ${grupo.name}*\n`;
            responderMensaje += `🆔 ID: \`${grupo.id._serialized}\`\n`;
            responderMensaje += `👥 Participantes: ${grupo.participants?.length ?? "?"}\n`;
            responderMensaje += `🔇 Silenciado: ${grupo.isMuted ? "Sí" : "No"}\n\n`;
          });

          responderMensaje +=
            "_Usa el ID para enviar mensajes al grupo vía API._";
          msg.reply(responderMensaje);
        }
      })
      .catch((err) => {
        console.error(err);
        msg.reply("❌ Error al obtener los grupos");
      });
  }
});

client.initialize();

io.on("connection", (socket) => {
  socket.emit("message", "Conectando....!");

  client.on("qr", (qr) => {
    console.log("QR received", qr);
    qrcode.toDataURL(qr, (err, url) => {
      socket.emit("qr", url);
      socket.emit("message", "Código QR recibido, escanear por favor!");
    });
  });

  //Para concectar el cliente
  client.on("ready", () => {
    console.log("Usuario conectado");
    socket.emit("ready", "WhatsApp está listo");
    socket.emit("message", "Usuario conectado");
  });

  client.on("authenticated", () => {
    socket.emit("authenticated", "WhatsApp está autenticado");
    socket.emit("message", "WhatsApp está autenticado");
    console.log("AUTENTICADO");
  });

  //Para el fallo de inicio de session el WhatasApp
  client.on("auth_failure", (session) => {
    socket.emit("message", "Error de autenticación, reiniciando...");
    console.log("ERROR REINICIANDO AUTTENTICACION");
  });

  //Para desconectarse al  WhatasApp
  client.on("disconnected", (reason) => {
    socket.emit("message", "Whatsapp está desconectado!");
    client.destroy();
    client.initialize();
  });
});

const verNumeroRegistrado = async (numero) => {
  const esRegistrado = await client.isRegisteredUser(numero);
  return esRegistrado;
};

/**
 * //NOTE:  Enviar mensajes por POST------------------------------------------>
 */
app.post(
  "/enviar-mensaje",
  [body("number").notEmpty(), body("message").notEmpty()],
  async (req, res) => {
    const errores = validationResult(req).formatWith(({ msg }) => {
      return msg;
    });

    //validamos si es diferente de vacio
    if (!errores.isEmpty()) {
      return res.status(422).json({
        status: false,
        message: errores.mapped(),
        // message: "No se puede conectar",
      });
    }

    const number = formatoNumeroTelefono(req.body.number);
    const message = req.body.message;
    const esNumeroRegistrado = await verNumeroRegistrado(number);

    // Si esNumeroRegistrado es falso || osea que si el numero no esta registrado todavia
    if (!esNumeroRegistrado) {
      return res.status(422).json({
        status: false,
        message: "El número ingresado no está registrado",
      });
    }

    client
      .sendMessage(number, message)
      .then((response) => {
        res.status(200).json({
          status: true,
          response: response,
        });
      })
      .catch((err) => {
        res.status(500).json({
          status: false,
          response: err,
        });
      });
  },
);

/**
 * //NOTE: Enviar archivos para un numero------------------------------------->
 */
app.post("/enviar-archivo", async (req, res) => {
  try {
    if (!req.files || Object.keys(req.files).length === 0) {
      return res.status(422).json({
        status: false,
        message: "No se subió ningún archivo",
      });
    }

    const number = formatoNumeroTelefono(req.body.number);
    const file = req.files.file;
    const caption = req.body.caption || `Archivo enviado: ${file.name}`;

    const media = new MessageMedia(
      file.mimetype,
      file.data.toString("base64"),
      file.name,
    );

    const response = await client.sendMessage(number, media, { caption });

    res.status(200).json({
      status: true,
      message: "Archivo enviado con éxito",
      response: response.from,
    });
  } catch (error) {
    res.status(500).json({
      status: false,
      message: "Error al enviar archivo: " + error.message,
    });
  }
});

/*
 * //NOTE: Obtener grupos de whatsapp--------------------------------------------->
 */
app.get("/grupos", async (req, res) => {
  try {
    const chats = await client.getChats();
    const grupos = chats
      .filter((chat) => chat.isGroup)
      .map((grupo) => ({
        id: grupo.id._serialized,
        name: grupo.name,
        participantes: grupo.participants?.length ?? 0,
      }));

    res.status(200).json({ status: true, grupos });
  } catch (err) {
    res.status(500).json({ status: false, message: err.message });
  }
});

const buscarGrupoPorNombre = async (req, res) => {
  const grupo = await client.getChats().then((chats) => {
    return chats.find(
      (chts) => chts.isGroup && chts.name.toLowerCase() === name.toLowerCase(),
    );
  });

  return grupo;
};

/**
 * //NOTE: Enviar mensaje por grupo de whatsapp--------------------------------------------->
 */
app.post(
  "/enviarMensajeEnGrupo",
  [
    body("id").custom((value, { req }) => {
      if (!value && !req.body.name) {
        throw new Error("Invalid value, you can use `ID` or `name`");
      }
      return true;
    }),
    body("message").notEmpty(),
  ],
  async (req, res) => {
    const errores = validationResult(req).formatWith(({ msg }) => {
      return msg;
    });

    if (!errores.isEmpty()) {
      return res.status(422).json({
        status: false,
        message: errores.mapped(),
      });
    }

    let chatId = req.body.id;
    const groupName = req.body.name;
    const message = req.body.message;

    if (!chatId) {
      const group = await buscarGrupoPorNombre(groupName);
      if (!group) {
        return res.status(422).json({
          status: false,
          message: "NO group found with name:",
          groupName,
        });
      }
      chatId = group.id._serialized;
    }

    client
      .sendMessage(chatId, message)
      .then((response) => {
        res.status(200).json({
          status: true,
          response: response,
        });
      })
      .catch((err) => {
        res.status(500).json({
          status: false,
          response: err,
        });
      });
  },
);

/*
 * //NOTE: Enviar archivos por grupo de whatsapp--------------------------------------------->
 */

app.post(
  "/enviarArchivoGrupo2",
  [
    body("id").custom((value, { req }) => {
      if (!value && !req.body.name) {
        throw new Error("Invalid value, you can use `ID` or `name`");
      }
      return true;
    }),
    body("message").notEmpty(),
  ],
  async (req, res) => {
    const errores = validationResult(req).formatWith(({ msg }) => msg);

    if (!errores.isEmpty()) {
      return res.status(422).json({ status: false, message: errores.mapped() });
    }

    let chatId = req.body.id;
    const groupName = req.body.name;
    const message = req.body.message;
    const fileUrl = req.body.file;

    let attachment, mimetype, filename;

    // ✅ Si viene archivo local (form-data)
    if (req.files && req.files.file) {
      const file = req.files.file;
      mimetype = file.mimetype;
      attachment = file.data.toString("base64");
      filename = file.name;

      // ✅ Si viene URL pública
    } else if (fileUrl) {
      try {
        const response = await axios.get(fileUrl, {
          responseType: "arraybuffer",
        });
        mimetype = response.headers["content-type"];
        attachment = response.data.toString("base64");
        filename = fileUrl.split("/").pop() || "Media";
      } catch (e) {
        return res.status(400).json({
          status: false,
          message: "No se pudo descargar el archivo desde la URL",
        });
      }

      // ❌ No vino ninguno
    } else {
      return res.status(422).json({
        status: false,
        message: "Se requiere un archivo o una URL",
      });
    }

    const media = new MessageMedia(mimetype, attachment, filename);

    if (!chatId) {
      const group = await buscarGrupoPorNombre(groupName);
      if (!group) {
        return res.status(422).json({
          status: false,
          message: "No se encontró el grupo",
          groupName,
        });
      }
      chatId = group.id._serialized;
    }

    client
      .sendMessage(chatId, media, { caption: message })
      .then((response) => {
        res.status(200).json({ status: true, response });
      })
      .catch((err) => {
        res.status(500).json({ status: false, response: err });
      });
  },
);

/**
 * Para ejecutar en el puerto
 */
server.listen(port, () =>
  console.log(
    "Aplicacion conrriendo el puerto 🏍🚨🚦:",
    `http://localhost:${port}/`,
  ),
);
