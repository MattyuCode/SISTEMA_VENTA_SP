import customtkinter as ctk
import sqlite3
import os
from datetime import datetime
from tkinter import messagebox, ttk
import tkinter as tk
from PIL import Image

# ── Colores Soluciones Plus ───────────────────────────────────────────────────
NAVY      = "#0d2b55"   # azul marino - sidebar fondo
ORANGE    = "#F97316"   # anaranjado  - activo / botones principales
WHITE     = "#ffffff"
GRAY_BG   = "#f4f6fb"   # fondo contenido
GRAY_CARD = "#ffffff"
BORDER    = "#e2e8f0"
TEXT_MAIN = "#0d2b55"
TEXT_MUTED= "#8a94a6"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

DB = "libreria.db"

# ── Estilo ttk (tablas) ───────────────────────────────────────────────────────
def apply_treeview_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview",
        background=WHITE, fieldbackground=WHITE,
        foreground="#374151", rowheight=26,
        borderwidth=0, font=("Segoe UI", 10))
    style.configure("Treeview.Heading",
        background=NAVY, foreground=WHITE,
        font=("Segoe UI", 10, "bold"), relief="flat", borderwidth=0)
    style.map("Treeview.Heading", background=[("active", ORANGE)])
    style.map("Treeview", background=[("selected", ORANGE)],
              foreground=[("selected", WHITE)])

