import customtkinter as ctk
from tkinter import messagebox, ttk
from database import get_categorias, crear_producto, guardar_mayoreos
from frames.categorias import CategoriasModal
from config import *

PRESENTACIONES_DEFAULT = ["Resma", "Fardo", "Caja", "Bolsa", "Paquete", "Docena"]

class NuevoProductoFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.presentaciones_temp = []

        wrap = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=12,
                            border_width=1, border_color=BORDER)
        wrap.pack(anchor="nw", fill="both", expand=True)
        ctk.CTkFrame(wrap, height=5, corner_radius=0, fg_color=ORANGE).pack(fill="x")

        form = ctk.CTkFrame(wrap, fg_color="transparent")
        form.pack(padx=24, pady=0, fill="both", expand=True)

        def fila(label, **kwargs):
            ctk.CTkLabel(form, text=label, anchor="w", text_color=NAVY,
                         font=ctk.CTkFont(size=13, weight="bold")).pack(fill="x", pady=(10, 0))
            w = ctk.CTkEntry(form, **kwargs)
            w.pack(fill="x", pady=(3, 0))
            return w

        # ── Categoría + Tipo en una sola fila ────────────────────────────
        cat_tipo_row = ctk.CTkFrame(form, fg_color="transparent")
        cat_tipo_row.pack(fill="x", pady=(10, 0))

        # Columna Categoría
        cat_col = ctk.CTkFrame(cat_tipo_row, fg_color="transparent")
        cat_col.pack(side="left", fill="x", expand=True, padx=(0, 16))
        cats = get_categorias()
        self.cat_var = ctk.StringVar(value=cats[0] if cats else "")
        ctk.CTkLabel(cat_col, text="Categoría", anchor="w", text_color=NAVY,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")

        # Fila dropdown + botón gestionar
        cat_row = ctk.CTkFrame(cat_col, fg_color="transparent")
        cat_row.pack(fill="x", pady=(3, 0))

        self.cat_menu = ctk.CTkOptionMenu(
            cat_row, variable=self.cat_var, values=cats if cats else ["Sin categorías"],
            fg_color=GRAY_BG2, button_color=NAVY,
            button_hover_color=ORANGE, text_color=TEXT_MAIN)
        self.cat_menu.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(cat_row, text="🗂️",
                      width=36, height=34,
                      fg_color=NAVY, hover_color="#1a3d6e",
                      text_color=WHITE,
                      font=ctk.CTkFont(size=16),
                      command=self._abrir_categorias).pack(side="left")

        # Columna Tipo
        tipo_col = ctk.CTkFrame(cat_tipo_row, fg_color="transparent")
        tipo_col.pack(side="left")
        self.tipo_var = ctk.StringVar(value="Producto")
        ctk.CTkLabel(tipo_col, text="Tipo", anchor="w", text_color=NAVY,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        tipo_frame = ctk.CTkFrame(tipo_col, fg_color="transparent")
        tipo_frame.pack(pady=(3, 0))
        self.btn_producto = ctk.CTkButton(tipo_frame, text="📦  Producto",
                          width=140, height=34, corner_radius=8,
                          fg_color=NAVY, hover_color="#1a3d6e",
                          command=lambda: self._set_tipo("Producto"))
        self.btn_producto.pack(side="left", padx=(0, 8))
        self.btn_servicio = ctk.CTkButton(tipo_frame, text="🔧  Servicio",
                          width=140, height=34, corner_radius=8,
                          fg_color="transparent", hover_color=GRAY_BG,
                          border_width=1, border_color=BORDER, text_color=NAVY,
                          command=lambda: self._set_tipo("Servicio"))
        self.btn_servicio.pack(side="left")

        # ── Nombre ────────────────────────────────────────────────────────
        self.nombre = fila("Nombre", placeholder_text="Ej: Papel Bond / Solvencia Fiscal")

        # ── Precio + Stock en una sola fila ──────────────────────────────
        self.precio_stock_row = ctk.CTkFrame(form, fg_color="transparent")
        self.precio_stock_row.pack(fill="x", pady=(10, 0))

        precio_col = ctk.CTkFrame(self.precio_stock_row, fg_color="transparent")
        precio_col.pack(side="left", fill="x", expand=True, padx=(0, 16))
        ctk.CTkLabel(precio_col, text="Precio base unitario (Q)", anchor="w", text_color=NAVY,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        self.precio = ctk.CTkEntry(precio_col, placeholder_text="0.00")
        self.precio.pack(fill="x", pady=(3, 0))

        self.stock_col = ctk.CTkFrame(self.precio_stock_row, fg_color="transparent")
        self.stock_col.pack(side="left", fill="x", expand=True)
        self.stock_label = ctk.CTkLabel(self.stock_col, text="Stock inicial (unidades)",
                                         anchor="w", text_color=NAVY,
                                         font=ctk.CTkFont(size=13, weight="bold"))
        self.stock_label.pack(anchor="w")
        self.stock = ctk.CTkEntry(self.stock_col, placeholder_text="0")
        self.stock.pack(fill="x", pady=(3, 0))

        # ── Precios de mayoreo ────────────────────────────────────────────
        self.pres_section = ctk.CTkFrame(form, fg_color="transparent")
        self.pres_section.pack(fill="x", pady=(14, 0))

        ctk.CTkLabel(self.pres_section,
                     text="💰  Precios de mayoreo (opcional)",
                     text_color=NAVY,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(self.pres_section,
                     text="Agrega presentaciones con precio mayoreo (resma, caja, fardo, bolsa...)",
                     text_color=TEXT_MUTED,
                     font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(0, 6))

        add_pres = ctk.CTkFrame(self.pres_section, fg_color=GRAY_BG, corner_radius=8)
        add_pres.pack(fill="x", pady=(0, 6))
        row_pres = ctk.CTkFrame(add_pres, fg_color="transparent")
        row_pres.pack(padx=10, pady=8, fill="x")

        ctk.CTkLabel(row_pres, text="Tipo:", text_color=NAVY,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 4))
        self.pres_var = ctk.StringVar(value="Resma")
        self.pres_opt = ctk.CTkOptionMenu(row_pres, variable=self.pres_var,
                                           values=PRESENTACIONES_DEFAULT,
                                           width=110, fg_color=WHITE,
                                           button_color=NAVY, button_hover_color=ORANGE,
                                           text_color=TEXT_MAIN)
        self.pres_opt.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(row_pres, text="Precio Q:", text_color=NAVY,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 4))
        self.pres_precio = ctk.CTkEntry(row_pres, width=90, placeholder_text="0.00")
        self.pres_precio.pack(side="left", padx=(0, 8))

        ctk.CTkButton(row_pres, text="+ Agregar", height=32, width=100,
                      fg_color=NAVY, hover_color="#1a3d6e",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self._agregar_presentacion).pack(side="left")

        self.pres_tree = ttk.Treeview(self.pres_section,
                                       columns=("Mayoreo", "Precio"),
                                       show="headings", height=3)
        for col, w in zip(("Mayoreo", "Precio"), [200, 120]):
            self.pres_tree.heading(col, text=col)
            self.pres_tree.column(col, width=w, anchor="center")
        self.pres_tree.pack(fill="x", pady=(0, 4))

        ctk.CTkButton(self.pres_section, text="🗑️ Quitar seleccionada",
                      fg_color="transparent", border_width=1, border_color=BORDER,
                      text_color=NAVY, hover_color=GRAY_BG, height=30,
                      command=self._quitar_presentacion).pack(anchor="w")

        # ── Tip + Guardar ─────────────────────────────────────────────────
        self.tip_lbl = ctk.CTkLabel(form,
                     text="💡 Hojas sueltas: 8 hojas = Q1.00  →  precio base = Q0.125 por hoja",
                     text_color=TEXT_MUTED, font=ctk.CTkFont(size=11), wraplength=480)
        self.tip_lbl.pack(anchor="w", pady=(8, 0))

        ctk.CTkButton(form, text="💾  Guardar", height=42,
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      text_color=WHITE, font=ctk.CTkFont(size=14, weight="bold"),
                      command=self.guardar).pack(fill="x", pady=(16, 0))

    def _abrir_categorias(self):
        """Abre el modal de gestión de categorías y refresca el dropdown al cerrar."""
        CategoriasModal(self, on_close=self._actualizar_cats)

    def _actualizar_cats(self):
        """Recarga las categorías en el dropdown después de cerrar el modal."""
        cats = get_categorias()
        if not cats:
            cats = ["Sin categorías"]
        self.cat_menu.configure(values=cats)
        if self.cat_var.get() not in cats:
            self.cat_var.set(cats[0])

    def refresh(self):
        self._actualizar_cats()

    def _set_tipo(self, tipo):
        self.tipo_var.set(tipo)
        if tipo == "Producto":
            self.btn_producto.configure(fg_color=NAVY, text_color=WHITE, border_width=0)
            self.btn_servicio.configure(fg_color="transparent", text_color=NAVY, border_width=1)
            self.stock_col.pack(side="left", fill="x", expand=True)
            self.stock_label.pack(anchor="w")
            self.stock.pack(fill="x", pady=(3, 0))
            self.pres_section.pack(fill="x", pady=(14, 0))
            self.tip_lbl.pack(anchor="w", pady=(8, 0))
        else:
            self.btn_servicio.configure(fg_color=ORANGE, text_color=WHITE, border_width=0)
            self.btn_producto.configure(fg_color="transparent", text_color=NAVY, border_width=1)
            self.stock_col.pack_forget()
            self.pres_section.pack_forget()
            self.tip_lbl.pack_forget()

    def _agregar_presentacion(self):
        nombre = self.pres_var.get()
        try:
            precio = float(self.pres_precio.get())
            if precio <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Precio inválido."); return
        if any(p["nombre"] == nombre for p in self.presentaciones_temp):
            messagebox.showwarning("Aviso", f"Ya agregaste '{nombre}'."); return
        self.presentaciones_temp.append({"nombre": nombre, "precio": precio})
        self._render_presentaciones()
        self.pres_precio.delete(0, "end")

    def _quitar_presentacion(self):
        sel = self.pres_tree.selection()
        if not sel: return
        idx = int(sel[0])
        self.presentaciones_temp.pop(idx)
        self._render_presentaciones()

    def _render_presentaciones(self):
        self.pres_tree.delete(*self.pres_tree.get_children())
        for i, p in enumerate(self.presentaciones_temp):
            self.pres_tree.insert("", "end", iid=i,
                                   values=(p["nombre"], f"Q{p['precio']:.2f}"))

    def guardar(self):
        nombre = self.nombre.get().strip()
        tipo   = self.tipo_var.get()
        if not nombre:
            messagebox.showerror("Error", "El nombre es obligatorio."); return
        try:
            precio = float(self.precio.get())
            stock  = int(self.stock.get()) if (tipo == "Producto" and self.stock.get().strip()) else 0
        except ValueError:
            messagebox.showerror("Error", "Precio y stock deben ser números."); return

        pid = crear_producto(self.cat_var.get(), nombre, tipo, precio, stock)
        if self.presentaciones_temp:
            guardar_mayoreos(pid, self.presentaciones_temp)

        messagebox.showinfo("Éxito", f"{'Servicio' if tipo == 'Servicio' else 'Producto'} "
                                      f"'{nombre}' guardado.")
        for e in (self.nombre, self.precio, self.stock):
            e.delete(0, "end")
        self.presentaciones_temp.clear()
        self._render_presentaciones()