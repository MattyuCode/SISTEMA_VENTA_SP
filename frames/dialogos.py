import customtkinter as ctk
from tkinter import messagebox
from database import get_categorias, editar_producto, agregar_stock
from config import *

class EditarProductoDialog(ctk.CTkToplevel):
    def __init__(self, parent, row, callback):
        super().__init__(parent)
        self.title("Editar producto")
        self.geometry("400x340")
        self.grab_set()
        self.configure(fg_color=GRAY_BG)
        self.callback = callback

        ctk.CTkFrame(self, height=5, corner_radius=0, fg_color=ORANGE).pack(fill="x")
        inner = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=0)
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        cats = get_categorias()
        self.cat_var = ctk.StringVar(value=row["cat"])
        ctk.CTkLabel(inner, text="Categoría", text_color=NAVY,
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        ctk.CTkOptionMenu(inner, variable=self.cat_var, values=cats,
                          fg_color=WHITE, button_color=NAVY,
                          button_hover_color=ORANGE,
                          text_color=TEXT_MAIN).pack(fill="x", pady=(2, 8))

        for label, key in [("Nombre","nombre"), ("Variante","variante")]:
            ctk.CTkLabel(inner, text=label, text_color=NAVY,
                         font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            e = ctk.CTkEntry(inner)
            e.insert(0, row[key] or "")
            e.pack(fill="x", pady=(2, 8))
            setattr(self, f"e_{key}", e)

        ctk.CTkLabel(inner, text="Precio (Q)", text_color=NAVY,
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.e_precio = ctk.CTkEntry(inner)
        self.e_precio.insert(0, str(row["precio"]))
        self.e_precio.pack(fill="x", pady=(2, 12))

        ctk.CTkButton(inner, text="💾  Guardar cambios", height=40,
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      font=ctk.CTkFont(weight="bold"),
                      command=lambda: self._save(row["id"])).pack(fill="x")

    def _save(self, pid):
        try:
            precio = float(self.e_precio.get())
        except ValueError:
            messagebox.showerror("Error", "Precio inválido"); return
        editar_producto(pid, self.cat_var.get(),
                        self.e_nombre.get().strip(),
                        self.e_variante.get().strip(),
                        precio)
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

        ctk.CTkLabel(inner, text=f"{row['nombre']} {row['variante']}".strip(),
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=NAVY).pack(pady=(0, 4))
        ctk.CTkLabel(inner, text=f"Stock actual: {row['stock']}",
                     text_color=TEXT_MUTED).pack(pady=(0, 10))
        ctk.CTkLabel(inner, text="Cantidad a agregar:", text_color=NAVY,
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.entry = ctk.CTkEntry(inner)
        self.entry.pack(fill="x", pady=(2, 12))
        ctk.CTkButton(inner, text="➕  Agregar al stock", height=40,
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