import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import get_productos_en_stock, registrar_venta, get_mayoreos
from config import *


class VenderFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.carrito  = []
        self.cantidad = 1
        self._pres_seleccionada = None

        self.paned = ctk.CTkFrame(self, fg_color="transparent")
        self.paned.pack(fill="both", expand=True)

        self.pw = tk.PanedWindow(self.paned, orient=tk.HORIZONTAL,
                                 sashwidth=6, sashrelief="flat",
                                 bg="#cbd5e1", handlesize=0)
        self.pw.pack(fill="both", expand=True)

        self.frm_izq = ctk.CTkFrame(self.pw, fg_color=WHITE, corner_radius=10)
        self.pw.add(self.frm_izq, minsize=280, width=500)

        self.frm_der = ctk.CTkFrame(self.pw, fg_color=WHITE, corner_radius=10)
        self.pw.add(self.frm_der, minsize=280)

        self._build_panel_izq(self.frm_izq)
        self._build_panel_der(self.frm_der)

    # ── Panel izquierdo ───────────────────────────────────────────────────────
    def _build_panel_izq(self, parent):
        ctk.CTkFrame(parent, height=4, corner_radius=0, fg_color=NAVY).pack(fill="x")

        inner = ctk.CTkFrame(parent, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        ctk.CTkLabel(inner, text="Buscar producto", text_color=NAVY,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(4, 2))
        self.buscar_var = ctk.StringVar()

        search_box = ctk.CTkFrame(inner, fg_color="transparent")
        search_box.pack(fill="x")

        self.buscar_entry = ctk.CTkEntry(search_box,
                                         textvariable=self.buscar_var,
                                         placeholder_text="Nombre...")
        self.buscar_entry.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(search_box, text="X", width=32, height=28,
                      fg_color=GRAY_BG2, hover_color=GRAY_BG,
                      text_color=NAVY,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=lambda: self.buscar_var.set("")
                      ).pack(side="left", padx=(4, 0))

        self.buscar_var.trace_add("write", lambda *_: self.actualizar_lista())

        # ── Lista con scrollbar ───────────────────────────────────────────
        lista_frame = ctk.CTkFrame(inner, fg_color="transparent")
        lista_frame.pack(fill="both", expand=True, pady=6)

        cols = ("Producto", "Precio", "Stock")
        self.lista = ttk.Treeview(lista_frame, columns=cols, show="headings", height=13)
        for col, w, anchor in zip(cols, [220, 90, 80], ["w", "center", "center"]):
            self.lista.heading(col, text=col)
            self.lista.column(col, width=w, anchor=anchor)
        self.lista.tag_configure("servicio", foreground="#7c3aed")

        sb = ctk.CTkScrollbar(lista_frame, command=self.lista.yview)
        self.lista.configure(yscrollcommand=sb.set)
        self.lista.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.lista.bind("<<TreeviewSelect>>", self._on_producto_sel)
        self.lista.bind("<Double-1>", lambda e: self.agregar_al_carrito())

        # ── Fila: Cantidad + Presentaciones ──────────────────────────────
        bottom_row = ctk.CTkFrame(inner, fg_color="transparent")
        bottom_row.pack(fill="x", pady=(4, 6))

        # Cantidad (izquierda)
        cf = ctk.CTkFrame(bottom_row, fg_color="transparent")
        cf.pack(side="left")
        ctk.CTkLabel(cf, text="Cantidad:", text_color=NAVY,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(0, 10))
        ctk.CTkButton(cf, text="−", width=36, height=36,
                      fg_color=NAVY, hover_color=ORANGE,
                      font=ctk.CTkFont(size=20, weight="bold"),
                      corner_radius=8, command=self.decrementar).pack(side="left")
        self.cant_var = ctk.StringVar(value="1")
        self.cant_var.trace_add("write", self._validar_cantidad)
        self.cant_entry = ctk.CTkEntry(cf, textvariable=self.cant_var,
                                       width=56, height=36, justify="center",
                                       font=ctk.CTkFont(size=15, weight="bold"))
        self.cant_entry.pack(side="left", padx=4)
        ctk.CTkButton(cf, text="+", width=36, height=36,
                      fg_color=NAVY, hover_color=ORANGE,
                      font=ctk.CTkFont(size=20, weight="bold"),
                      corner_radius=8, command=self.incrementar).pack(side="left")

        # Panel presentaciones (derecha)
        self.pres_panel = ctk.CTkFrame(bottom_row, fg_color=GRAY_BG, corner_radius=8)
        # No se hace pack aquí

        self.pres_nombre_lbl = ctk.CTkLabel(self.pres_panel, text="",
                                            font=ctk.CTkFont(size=10, weight="bold"),
                                            text_color=NAVY)
        self.pres_nombre_lbl.pack(anchor="w", padx=8, pady=(4, 2))

        self.pres_botones_frame = ctk.CTkFrame(self.pres_panel, fg_color="transparent")
        self.pres_botones_frame.pack(fill="x", padx=8, pady=(0, 6))

        # ── Botón agregar (siempre al final) ──────────────────────────────
        ctk.CTkButton(inner, text="➕  Agregar al carrito", height=38,
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self.agregar_al_carrito
                      ).pack(fill="x", pady=(0, 0))

    # ── Panel derecho ─────────────────────────────────────────────────────────
    def _build_panel_der(self, parent):
        ctk.CTkFrame(parent, height=4, corner_radius=0, fg_color=ORANGE).pack(fill="x")

        inner = ctk.CTkFrame(parent, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=10)

        ctk.CTkLabel(inner, text="🛒  Carrito de venta",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=NAVY).pack(anchor="w", pady=(0, 6))

        cols = ("Producto", "Cant", "Precio", "Descuento", "Subtotal")
        self.carrito_tree = ttk.Treeview(inner, columns=cols, show="headings", height=13)
        for col, w, anchor in zip(cols, [180, 50, 80, 80, 90], ["w", "center", "center", "center", "center"]):
            self.carrito_tree.heading(col, text=col)
            self.carrito_tree.column(col, width=w, anchor=anchor)
        self.carrito_tree.tag_configure("con_descuento", foreground="#dc2626")
        self.carrito_tree.pack(fill="both", expand=True, pady=4)
        self.carrito_tree.bind("<Delete>", lambda e: self.quitar_del_carrito())

        desc_frame = ctk.CTkFrame(inner, fg_color=GRAY_BG, corner_radius=8)
        desc_frame.pack(fill="x", pady=(0, 6))
        row_desc = ctk.CTkFrame(desc_frame, fg_color="transparent")
        row_desc.pack(padx=10, pady=6, fill="x")

        ctk.CTkLabel(row_desc, text="Descuento Q:", text_color=NAVY,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(0, 8))
        self.descuento_var = ctk.StringVar(value="0")
        ctk.CTkEntry(row_desc, textvariable=self.descuento_var,
                     width=100).pack(side="left")
        ctk.CTkButton(row_desc, text="✔ Aplicar", width=90, height=28,
                      fg_color=NAVY, hover_color="#1a3d6e",
                      text_color=WHITE,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self.aplicar_descuento_a_seleccionado).pack(side="left", padx=(8, 0))
        ctk.CTkButton(row_desc, text="✕ Quitar", width=80, height=28,
                      fg_color="transparent", border_width=1, border_color=BORDER,
                      text_color=NAVY, hover_color=GRAY_BG,
                      command=lambda: self.descuento_var.set("0")).pack(side="left", padx=(6, 0))

        totales_frame = ctk.CTkFrame(inner, fg_color="transparent")
        totales_frame.pack(fill="x", pady=(2, 6))

        self.subtotal_lbl = ctk.CTkLabel(totales_frame, text="Subtotal: Q0.00",
                                          font=ctk.CTkFont(size=12),
                                          text_color=TEXT_MUTED)
        self.subtotal_lbl.pack(anchor="e")

        self.desc_lbl = ctk.CTkLabel(totales_frame, text="",
                                      font=ctk.CTkFont(size=12),
                                      text_color="#dc2626")
        self.desc_lbl.pack(anchor="e")

        self.total_lbl = ctk.CTkLabel(totales_frame, text="Total: Q0.00",
                                       font=ctk.CTkFont(size=20, weight="bold"),
                                       text_color=ORANGE)
        self.total_lbl.pack(anchor="e")

        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(fill="x")
        for txt, cmd in [("🗑️ Quitar",  self.quitar_del_carrito),
                          ("🧹 Limpiar", self.limpiar)]:
            ctk.CTkButton(btns, text=txt, fg_color="transparent",
                          hover_color=GRAY_BG, border_width=1, border_color=BORDER,
                          text_color=NAVY, command=cmd).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btns, text="✅  Confirmar venta", height=40,
                      fg_color=NAVY, hover_color=ORANGE,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self.confirmar_venta).pack(side="right")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def refresh(self):
        self.actualizar_lista()

    def actualizar_lista(self):
        self.lista.delete(*self.lista.get_children())
        self._info = {}  # cache id -> row
        for r in get_productos_en_stock(self.buscar_var.get().strip()):
            self._info[r["id"]] = r
            tag       = "servicio" if r["tipo"] == "Servicio" else ""
            stock_txt = "∞" if r["tipo"] == "Servicio" else str(r["stock"])
            precio_txt = "Variable" if r.get("precio_variable") else f"Q{r['precio']:.2f}"
            self.lista.insert("", "end", iid=r["id"], values=(
                r["nombre"], precio_txt, stock_txt
            ), tags=(tag,))

    # ── Presentaciones ────────────────────────────────────────────────────────
    def _on_producto_sel(self, event=None):
        sel = self.lista.selection()
        if not sel:
            self.pres_panel.pack_forget()
            self._pres_seleccionada = None
            return

        pid = int(sel[0])
        vals = self.lista.item(pid, "values")

        for w in self.pres_botones_frame.winfo_children():
            w.destroy()
        self._pres_seleccionada = None

        # Producto de precio variable: no muestra presentaciones
        if self._info.get(pid, {}).get("precio_variable"):
            self.pres_panel.pack_forget()
            return

        presentaciones = get_mayoreos(pid)
        if not presentaciones:
            self.pres_panel.pack_forget()
            return

        self.pres_nombre_lbl.configure(text=f"Unidad y Mayor — {vals[0]}")
        self.pres_panel.pack(side="left", fill="x", expand=True, padx=(12, 0))  # ← solo una vez

        precio_base = float(vals[1].replace("Q", ""))
        primera = True
        if precio_base > 0:
            self._crear_boton_pres("Unidad", precio_base, seleccionado=True)
            self._pres_seleccionada = {"nombre": "Unidad", "precio": precio_base}
            primera = False

        for p in presentaciones:
            self._crear_boton_pres(p["nombre"], p["precio"], seleccionado=primera)
            if primera:
                self._pres_seleccionada = {"nombre": p["nombre"], "precio": p["precio"]}
                primera = False
        # ← eliminar el segundo pack que estaba aquí


    def _crear_boton_pres(self, nombre, precio, seleccionado=False):
        btn = ctk.CTkButton(
            self.pres_botones_frame,
            text=f"{nombre}\nQ{precio:.2f}",
            width=100, height=30,
            corner_radius=6,
            fg_color=ORANGE if seleccionado else "transparent",
            text_color=WHITE if seleccionado else NAVY,
            border_width=1,
            border_color=ORANGE if seleccionado else NAVY,
            hover_color="#ea6c0a",
            font=ctk.CTkFont(size=10),
            command=lambda n=nombre, p=precio: self._sel_pres(n, p)
        )
        btn.pack(side="left", padx=(0, 4))

    def _sel_pres(self, nombre, precio):
        self._pres_seleccionada = {"nombre": nombre, "precio": precio}
        for btn in self.pres_botones_frame.winfo_children():
            btn_nombre = btn.cget("text").split("\n")[0]
            if btn_nombre == nombre:
                btn.configure(fg_color=ORANGE, text_color=WHITE,
                              hover_color="#ea6c0a", border_color=ORANGE)
            else:
                btn.configure(fg_color="transparent", text_color=NAVY,
                              hover_color=GRAY_BG, border_color=NAVY)

    # ── Validación cantidad ───────────────────────────────────────────────────
    def _validar_cantidad(self, *_):
        val = self.cant_var.get()
        if val == "":
            self.cantidad = 1
            return
        try:
            n = int(val)
            self.cantidad = max(1, n)
            if n < 1:
                self.cant_var.set("1")
        except ValueError:
            limpio = "".join(c for c in val if c.isdigit())
            self.cant_var.set(limpio or "1")

    def incrementar(self):
        self.cantidad += 1
        self.cant_var.set(str(self.cantidad))

    def decrementar(self):
        if self.cantidad > 1:
            self.cantidad -= 1
            self.cant_var.set(str(self.cantidad))

    def _reset_cantidad(self):
        self.cantidad = 1
        self.cant_var.set("1")

    # ── Carrito ───────────────────────────────────────────────────────────────
    def agregar_al_carrito(self):
        sel = self.lista.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un producto.")
            return

        pid  = int(sel[0])
        vals = self.lista.item(pid, "values")
        tipo       = "Servicio" if vals[2] == "∞" else "Producto"
        stock_disp = 999999 if tipo == "Servicio" else int(vals[2])

        # ── Precio variable: preguntar el monto ───────────────────────────
        if self._info.get(pid, {}).get("precio_variable"):
            precio = self._pedir_precio(vals[0])
            if precio is None:
                return  # canceló
            nombre = vals[0]
        elif self._pres_seleccionada:
            pres_nombre = self._pres_seleccionada["nombre"]
            precio      = self._pres_seleccionada["precio"]
            nombre      = vals[0] if pres_nombre == "Unidad" else f"{vals[0]} [{pres_nombre}]"
        else:
            nombre = vals[0]
            precio = float(vals[1].replace("Q", ""))

        es_variable = bool(self._info.get(pid, {}).get("precio_variable"))

        en_c = sum(i["cantidad"] for i in self.carrito
                   if i["producto_id"] == pid and i["nombre"] == nombre)
        if en_c + self.cantidad > stock_disp:
            messagebox.showerror("Error",
                f"Stock insuficiente. Disponible: {stock_disp - en_c}")
            return

        # Los de precio variable NO se fusionan (cada uno con su propio precio)
        if not es_variable:
            for item in self.carrito:
                if item["producto_id"] == pid and item["nombre"] == nombre:
                    item["cantidad"] += self.cantidad
                    self._reset_cantidad()
                    self._render_carrito()
                    return

        self.carrito.append({"producto_id": pid, "nombre": nombre,
                              "precio": precio, "cantidad": self.cantidad,
                              "tipo": tipo, "descuento": 0.0})
        self._reset_cantidad()
        self._render_carrito()

    def _pedir_precio(self, nombre_prod):
        """Diálogo modal que pide el precio para un servicio de precio variable.
        Retorna el precio (float) o None si se cancela."""
        dlg = ctk.CTkToplevel(self)
        dlg.title("Precio del servicio")
        dlg.geometry("340x210")
        dlg.resizable(False, False)
        dlg.configure(fg_color=GRAY_BG)
        dlg.grab_set()
        dlg.lift()
        dlg.after(50, dlg.focus_force)

        ctk.CTkFrame(dlg, height=5, corner_radius=0, fg_color=ORANGE).pack(fill="x")
        inner = ctk.CTkFrame(dlg, fg_color=WHITE, corner_radius=0)
        inner.pack(fill="both", expand=True, padx=18, pady=14)

        ctk.CTkLabel(inner, text="💲 Precio variable",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=NAVY).pack(anchor="w")
        ctk.CTkLabel(inner, text=nombre_prod,
                     font=ctk.CTkFont(size=12),
                     text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 8))
        ctk.CTkLabel(inner, text="¿Cuánto vas a cobrar? (Q)",
                     text_color=NAVY,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")

        entry = ctk.CTkEntry(inner, placeholder_text="0.00", height=36)
        entry.pack(fill="x", pady=(4, 10))
        entry.focus_set()

        resultado = {"precio": None}

        def aceptar():
            try:
                p = float(entry.get())
                if p <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Ingresa un precio válido mayor a 0.",
                                     parent=dlg)
                return
            resultado["precio"] = p
            dlg.destroy()

        entry.bind("<Return>", lambda _: aceptar())

        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(fill="x")
        ctk.CTkButton(btns, text="✔ Aceptar",
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      width=120, height=34,
                      command=aceptar).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text="Cancelar",
                      fg_color="transparent", hover_color=GRAY_BG2,
                      text_color=TEXT_MUTED, border_width=1, border_color=BORDER,
                      width=100, height=34,
                      command=dlg.destroy).pack(side="left")

        dlg.wait_window()
        return resultado["precio"]

    def aplicar_descuento_a_seleccionado(self):
        sel = self.carrito_tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un producto del carrito."); return
        try:
            descuento = float(self.descuento_var.get())
            if descuento < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Descuento inválido."); return

        idx = int(sel[0])
        self.carrito[idx]["descuento"] = descuento
        self.descuento_var.set("0")
        self._render_carrito()

    def _render_carrito(self):
        self.carrito_tree.delete(*self.carrito_tree.get_children())
        subtotal   = 0.0
        total_desc = 0.0

        for i, item in enumerate(self.carrito):
            sub       = item["precio"] * item["cantidad"]
            desc      = item.get("descuento", 0.0)
            sub_final = max(0.0, sub - desc)
            subtotal  += sub_final
            total_desc += desc

            desc_txt = f"-Q{desc:.2f}" if desc > 0 else "—"
            tag      = "con_descuento" if desc > 0 else ""

            self.carrito_tree.insert("", "end", iid=i, values=(
                item["nombre"], item["cantidad"],
                f"Q{item['precio']:.2f}",
                desc_txt,
                f"Q{sub_final:.2f}"
            ), tags=(tag,))

        bruto = subtotal + total_desc
        self.subtotal_lbl.configure(text=f"Subtotal: Q{bruto:.2f}")
        if total_desc > 0:
            self.desc_lbl.configure(text=f"Descuentos: -Q{total_desc:.2f}")
        else:
            self.desc_lbl.configure(text="")
        self.total_lbl.configure(text=f"Total: Q{subtotal:.2f}")

    def quitar_del_carrito(self):
        sel = self.carrito_tree.selection()
        if not sel: return
        self.carrito.pop(int(sel[0]))
        self._render_carrito()

    def limpiar(self):
        self.carrito.clear()
        self.descuento_var.set("0")
        self._render_carrito()

    def confirmar_venta(self):
        if not self.carrito:
            messagebox.showwarning("Aviso", "El carrito está vacío."); return

        total_descuentos = sum(i.get("descuento", 0.0) for i in self.carrito)
        total = sum(
            max(0.0, i["precio"] * i["cantidad"] - i.get("descuento", 0.0))
            for i in self.carrito
        )

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        items = [{"producto_id": i["producto_id"],
                  "nombre_venta": i["nombre"],
                  "cantidad":    i["cantidad"],
                  "precio_unit": i["precio"],
                  "subtotal":    i["precio"] * i["cantidad"],
                  "descuento":   i.get("descuento", 0.0),
                  "tipo":        i.get("tipo", "Producto")}
                 for i in self.carrito]
        registrar_venta(fecha, total, items, descuento=total_descuentos)

        msg = f"✅ Venta completada\nTotal: Q{total:.2f}"
        if total_descuentos > 0:
            msg += f"\nDescuentos aplicados: -Q{total_descuentos:.2f}"
        messagebox.showinfo("Venta registrada", msg)

        self.carrito.clear()
        self.descuento_var.set("0")
        self._pres_seleccionada = None
        self._render_carrito()
        self.actualizar_lista()