# ── Base de datos ──────────────────────────────────────────────────────────────
def init_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS categorias (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS productos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_id INTEGER REFERENCES categorias(id),
            nombre      TEXT NOT NULL,
            variante    TEXT NOT NULL DEFAULT '',
            precio      REAL NOT NULL,
            stock       INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS ventas (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            total REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS detalle_venta (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id    INTEGER REFERENCES ventas(id),
            producto_id INTEGER REFERENCES productos(id),
            cantidad    INTEGER NOT NULL,
            precio_unit REAL NOT NULL,
            subtotal    REAL NOT NULL
        );
    """)
    cats = ["Lápices","Lapiceros","Cuadernos","Hojas","Adhesivos","Papelería"]
    for c in cats:
        cur.execute("INSERT OR IGNORE INTO categorias(nombre) VALUES(?)", (c,))
    con.commit()
    con.close()

def query(sql, params=(), fetchall=True):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(sql, params)
    res = cur.fetchall() if fetchall else cur.fetchone()
    con.commit()
    con.close()
    return res

def execute(sql, params=()):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(sql, params)
    lid = cur.lastrowid
    con.commit()
    con.close()
    return lid

# ── App principal ──────────────────────────────────────────────────────────────
class LibreriaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Librería - SOLUCIONES PLUS")
        self.geometry("1200x680")
        self.resizable(True, True)
        self.configure(fg_color=GRAY_BG)
        apply_treeview_style()

        # ── Sidebar azul marino ───────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, width=195, corner_radius=0,
                                    fg_color=NAVY)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Cabecera sidebar centrada
        hdr = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(20,14))

        # Ícono naranja centrado con logo o "SP"
        icon_box = ctk.CTkFrame(hdr, width=64, height=64, corner_radius=14,
                                fg_color=ORANGE)
        icon_box.pack(anchor="center")
        icon_box.pack_propagate(False)

        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SP White.png")
        if os.path.exists(logo_path):
            try:
                pil_img = Image.open(logo_path)
                pil_img.thumbnail((54, 54), Image.LANCZOS)
                self._icon_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img,
                                               size=(pil_img.width, pil_img.height))
                ctk.CTkLabel(icon_box, image=self._icon_img, text="").place(
                    relx=0.5, rely=0.5, anchor="center")
            except Exception:
                ctk.CTkLabel(icon_box, text="SP",
                             font=ctk.CTkFont(size=20, weight="bold"),
                             text_color=WHITE).place(relx=0.5, rely=0.5, anchor="center")
        else:
            ctk.CTkLabel(icon_box, text="SP",
                         font=ctk.CTkFont(size=20, weight="bold"),
                         text_color=WHITE).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(hdr, text="Soluciones Plus",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=WHITE, justify="center").pack(anchor="center", pady=(10,0))
        ctk.CTkLabel(hdr, text="Sistema de ventas",
                     font=ctk.CTkFont(size=11),
                     text_color="gray60", justify="center").pack(anchor="center")

        ctk.CTkFrame(self.sidebar, height=1, fg_color="gray30").pack(fill="x", padx=0, pady=4)

        # ── Logo inferior ─────────────────────────────────────────────────
        ctk.CTkFrame(self.sidebar, height=1, fg_color="gray30").pack(side="bottom", fill="x")
        logo_footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_footer.pack(side="bottom", pady=14)

        logo_path2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SP White.png")
        if os.path.exists(logo_path2):
            try:
                pil_f = Image.open(logo_path2)
                pil_f.thumbnail((155, 70), Image.LANCZOS)
                self._logo_footer = ctk.CTkImage(light_image=pil_f, dark_image=pil_f,
                                                 size=(pil_f.width, pil_f.height))
                ctk.CTkLabel(logo_footer, image=self._logo_footer, text="").pack()
            except Exception:
                ctk.CTkLabel(logo_footer, text="[logo inválido]",
                             text_color="gray50", font=ctk.CTkFont(size=10)).pack()
        else:
            ctk.CTkFrame(logo_footer, width=155, height=52,
                         corner_radius=8, fg_color="#122f5c").pack()
            ctk.CTkLabel(logo_footer, text="Pon logo.png junto al script",
                         text_color="gray50", font=ctk.CTkFont(size=10),
                         wraplength=150, justify="center").pack(pady=4)

        # Navegación
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=10, pady=8)

        self.nav_buttons = {}
        nav_items = [
            ("🏠  Inicio",         "inicio"),
            ("📦  Inventario",     "inventario"),
            ("➕  Nuevo producto", "nuevo_producto"),
            ("🛒  Vender",         "vender"),
            ("📋  Historial",      "historial"),
        ]
        for label, key in nav_items:
            btn = ctk.CTkButton(
                nav_frame, text=label, width=170, height=36,
                anchor="w", corner_radius=8,
                fg_color="transparent",
                text_color="gray80",
                hover_color="#1a3d6e",
                font=ctk.CTkFont(size=13),
                command=lambda k=key: self.show_frame(k))
            btn.pack(pady=2)
            self.nav_buttons[key] = btn

        ctk.CTkFrame(self.sidebar, height=1, fg_color="gray30").pack(fill="x", side="bottom")

        # ── Contenido ─────────────────────────────────────────────────────
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=GRAY_BG)
        self.content.pack(side="right", fill="both", expand=True)

        # Barra superior
        topbar = ctk.CTkFrame(self.content, height=52, corner_radius=0,
                               fg_color=WHITE)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        self.topbar_title = ctk.CTkLabel(topbar, text="Panel principal",
            font=ctk.CTkFont(size=17, weight="bold"), text_color=NAVY)
        self.topbar_title.pack(side="left", padx=20)
        ctk.CTkLabel(topbar,
            text=f"Soluciones Plus  —  {datetime.now().strftime('%d/%m/%Y')}",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(side="right", padx=20)

        self.inner = ctk.CTkFrame(self.content, fg_color=GRAY_BG, corner_radius=0)
        self.inner.pack(fill="both", expand=True, padx=20, pady=16)

        self.frames = {}
        self.frames["inicio"]         = InicioFrame(self.inner, self)
        self.frames["inventario"]     = InventarioFrame(self.inner, self)
        self.frames["nuevo_producto"] = NuevoProductoFrame(self.inner, self)
        self.frames["vender"]         = VenderFrame(self.inner, self)
        self.frames["historial"]      = HistorialFrame(self.inner, self)

        self.show_frame("inicio")

    def show_frame(self, key):
        titles = {
            "inicio": "Panel principal",
            "inventario": "Inventario",
            "nuevo_producto": "Registrar nuevo producto",
            "vender": "Nueva venta",
            "historial": "Historial de ventas",
        }
        for f in self.frames.values():
            f.pack_forget()
        self.frames[key].pack(fill="both", expand=True)
        if hasattr(self.frames[key], "refresh"):
            self.frames[key].refresh()
        self.topbar_title.configure(text=titles.get(key, ""))
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color=ORANGE, text_color=WHITE,
                              hover_color=ORANGE, font=ctk.CTkFont(size=13, weight="bold"))
            else:
                btn.configure(fg_color="transparent", text_color="gray80",
                              hover_color="#1a3d6e", font=ctk.CTkFont(size=13))


# ── Frame: Inicio ─────────────────────────────────────────────────────────────
class InicioFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()

        total_prod = query("SELECT COUNT(*) as c FROM productos", fetchall=False)["c"]
        sin_stock  = query("SELECT COUNT(*) as c FROM productos WHERE stock=0", fetchall=False)["c"]
        ventas_hoy = query(
            "SELECT COALESCE(SUM(total),0) as t FROM ventas WHERE fecha LIKE ?",
            (datetime.now().strftime("%Y-%m-%d") + "%",), fetchall=False)["t"]
        ventas_mes = query(
            "SELECT COALESCE(SUM(total),0) as t FROM ventas WHERE fecha LIKE ?",
            (datetime.now().strftime("%Y-%m") + "%",), fetchall=False)["t"]

        cards_data = [
            ("📦 Productos",   str(total_prod),        NAVY),
            ("⚠️ Sin stock",   str(sin_stock),          ORANGE),
            ("💰 Ventas hoy",  f"Q{ventas_hoy:.2f}",   "#16a34a"),
            ("📅 Ventas mes",  f"Q{ventas_mes:.2f}",   "#7c3aed"),
        ]
        cards_row = ctk.CTkFrame(self, fg_color="transparent")
        cards_row.pack(fill="x", pady=(0, 20))

        for title, val, color in cards_data:
            card = ctk.CTkFrame(cards_row, width=190, height=96,
                                corner_radius=12, fg_color=WHITE,
                                border_width=1, border_color=BORDER)
            card.pack(side="left", padx=(0,12))
            card.pack_propagate(False)
            # acento de color arriba
            accent = ctk.CTkFrame(card, height=4, corner_radius=0, fg_color=color)
            accent.pack(fill="x")
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12),
                         text_color=TEXT_MUTED).pack(pady=(8,2))
            ctk.CTkLabel(card, text=val,
                         font=ctk.CTkFont(size=22, weight="bold"),
                         text_color=color).pack()

        # Sección stock bajo
        sec = ctk.CTkFrame(self, fg_color="transparent")
        sec.pack(fill="x", pady=(0,10))
        ctk.CTkLabel(sec, text="⚠️  Productos con stock bajo (≤ 5)",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=NAVY).pack(side="left")

        tabla = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10,
                             border_width=1, border_color=BORDER)
        tabla.pack(fill="both", expand=True)

        cols = ("Producto","Variante","Categoría","Stock","Estado")
        tree = ttk.Treeview(tabla, columns=cols, show="headings", height=12)
        widths = [160, 140, 120, 70, 90]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")
        tree.tag_configure("sin_stock", foreground="#b91c1c")
        tree.tag_configure("bajo",      foreground="#b45309")

        sb = ctk.CTkScrollbar(tabla, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        sb.pack(side="right", fill="y")

        rows = query("""
            SELECT p.nombre, p.variante, p.stock, c.nombre as cat
            FROM productos p JOIN categorias c ON p.categoria_id=c.id
            WHERE p.stock <= 5 ORDER BY p.stock ASC LIMIT 20
        """)
        if not rows:
            tree.insert("", "end", values=("","","Todo el inventario tiene stock suficiente.","",""))
        else:
            for r in rows:
                estado = "❌ Agotado" if r["stock"]==0 else "⚠️ Bajo"
                tag    = "sin_stock"  if r["stock"]==0 else "bajo"
                tree.insert("", "end", values=(
                    r["nombre"], r["variante"] or "—", r["cat"],
                    r["stock"], estado), tags=(tag,))


# ── Frame: Inventario ─────────────────────────────────────────────────────────
class InventarioFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.search_var = ctk.StringVar()

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0,10))
        ctk.CTkEntry(top, placeholder_text="Buscar producto...",
                     textvariable=self.search_var, width=240).pack(side="right")
        self.search_var.trace_add("write", lambda *_: self.refresh())

        tabla = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10,
                             border_width=1, border_color=BORDER)
        tabla.pack(fill="both", expand=True)

        cols = ("ID","Categoría","Producto","Variante","Precio","Stock","Estado")
        self.tree = ttk.Treeview(tabla, columns=cols, show="headings", height=20)
        widths = [40,110,160,140,80,60,90]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        self.tree.tag_configure("sin_stock", foreground="#b91c1c")
        self.tree.tag_configure("bajo",      foreground="#b45309")

        sb = ctk.CTkScrollbar(tabla, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        sb.pack(side="right", fill="y")

        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", pady=8)
        ctk.CTkButton(btn_bar, text="✏️ Editar",
                      fg_color=NAVY, hover_color="#1a3d6e",
                      command=self.editar).pack(side="left", padx=(0,6))
        ctk.CTkButton(btn_bar, text="🗑️ Eliminar",
                      fg_color="#dc2626", hover_color="#b91c1c",
                      command=self.eliminar).pack(side="left", padx=(0,6))
        ctk.CTkButton(btn_bar, text="➕ Agregar stock",
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      command=self.agregar_stock).pack(side="left")

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        q = self.search_var.get().strip()
        rows = query("""
            SELECT p.id, c.nombre as cat, p.nombre, p.variante, p.precio, p.stock
            FROM productos p JOIN categorias c ON p.categoria_id=c.id
            WHERE p.nombre LIKE ? OR p.variante LIKE ? OR c.nombre LIKE ?
            ORDER BY c.nombre, p.nombre, p.variante
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
        for r in rows:
            estado = "✅ OK" if r["stock"]>5 else ("⚠️ Bajo" if r["stock"]>0 else "❌ Agotado")
            tag    = ""       if r["stock"]>5 else ("bajo"   if r["stock"]>0 else "sin_stock")
            self.tree.insert("", "end", iid=r["id"], values=(
                r["id"], r["cat"], r["nombre"], r["variante"] or "—",
                f"Q{r['precio']:.2f}", r["stock"], estado), tags=(tag,))

    def _sel(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso","Selecciona un producto primero.")
            return None
        return int(sel[0])

    def editar(self):
        pid = self._sel()
        if pid is None: return
        row = query("SELECT * FROM productos WHERE id=?", (pid,), fetchall=False)
        EditarProductoDialog(self, row, self.refresh)

    def eliminar(self):
        pid = self._sel()
        if pid is None: return
        if messagebox.askyesno("Confirmar","¿Eliminar este producto?"):
            execute("DELETE FROM productos WHERE id=?", (pid,))
            self.refresh()

    def agregar_stock(self):
        pid = self._sel()
        if pid is None: return
        row = query("SELECT * FROM productos WHERE id=?", (pid,), fetchall=False)
        AgregarStockDialog(self, row, self.refresh)


# ── Frame: Nuevo Producto ─────────────────────────────────────────────────────
class NuevoProductoFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        wrap = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=12,
                            border_width=1, border_color=BORDER)
        wrap.pack(anchor="nw", padx=0, pady=0, fill="x")

        ctk.CTkFrame(wrap, height=5, corner_radius=0, fg_color=ORANGE).pack(fill="x")

        form = ctk.CTkFrame(wrap, fg_color="transparent")
        form.pack(padx=24, pady=20, fill="x")

        def row(label, widget_class, **kwargs):
            ctk.CTkLabel(form, text=label, anchor="w",
                         text_color=NAVY, font=ctk.CTkFont(size=13, weight="bold")).pack(fill="x", pady=(10,0))
            w = widget_class(form, **kwargs)
            w.pack(fill="x", pady=(3,0))
            return w

        cats = [r["nombre"] for r in query("SELECT nombre FROM categorias ORDER BY nombre")]
        self.cat_var = ctk.StringVar(value=cats[0] if cats else "")
        ctk.CTkLabel(form, text="Categoría", anchor="w",
                     text_color=NAVY, font=ctk.CTkFont(size=13, weight="bold")).pack(fill="x", pady=(10,0))
        ctk.CTkOptionMenu(form, variable=self.cat_var, values=cats,
                          fg_color=WHITE, button_color=NAVY,
                          button_hover_color=ORANGE,
                          text_color=TEXT_MAIN).pack(fill="x", pady=(3,0))

        self.nombre   = row("Nombre del producto",          ctk.CTkEntry, placeholder_text="Ej: Lápiz")
        self.variante = row("Variante (marca/tipo/tamaño)", ctk.CTkEntry, placeholder_text="Ej: Mongol / Bic Rojo / 80 hojas")
        self.precio   = row("Precio unitario (Q)",          ctk.CTkEntry, placeholder_text="0.00")
        self.stock    = row("Stock inicial (unidades)",     ctk.CTkEntry, placeholder_text="0")

        ctk.CTkLabel(form, text="💡 Hojas sueltas: si 8 hojas = Q1.00  →  precio = Q0.125 por hoja",
                     text_color=TEXT_MUTED, font=ctk.CTkFont(size=11),
                     wraplength=480).pack(anchor="w", pady=(8,0))

        ctk.CTkButton(form, text="💾  Guardar producto", height=42,
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      text_color=WHITE, font=ctk.CTkFont(size=14, weight="bold"),
                      command=self.guardar).pack(fill="x", pady=(20,0))

    def guardar(self):
        nombre  = self.nombre.get().strip()
        variante= self.variante.get().strip()
        precio_s= self.precio.get().strip()
        stock_s = self.stock.get().strip()
        if not nombre:
            messagebox.showerror("Error","El nombre es obligatorio."); return
        try:
            precio = float(precio_s)
            stock  = int(stock_s) if stock_s else 0
        except ValueError:
            messagebox.showerror("Error","Precio y stock deben ser números."); return
        cat = query("SELECT id FROM categorias WHERE nombre=?",
                    (self.cat_var.get(),), fetchall=False)
        execute("INSERT INTO productos(categoria_id,nombre,variante,precio,stock) VALUES(?,?,?,?,?)",
                (cat["id"], nombre, variante, precio, stock))
        messagebox.showinfo("Éxito", f"Producto '{nombre} {variante}' guardado.")
        for e in (self.nombre, self.variante, self.precio, self.stock):
            e.delete(0,"end")


# ── Frame: Vender ─────────────────────────────────────────────────────────────
class VenderFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.carrito = []

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True)

        # ── Panel izquierdo ───────────────────────────────────────────────
        izq = ctk.CTkFrame(main, width=420, fg_color=WHITE,
                           corner_radius=10, border_width=1, border_color=BORDER)
        izq.pack(side="left", fill="both", padx=(0,12))
        izq.pack_propagate(False)

        ctk.CTkFrame(izq, height=4, corner_radius=0, fg_color=NAVY).pack(fill="x")
        inner_izq = ctk.CTkFrame(izq, fg_color="transparent")
        inner_izq.pack(fill="both", expand=True, padx=12, pady=10)

        ctk.CTkLabel(inner_izq, text="Buscar producto",
                     text_color=NAVY, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(4,2))
        self.buscar_var = ctk.StringVar()
        ctk.CTkEntry(inner_izq, textvariable=self.buscar_var,
                     placeholder_text="Nombre o variante...").pack(fill="x")
        self.buscar_var.trace_add("write", lambda *_: self.actualizar_lista())

        cols = ("Producto","Variante","Precio","Stock")
        self.lista = ttk.Treeview(inner_izq, columns=cols, show="headings", height=13)
        for col in cols:
            self.lista.heading(col, text=col)
            self.lista.column(col, width=88, anchor="center")
        self.lista.pack(fill="both", expand=True, pady=6)
        self.lista.bind("<Double-1>", lambda e: self.agregar_al_carrito())

        # Botones cantidad
        cant_frame = ctk.CTkFrame(inner_izq, fg_color="transparent")
        cant_frame.pack(fill="x", pady=(4,6))
        ctk.CTkLabel(cant_frame, text="Cantidad:",
                     text_color=NAVY, font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(0,10))
        self.cantidad = 1
        ctk.CTkButton(cant_frame, text="−", width=36, height=36,
                      fg_color=NAVY, hover_color=ORANGE,
                      font=ctk.CTkFont(size=20, weight="bold"),
                      corner_radius=8, command=self.decrementar).pack(side="left")
        self.cant_lbl = ctk.CTkLabel(cant_frame, text="1", width=40,
                                      font=ctk.CTkFont(size=16, weight="bold"),
                                      text_color=NAVY, anchor="center")
        self.cant_lbl.pack(side="left", padx=4)
        ctk.CTkButton(cant_frame, text="+", width=36, height=36,
                      fg_color=NAVY, hover_color=ORANGE,
                      font=ctk.CTkFont(size=20, weight="bold"),
                      corner_radius=8, command=self.incrementar).pack(side="left")

        ctk.CTkButton(inner_izq, text="➕  Agregar al carrito", height=38,
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self.agregar_al_carrito).pack(fill="x")

        # ── Panel derecho (carrito) ───────────────────────────────────────
        der = ctk.CTkFrame(main, fg_color=WHITE, corner_radius=10,
                           border_width=1, border_color=BORDER)
        der.pack(side="right", fill="both", expand=True)

        ctk.CTkFrame(der, height=4, corner_radius=0, fg_color=ORANGE).pack(fill="x")
        inner_der = ctk.CTkFrame(der, fg_color="transparent")
        inner_der.pack(fill="both", expand=True, padx=12, pady=10)

        ctk.CTkLabel(inner_der, text="🛒  Carrito de venta",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=NAVY).pack(anchor="w", pady=(0,6))

        cols2 = ("Producto","Cant","Precio","Subtotal")
        self.carrito_tree = ttk.Treeview(inner_der, columns=cols2, show="headings", height=13)
        for col in cols2:
            self.carrito_tree.heading(col, text=col)
            self.carrito_tree.column(col, width=110, anchor="center")
        self.carrito_tree.pack(fill="both", expand=True, pady=4)
        self.carrito_tree.bind("<Delete>", lambda e: self.quitar_del_carrito())

        self.total_lbl = ctk.CTkLabel(inner_der, text="Total: Q0.00",
                                       font=ctk.CTkFont(size=20, weight="bold"),
                                       text_color=ORANGE)
        self.total_lbl.pack(anchor="e", pady=6)

        btns = ctk.CTkFrame(inner_der, fg_color="transparent")
        btns.pack(fill="x")
        ctk.CTkButton(btns, text="🗑️ Quitar",
                      fg_color="transparent", border_width=1, border_color=BORDER,
                      text_color=NAVY, hover_color=GRAY_BG,
                      command=self.quitar_del_carrito).pack(side="left", padx=(0,6))
        ctk.CTkButton(btns, text="🧹 Limpiar",
                      fg_color="transparent", border_width=1, border_color=BORDER,
                      text_color=NAVY, hover_color=GRAY_BG,
                      command=self.limpiar).pack(side="left")
        ctk.CTkButton(btns, text="✅  Confirmar venta", height=40,
                      fg_color=NAVY, hover_color=ORANGE,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self.confirmar_venta).pack(side="right")

    def refresh(self):
        self.actualizar_lista()

    def actualizar_lista(self):
        self.lista.delete(*self.lista.get_children())
        q = self.buscar_var.get().strip()
        rows = query("""
            SELECT id, nombre, variante, precio, stock FROM productos
            WHERE (nombre LIKE ? OR variante LIKE ?) AND stock > 0
            ORDER BY nombre, variante
        """, (f"%{q}%", f"%{q}%"))
        for r in rows:
            self.lista.insert("", "end", iid=r["id"], values=(
                r["nombre"], r["variante"] or "—",
                f"Q{r['precio']:.2f}", r["stock"]))

    def incrementar(self):
        self.cantidad += 1
        self.cant_lbl.configure(text=str(self.cantidad))

    def decrementar(self):
        if self.cantidad > 1:
            self.cantidad -= 1
            self.cant_lbl.configure(text=str(self.cantidad))

    def agregar_al_carrito(self):
        sel = self.lista.selection()
        if not sel:
            messagebox.showwarning("Aviso","Selecciona un producto."); return
        pid  = int(sel[0])
        cant = self.cantidad
        prod = query("SELECT * FROM productos WHERE id=?", (pid,), fetchall=False)
        en_carrito = sum(i["cantidad"] for i in self.carrito if i["producto_id"]==pid)
        if en_carrito + cant > prod["stock"]:
            messagebox.showerror("Error",
                f"Stock insuficiente. Disponible: {prod['stock']-en_carrito}"); return
        for item in self.carrito:
            if item["producto_id"] == pid:
                item["cantidad"] += cant
                self.cantidad = 1
                self.cant_lbl.configure(text="1")
                self._render_carrito()
                return
        nombre_completo = f"{prod['nombre']} {prod['variante']}".strip()
        self.carrito.append({"producto_id":pid,"nombre":nombre_completo,
                              "precio":prod["precio"],"cantidad":cant})
        self.cantidad = 1
        self.cant_lbl.configure(text="1")
        self._render_carrito()

    def _render_carrito(self):
        self.carrito_tree.delete(*self.carrito_tree.get_children())
        total = 0.0
        for i, item in enumerate(self.carrito):
            sub = item["precio"] * item["cantidad"]
            total += sub
            self.carrito_tree.insert("", "end", iid=i, values=(
                item["nombre"], item["cantidad"],
                f"Q{item['precio']:.2f}", f"Q{sub:.2f}"))
        self.total_lbl.configure(text=f"Total: Q{total:.2f}")

    def quitar_del_carrito(self):
        sel = self.carrito_tree.selection()
        if not sel: return
        self.carrito.pop(int(sel[0]))
        self._render_carrito()

    def limpiar(self):
        self.carrito.clear()
        self._render_carrito()

    def confirmar_venta(self):
        if not self.carrito:
            messagebox.showwarning("Aviso","El carrito está vacío."); return
        total = sum(i["precio"]*i["cantidad"] for i in self.carrito)
        if not messagebox.askyesno("Confirmar",
            f"¿Confirmar venta por Q{total:.2f}?\nSe descontará el stock automáticamente."):
            return
        fecha    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        venta_id = execute("INSERT INTO ventas(fecha,total) VALUES(?,?)",(fecha,total))
        for item in self.carrito:
            execute("""INSERT INTO detalle_venta(venta_id,producto_id,cantidad,precio_unit,subtotal)
                       VALUES(?,?,?,?,?)""",
                    (venta_id,item["producto_id"],item["cantidad"],
                     item["precio"],item["precio"]*item["cantidad"]))
            execute("UPDATE productos SET stock=stock-? WHERE id=?",
                    (item["cantidad"],item["producto_id"]))
        messagebox.showinfo("Venta registrada",f"✅ Venta completada\nTotal: Q{total:.2f}")
        self.carrito.clear()
        self._render_carrito()
        self.actualizar_lista()


# ── Frame: Historial ──────────────────────────────────────────────────────────
class HistorialFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        top_wrap = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10,
                                border_width=1, border_color=BORDER)
        top_wrap.pack(fill="x", pady=(0,12))
        ctk.CTkFrame(top_wrap, height=4, corner_radius=0, fg_color=NAVY).pack(fill="x")

        cols = ("ID","Fecha","Total","Productos")
        self.tree = ttk.Treeview(top_wrap, columns=cols, show="headings", height=8)
        widths = [50,160,90,500]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        self.tree.pack(fill="x", padx=1, pady=1)
        self.tree.bind("<<TreeviewSelect>>", self.mostrar_detalle)

        det_wrap = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10,
                                border_width=1, border_color=BORDER)
        det_wrap.pack(fill="both", expand=True)
        ctk.CTkFrame(det_wrap, height=4, corner_radius=0, fg_color=ORANGE).pack(fill="x")
        ctk.CTkLabel(det_wrap, text="Detalle de la venta seleccionada",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=NAVY).pack(anchor="w", padx=12, pady=(8,4))

        cols2 = ("Producto","Cantidad","Precio unit.","Subtotal")
        self.det_tree = ttk.Treeview(det_wrap, columns=cols2, show="headings", height=8)
        for col in cols2:
            self.det_tree.heading(col, text=col)
            self.det_tree.column(col, width=170, anchor="center")
        self.det_tree.pack(fill="both", expand=True, padx=1, pady=(0,1))

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for v in query("SELECT * FROM ventas ORDER BY id DESC LIMIT 100"):
            prods = query("""SELECT p.nombre||' '||p.variante as n, d.cantidad
                             FROM detalle_venta d JOIN productos p ON d.producto_id=p.id
                             WHERE d.venta_id=?""", (v["id"],))
            resumen = ", ".join(f"{r['n'].strip()} x{r['cantidad']}" for r in prods)
            self.tree.insert("","end", iid=v["id"], values=(
                v["id"], v["fecha"], f"Q{v['total']:.2f}", resumen))

    def mostrar_detalle(self, event):
        sel = self.tree.selection()
        if not sel: return
        self.det_tree.delete(*self.det_tree.get_children())
        for r in query("""SELECT p.nombre||' '||p.variante as prod,
                                 d.cantidad, d.precio_unit, d.subtotal
                          FROM detalle_venta d JOIN productos p ON d.producto_id=p.id
                          WHERE d.venta_id=?""", (int(sel[0]),)):
            self.det_tree.insert("","end", values=(
                r["prod"].strip(), r["cantidad"],
                f"Q{r['precio_unit']:.2f}", f"Q{r['subtotal']:.2f}"))


