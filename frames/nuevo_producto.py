import customtkinter as ctk
from tkinter import messagebox
from database import get_categorias, crear_producto
from config import *

class NuevoProductoFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        wrap = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=12,
                            border_width=1, border_color=BORDER)
        wrap.pack(anchor="nw", fill="x")
        ctk.CTkFrame(wrap, height=5, corner_radius=0, fg_color=ORANGE).pack(fill="x")

        form = ctk.CTkFrame(wrap, fg_color="transparent")
        form.pack(padx=24, pady=20, fill="x")

        def fila(label, **kwargs):
            ctk.CTkLabel(form, text=label, anchor="w", text_color=NAVY,
                         font=ctk.CTkFont(size=13, weight="bold")).pack(fill="x", pady=(10, 0))
            w = ctk.CTkEntry(form, **kwargs)
            w.pack(fill="x", pady=(3, 0))
            return w

        # Categoría
        cats = get_categorias()
        self.cat_var = ctk.StringVar(value=cats[0] if cats else "")
        ctk.CTkLabel(form, text="Categoría", anchor="w", text_color=NAVY,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(fill="x", pady=(10, 0))
        ctk.CTkOptionMenu(form, variable=self.cat_var, values=cats,
                          fg_color=WHITE, button_color=NAVY,
                          button_hover_color=ORANGE,
                          text_color=TEXT_MAIN).pack(fill="x", pady=(3, 0))

        # Tipo: Producto / Servicio
        self.tipo_var = ctk.StringVar(value="Producto")
        ctk.CTkLabel(form, text="Tipo", anchor="w", text_color=NAVY,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(fill="x", pady=(10, 0))

        tipo_frame = ctk.CTkFrame(form, fg_color="transparent")
        tipo_frame.pack(fill="x", pady=(3, 0))

        self.btn_producto = ctk.CTkButton(tipo_frame, text="📦  Producto",
                          width=140, height=34, corner_radius=8,
                          fg_color=NAVY, hover_color="#1a3d6e",
                          command=lambda: self._set_tipo("Producto"))
        self.btn_producto.pack(side="left", padx=(0, 8))

        self.btn_servicio = ctk.CTkButton(tipo_frame, text="🔧  Servicio",
                          width=140, height=34, corner_radius=8,
                          fg_color="transparent", hover_color=GRAY_BG,
                          border_width=1, border_color=BORDER,
                          text_color=NAVY,
                          command=lambda: self._set_tipo("Servicio"))
        self.btn_servicio.pack(side="left")

        self.nombre   = fila("Nombre",                       placeholder_text="Ej: Lápiz / Solvencia Fiscal")
       #self.variante = fila("Variante (marca/tipo/tamaño)", placeholder_text="Ej: Mongol / DPI / Renap")
        self.precio   = fila("Precio unitario (Q)",          placeholder_text="0.00")

        # Stock solo para productos
        self.stock_label = ctk.CTkLabel(form, text="Stock inicial (unidades)", anchor="w",
                                         text_color=NAVY, font=ctk.CTkFont(size=13, weight="bold"))
        self.stock_label.pack(fill="x", pady=(10, 0))
        self.stock = ctk.CTkEntry(form, placeholder_text="0")
        self.stock.pack(fill="x", pady=(3, 0))

        self.tip_lbl = ctk.CTkLabel(form,
                     text="💡 Hojas sueltas: 8 hojas = Q1.00  →  precio = Q0.125 por hoja",
                     text_color=TEXT_MUTED, font=ctk.CTkFont(size=11), wraplength=480)
        self.tip_lbl.pack(anchor="w", pady=(8, 0))

        ctk.CTkButton(form, text="💾  Guardar", height=42,
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      text_color=WHITE, font=ctk.CTkFont(size=14, weight="bold"),
                      command=self.guardar).pack(fill="x", pady=(20, 0))

    def _set_tipo(self, tipo):
        self.tipo_var.set(tipo)
        if tipo == "Producto":
            self.btn_producto.configure(fg_color=NAVY, text_color=WHITE,
                                         border_width=0)
            self.btn_servicio.configure(fg_color="transparent", text_color=NAVY,
                                         border_width=1)
            self.stock_label.pack(fill="x", pady=(10, 0))
            self.stock.pack(fill="x", pady=(3, 0))
            self.tip_lbl.pack(anchor="w", pady=(8, 0))
        else:
            self.btn_servicio.configure(fg_color=ORANGE, text_color=WHITE,
                                         border_width=0)
            self.btn_producto.configure(fg_color="transparent", text_color=NAVY,
                                         border_width=1)
            # ocultar stock para servicios
            self.stock_label.pack_forget()
            self.stock.pack_forget()
            self.tip_lbl.pack_forget()

    def guardar(self):
        nombre   = self.nombre.get().strip()
        variante = self.variante.get().strip()
        tipo     = self.tipo_var.get()
        if not nombre:
            messagebox.showerror("Error", "El nombre es obligatorio."); return
        try:
            precio = float(self.precio.get())
            stock  = int(self.stock.get()) if (tipo == "Producto" and self.stock.get().strip()) else 0
        except ValueError:
            messagebox.showerror("Error", "Precio y stock deben ser números."); return

        crear_producto(self.cat_var.get(), nombre, variante, tipo, precio, stock)
        messagebox.showinfo("Éxito", f"{'Servicio' if tipo=='Servicio' else 'Producto'} "
                                      f"'{nombre} {variante}' guardado.")
        for e in (self.nombre, self.variante, self.precio, self.stock):
            e.delete(0, "end")