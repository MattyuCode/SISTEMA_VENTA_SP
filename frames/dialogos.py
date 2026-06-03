import customtkinter as ctk
from tkinter import messagebox, ttk

from reportlab.lib.colors import white

from database import get_categorias, editar_producto, agregar_stock, get_mayoreos, guardar_mayoreos
from config import *

PRESENTACIONES_DEFAULT = ["Resma", "Fardo", "Caja", "Bolsa", "Paquete", "Docena"]


class EditarProductoDialog(ctk.CTkToplevel):
    def __init__(self, parent, row, callback):
        super().__init__(parent)
        self.title("Editar producto")
        self.geometry("460x600")
        self.grab_set()
        self.configure(fg_color=GRAY_BG)
        self.callback = callback
        self.presentaciones_temp = []

        ctk.CTkFrame(self, height=5, corner_radius=0, fg_color=ORANGE).pack(fill="x")
        inner = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10)
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        # Contenedor con padding interno
        body = ctk.CTkFrame(inner, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=10, )

        # Categoría
        cats = get_categorias()
        self.cat_var = ctk.StringVar(value=row["cat"])
        ctk.CTkLabel(body, text="Categoría", text_color=NAVY,
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        ctk.CTkOptionMenu(body, variable=self.cat_var, values=cats,
                          fg_color=WHITE, button_color=NAVY,
                          button_hover_color=ORANGE,
                          text_color=TEXT_MAIN).pack(fill="x", pady=(2, 8))

        # Tipo
        self.tipo_var = ctk.StringVar(value=row.get("tipo", "Producto"))
        ctk.CTkLabel(body, text="Tipo", text_color=NAVY,
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        tipo_frame = ctk.CTkFrame(body, fg_color="transparent")
        tipo_frame.pack(fill="x", pady=(2, 8))
        self.btn_producto = ctk.CTkButton(tipo_frame, text="📦  Producto",
                          width=140, height=32, corner_radius=8,
                          command=lambda: self._set_tipo("Producto"))
        self.btn_producto.pack(side="left", padx=(0, 8))
        self.btn_servicio = ctk.CTkButton(tipo_frame, text="🔧  Servicio",
                          width=140, height=32, corner_radius=8,
                          command=lambda: self._set_tipo("Servicio"))
        self.btn_servicio.pack(side="left")

        # Nombre
        ctk.CTkLabel(body, text="Nombre", text_color=NAVY,
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.e_nombre = ctk.CTkEntry(body)
        self.e_nombre.insert(0, row["nombre"] or "")
        self.e_nombre.pack(fill="x", pady=(2, 8))

        # Precio
        ctk.CTkLabel(body, text="Precio (Q)", text_color=NAVY,
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.e_precio = ctk.CTkEntry(body)
        self.e_precio.insert(0, str(row["precio"]))
        self.e_precio.pack(fill="x", pady=(2, 8))

        # Precio variable
        self.precio_var_chk = ctk.BooleanVar(value=bool(row.get("precio_variable", 0)))
        ctk.CTkCheckBox(body,
                        text="💲 Precio variable (se pregunta al vender)",
                        variable=self.precio_var_chk,
                        text_color=NAVY,
                        fg_color=NAVY, hover_color="#1a3d6e",
                        font=ctk.CTkFont(size=12, weight="bold"),
                        command=self._toggle_precio_var).pack(anchor="w", pady=(0, 8))

        # ── Precios de mayoreo (contenedor ocultable) ─────────────────────
        self.mayoreo_section = ctk.CTkFrame(body, fg_color="transparent")

        ctk.CTkLabel(self.mayoreo_section, text="💰  Precios de mayoreo",
                     text_color=NAVY,
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w")

        add_row = ctk.CTkFrame(self.mayoreo_section, fg_color=GRAY_BG, corner_radius=8)
        add_row.pack(fill="x", pady=(4, 6))
        row_inner = ctk.CTkFrame(add_row, fg_color="transparent")
        row_inner.pack(padx=8, pady=6, fill="x")

        ctk.CTkLabel(row_inner, text="Tipo:", text_color=NAVY,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 4))
        self.pres_var = ctk.StringVar(value="Resma")
        ctk.CTkOptionMenu(row_inner, variable=self.pres_var,
                          values=PRESENTACIONES_DEFAULT,
                          width=100, fg_color=WHITE,
                          button_color=NAVY, button_hover_color=ORANGE,
                          text_color=TEXT_MAIN).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(row_inner, text="Q:", text_color=NAVY,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 4))
        self.pres_precio = ctk.CTkEntry(row_inner, width=80, placeholder_text="0.00")
        self.pres_precio.pack(side="left", padx=(0, 8))

        ctk.CTkButton(row_inner, text="+ Agregar", height=28, width=90,
                      fg_color=NAVY, hover_color="#1a3d6e",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=self._agregar).pack(side="left")

        self.pres_tree = ttk.Treeview(self.mayoreo_section,
                                      columns=("Mayoreo", "Precio"),
                                      show="headings", height=3)
        for col, w in zip(("Mayoreo", "Precio"), [180, 100]):
            self.pres_tree.heading(col, text=col)
            self.pres_tree.column(col, width=w, anchor="center")
        self.pres_tree.pack(fill="x", pady=(0, 4))

        ctk.CTkButton(self.mayoreo_section, text="🗑️ Quitar seleccionada",
                      fg_color="transparent", border_width=1, border_color=BORDER,
                      text_color=NAVY, hover_color=GRAY_BG, height=28,
                      command=self._quitar).pack(anchor="w", pady=(0, 10))

        # Cargar presentaciones existentes
        for p in get_mayoreos(row["id"]):
            self.presentaciones_temp.append(p)
        self._render()

        # Guardar — siempre al fondo
        self.btn_guardar = ctk.CTkButton(body, text="💾  Guardar cambios", height=40,
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      font=ctk.CTkFont(weight="bold"),
                      command=lambda: self._save(row["id"]))
        self.btn_guardar.pack(fill="x")

        # Aplicar estado inicial correcto (oculta mayoreo si es Servicio)
        self._set_tipo(self.tipo_var.get())
        if self.precio_var_chk.get():
            self._toggle_precio_var()

    def _set_tipo(self, tipo):
        self.tipo_var.set(tipo)
        if tipo == "Producto":
            self.btn_producto.configure(fg_color=NAVY, text_color=WHITE,
                                        hover_color="#1a3d6e", border_width=0)
            self.btn_servicio.configure(fg_color="transparent", text_color=NAVY,
                                        hover_color=GRAY_BG,
                                        border_width=1, border_color=BORDER)
            # Mostrar sección de mayoreo antes del botón guardar
            self.mayoreo_section.pack(fill="x", pady=(0, 6),
                                      before=self.btn_guardar)
            self.geometry("460x600")
        else:
            self.btn_servicio.configure(fg_color=ORANGE, text_color=WHITE,
                                        hover_color="#ea6c0a", border_width=0)
            self.btn_producto.configure(fg_color="transparent", text_color=NAVY,
                                        hover_color=GRAY_BG,
                                        border_width=1, border_color=BORDER)
            # Ocultar sección de mayoreo
            self.mayoreo_section.pack_forget()
            self.geometry("460x380")

    def _toggle_precio_var(self):
        if self.precio_var_chk.get():
            self.e_precio.delete(0, "end")
            self.e_precio.insert(0, "0")
            self.e_precio.configure(state="disabled")
            self.mayoreo_section.pack_forget()
            self.geometry("460x420")
        else:
            self.e_precio.configure(state="normal")
            if self.tipo_var.get() == "Producto":
                self.mayoreo_section.pack(fill="x", pady=(0, 6),
                                          before=self.btn_guardar)
                self.geometry("460x640")

    def _agregar(self):
        nombre = self.pres_var.get()
        try:
            precio = float(self.pres_precio.get())
            if precio <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Precio inválido."); return
        if any(p["nombre"] == nombre for p in self.presentaciones_temp):
            messagebox.showwarning("Aviso", f"Ya existe '{nombre}'."); return
        self.presentaciones_temp.append({"nombre": nombre, "precio": precio})
        self._render()
        self.pres_precio.delete(0, "end")

    def _quitar(self):
        sel = self.pres_tree.selection()
        if not sel: return
        self.presentaciones_temp.pop(int(sel[0]))
        self._render()

    def _render(self):
        self.pres_tree.delete(*self.pres_tree.get_children())
        for i, p in enumerate(self.presentaciones_temp):
            self.pres_tree.insert("", "end", iid=i,
                                  values=(p["nombre"], f"Q{p['precio']:.2f}"))

    def _save(self, pid):
        nombre = self.e_nombre.get().strip()
        if not nombre:
            messagebox.showerror("Error", "El nombre es obligatorio."); return
        es_variable = 1 if self.precio_var_chk.get() else 0
        if es_variable:
            precio = 0.0
        else:
            try:
                precio = float(self.e_precio.get())
            except ValueError:
                messagebox.showerror("Error", "Precio inválido"); return

        editar_producto(pid, self.cat_var.get(), nombre,
                        self.tipo_var.get(), precio, es_variable)
        # Si es precio variable, no guardar mayoreos
        guardar_mayoreos(pid, [] if es_variable else self.presentaciones_temp)
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
        inner = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=0)
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        # Opcional: mismo padding interno para este diálogo
        body = ctk.CTkFrame(inner, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=10)

        ctk.CTkLabel(body, text=row["nombre"],
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=NAVY).pack(pady=(0, 4))
        ctk.CTkLabel(body, text=f"Stock actual: {row['stock']}",
                     text_color=TEXT_MUTED).pack(pady=(0, 10))
        ctk.CTkLabel(body, text="Cantidad a agregar:", text_color=NAVY,
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.entry = ctk.CTkEntry(body)
        self.entry.pack(fill="x", pady=(2, 12))
        ctk.CTkButton(body, text="➕  Agregar al stock", height=40,
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      font=ctk.CTkFont(weight="bold"),
                      command=lambda: self._add(row["id"])).pack(fill="x")

    def _add(self, pid):
        try:
            n = int(self.entry.get())
            if n <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Ingresa un número entero positivo."); return
        agregar_stock(pid, n)
        self.callback()
        self.destroy()