# ── Diálogos auxiliares ───────────────────────────────────────────────────────
class EditarProductoDialog(ctk.CTkToplevel):
    def __init__(self, parent, row, callback):
        super().__init__(parent)
        self.title("Editar producto")
        self.geometry("400x340")
        self.grab_set()
        self.configure(fg_color=GRAY_BG)
        self.callback = callback

        ctk.CTkFrame(self, height=5, corner_radius=0, fg_color=ORANGE).pack(fill="x")

        frame = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=0)
        frame.pack(fill="both", expand=True, padx=0, pady=0)
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        cats = [r["nombre"] for r in query("SELECT nombre FROM categorias ORDER BY nombre")]
        cat_actual = query("""SELECT c.nombre FROM categorias c
                              JOIN productos p ON p.categoria_id=c.id
                              WHERE p.id=?""", (row["id"],), fetchall=False)["nombre"]
        self.cat_var = ctk.StringVar(value=cat_actual)
        ctk.CTkLabel(inner, text="Categoría", text_color=NAVY,
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        ctk.CTkOptionMenu(inner, variable=self.cat_var, values=cats,
                          fg_color=WHITE, button_color=NAVY,
                          button_hover_color=ORANGE,
                          text_color=TEXT_MAIN).pack(fill="x", pady=(2,8))

        for label, attr in [("Nombre","nombre"),("Variante","variante")]:
            ctk.CTkLabel(inner, text=label, text_color=NAVY,
                         font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            e = ctk.CTkEntry(inner)
            e.insert(0, row[attr] or "")
            e.pack(fill="x", pady=(2,8))
            setattr(self, f"e_{attr}", e)

        ctk.CTkLabel(inner, text="Precio (Q)", text_color=NAVY,
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.e_precio = ctk.CTkEntry(inner)
        self.e_precio.insert(0, str(row["precio"]))
        self.e_precio.pack(fill="x", pady=(2,12))

        ctk.CTkButton(inner, text="💾  Guardar cambios", height=40,
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      font=ctk.CTkFont(weight="bold"),
                      command=lambda: self._save(row["id"])).pack(fill="x")

    def _save(self, pid):
        cat = query("SELECT id FROM categorias WHERE nombre=?",
                    (self.cat_var.get(),), fetchall=False)
        try:
            precio = float(self.e_precio.get())
        except ValueError:
            messagebox.showerror("Error","Precio inválido"); return
        execute("UPDATE productos SET categoria_id=?,nombre=?,variante=?,precio=? WHERE id=?",
                (cat["id"], self.e_nombre.get().strip(),
                 self.e_variante.get().strip(), precio, pid))
        self.callback()
        self.destroy()


class AgregarStockDialog(ctk.CTkToplevel):
    def __init__(self, parent, row, callback):
        super().__init__(parent)
        self.title("Agregar stock")
        self.geometry("320x220")
        self.grab_set()
        self.configure(fg_color=GRAY_BG)
        self.callback = callback

        ctk.CTkFrame(self, height=5, corner_radius=0, fg_color=ORANGE).pack(fill="x")
        frame = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=0)
        frame.pack(fill="both", expand=True)
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        nombre = f"{row['nombre']} {row['variante']}".strip()
        ctk.CTkLabel(inner, text=nombre,
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=NAVY).pack(pady=(0,4))
        ctk.CTkLabel(inner, text=f"Stock actual: {row['stock']}",
                     text_color=TEXT_MUTED).pack(pady=(0,10))
        ctk.CTkLabel(inner, text="Cantidad a agregar:", text_color=NAVY,
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.entry = ctk.CTkEntry(inner)
        self.entry.pack(fill="x", pady=(2,12))
        ctk.CTkButton(inner, text="➕  Agregar al stock", height=40,
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      font=ctk.CTkFont(weight="bold"),
                      command=lambda: self._add(row["id"])).pack(fill="x")

    def _add(self, pid):
        try:
            n = int(self.entry.get())
            if n <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error","Ingresa un número entero positivo."); return
        execute("UPDATE productos SET stock=stock+? WHERE id=?", (n, pid))
        self.callback()
        self.destroy()


# ── Arranque ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app = LibreriaApp()
    app.mainloop()