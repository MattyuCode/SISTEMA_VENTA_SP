import customtkinter as ctk
from tkinter import ttk
from database import get_ventas, get_detalle_venta
from config import *

class HistorialFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        top = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10,
                           border_width=1, border_color=BORDER)
        top.pack(fill="x", pady=(0, 12))
        ctk.CTkFrame(top, height=4, corner_radius=0, fg_color=NAVY).pack(fill="x")

        self.tree = ttk.Treeview(top,
            columns=("ID","Fecha","Total","Productos"),
            show="headings", height=8)
        for col, w in zip(("ID","Fecha","Total","Productos"), [50, 160, 90, 500]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        self.tree.pack(fill="x", padx=1, pady=1)
        self.tree.bind("<<TreeviewSelect>>", self.mostrar_detalle)

        det = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10,
                           border_width=1, border_color=BORDER)
        det.pack(fill="both", expand=True)
        ctk.CTkFrame(det, height=4, corner_radius=0, fg_color=ORANGE).pack(fill="x")
        ctk.CTkLabel(det, text="Detalle de la venta seleccionada",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=NAVY).pack(anchor="w", padx=12, pady=(8, 4))

        self.det_tree = ttk.Treeview(det,
            columns=("Producto","Cantidad","Precio unit.","Subtotal"),
            show="headings", height=8)
        for col in ("Producto","Cantidad","Precio unit.","Subtotal"):
            self.det_tree.heading(col, text=col)
            self.det_tree.column(col, width=170, anchor="center")
        self.det_tree.pack(fill="both", expand=True, padx=1, pady=(0, 1))

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for v in get_ventas():
            self.tree.insert("", "end", iid=v["id"], values=(
                v["id"], v["fecha"], f"Q{v['total']:.2f}", v["resumen"]))

    def mostrar_detalle(self, event):
        sel = self.tree.selection()
        if not sel: return
        self.det_tree.delete(*self.det_tree.get_children())
        for r in get_detalle_venta(int(sel[0])):
            self.det_tree.insert("", "end", values=(
                r["prod"], r["cantidad"],
                f"Q{r['precio_unit']:.2f}", f"Q{r['subtotal']:.2f}"))