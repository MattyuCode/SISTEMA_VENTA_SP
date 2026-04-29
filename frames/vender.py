import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
from database import get_productos_en_stock, registrar_venta
from config import *

class VenderFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.carrito  = []
        self.cantidad = 1

        # ── PanedWindow = separador arrastrable ───────────────────────────
        self.paned = ctk.CTkFrame(self, fg_color="transparent")
        self.paned.pack(fill="both", expand=True)

        import tkinter as tk
        self.pw = tk.PanedWindow(self.paned, orient=tk.HORIZONTAL,
                                 sashwidth=6, sashrelief="flat",
                                 bg="#cbd5e1", handlesize=0)
        self.pw.pack(fill="both", expand=True)

        # Panel izquierdo
        self.frm_izq = ctk.CTkFrame(self.pw, fg_color=WHITE,
                                     corner_radius=10)
        self.pw.add(self.frm_izq, minsize=280, width=430)

        # Panel derecho
        self.frm_der = ctk.CTkFrame(self.pw, fg_color=WHITE,
                                     corner_radius=10)
        self.pw.add(self.frm_der, minsize=280)

        self._build_panel_izq(self.frm_izq)
        self._build_panel_der(self.frm_der)

    # ── Panel izquierdo ───────────────────────────────────────────────────────
    def _build_panel_izq(self, parent):
        ctk.CTkFrame(parent, height=4, corner_radius=0,
                     fg_color=NAVY).pack(fill="x")

        inner = ctk.CTkFrame(parent, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=10)

        ctk.CTkLabel(inner, text="Buscar producto", text_color=NAVY,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(4, 2))
        self.buscar_var = ctk.StringVar()
        ctk.CTkEntry(inner, textvariable=self.buscar_var,
                     placeholder_text="Nombre o variante...").pack(fill="x")
        self.buscar_var.trace_add("write", lambda *_: self.actualizar_lista())

        # Lista con scrollbar en su propio contenedor
        lista_frame = ctk.CTkFrame(inner, fg_color="transparent")
        lista_frame.pack(fill="both", expand=True, pady=6)

        self.lista = ttk.Treeview(lista_frame,
            columns=("Producto","Variante","Precio","Stock","Tipo"),
            show="headings", height=13)
        for col, w in zip(("Producto","Variante","Precio","Stock","Tipo"),
                           [110, 110, 70, 55, 75]):
            self.lista.heading(col, text=col)
            self.lista.column(col, width=w, anchor="center")
        self.lista.tag_configure("servicio", foreground="#7c3aed")

        sb = ctk.CTkScrollbar(lista_frame, command=self.lista.yview)
        self.lista.configure(yscrollcommand=sb.set)
        self.lista.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.lista.bind("<Double-1>", lambda e: self.agregar_al_carrito())

        # Cantidad — fijo abajo, no se mueve
        cf = ctk.CTkFrame(inner, fg_color="transparent")
        cf.pack(fill="x", pady=(4, 6))
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

        ctk.CTkButton(inner, text="➕  Agregar al carrito", height=38,
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self.agregar_al_carrito).pack(fill="x", side="bottom", pady=(4,0))

    # ── Panel derecho ─────────────────────────────────────────────────────────
    def _build_panel_der(self, parent):
        ctk.CTkFrame(parent, height=4, corner_radius=0,
                     fg_color=ORANGE).pack(fill="x")

        inner = ctk.CTkFrame(parent, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=10)

        ctk.CTkLabel(inner, text="🛒  Carrito de venta",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=NAVY).pack(anchor="w", pady=(0, 6))

        self.carrito_tree = ttk.Treeview(inner,
            columns=("Producto","Cant","Precio","Subtotal"),
            show="headings", height=13)
        for col, w in zip(("Producto","Cant","Precio","Subtotal"),
                           [200, 60, 90, 100]):
            self.carrito_tree.heading(col, text=col)
            self.carrito_tree.column(col, width=w, anchor="center")
        self.carrito_tree.pack(fill="both", expand=True, pady=4)
        self.carrito_tree.bind("<Delete>", lambda e: self.quitar_del_carrito())

        self.total_lbl = ctk.CTkLabel(inner, text="Total: Q0.00",
                                       font=ctk.CTkFont(size=20, weight="bold"),
                                       text_color=ORANGE)
        self.total_lbl.pack(anchor="e", pady=6)

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
        for r in get_productos_en_stock(self.buscar_var.get().strip()):
            tag      = "servicio" if r["tipo"] == "Servicio" else ""
            stock_txt = "∞" if r["tipo"] == "Servicio" else str(r["stock"])
            self.lista.insert("", "end", iid=r["id"], values=(
                r["nombre"], r["variante"] or "—",
                f"Q{r['precio']:.2f}", stock_txt, r["tipo"]), tags=(tag,))

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
            messagebox.showwarning("Aviso", "Selecciona un producto."); return
        pid        = int(sel[0])
        vals       = self.lista.item(pid, "values")
        tipo       = vals[4]
        stock_disp = 999999 if tipo == "Servicio" else int(vals[3])
        precio     = float(vals[2].replace("Q", ""))
        nombre     = f"{vals[0]} {vals[1]}".replace("—", "").strip()

        en_c = sum(i["cantidad"] for i in self.carrito if i["producto_id"] == pid)
        if en_c + self.cantidad > stock_disp:
            messagebox.showerror("Error",
                f"Stock insuficiente. Disponible: {stock_disp - en_c}")
            return

        for item in self.carrito:
            if item["producto_id"] == pid:
                item["cantidad"] += self.cantidad
                self._reset_cantidad()
                self._render_carrito()
                return

        self.carrito.append({"producto_id": pid, "nombre": nombre,
                              "precio": precio, "cantidad": self.cantidad,
                              "tipo": tipo})
        self._reset_cantidad()
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
            messagebox.showwarning("Aviso", "El carrito está vacío."); return
        total = sum(i["precio"] * i["cantidad"] for i in self.carrito)
        if not messagebox.askyesno("Confirmar",
                f"¿Confirmar venta por Q{total:.2f}?\nSe descontará el stock automáticamente."):
            return
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        items = [{"producto_id": i["producto_id"],
                  "cantidad":    i["cantidad"],
                  "precio_unit": i["precio"],
                  "subtotal":    i["precio"] * i["cantidad"],
                  "tipo":        i.get("tipo", "Producto")}
                 for i in self.carrito]
        registrar_venta(fecha, total, items)
        messagebox.showinfo("Venta registrada", f"✅ Venta completada\nTotal: Q{total:.2f}")
        self.carrito.clear()
        self._render_carrito()
        self.actualizar_lista()