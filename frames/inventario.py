import customtkinter as ctk
from tkinter import ttk, messagebox
from database import get_productos, get_producto, editar_producto, eliminar_producto, agregar_stock
from config import *
from frames.dialogos import EditarProductoDialog, AgregarStockDialog

class InventarioFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.search_var = ctk.StringVar()

        # ── Barra superior ────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 8))
        ctk.CTkEntry(top, placeholder_text="🔍  Buscar producto...",
                     textvariable=self.search_var, width=260).pack(side="right")
        self.search_var.trace_add("write", lambda *_: self.refresh())

        # ── Botones de acción ─────────────────────────────────────────────
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", pady=(0, 8))

        ctk.CTkButton(btns, text="✏️  Editar",
                      fg_color=NAVY, hover_color="#1a3d6e",
                      width=120, height=34,
                      command=self.editar).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btns, text="🗑️  Eliminar",
                      fg_color="#dc2626", hover_color="#b91c1c",
                      width=120, height=34,
                      command=self.eliminar).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btns, text="➕  Agregar stock",
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      width=140, height=34,
                      command=self.agregar_stock).pack(side="left")

        # ── Tabla ─────────────────────────────────────────────────────────
        tabla = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10,
                             border_width=1, border_color=BORDER)
        tabla.pack(fill="both", expand=True)

        cols = ("ID","Categoría","Producto","Variante","Precio","Stock","Estado")
        self.tree = ttk.Treeview(tabla, columns=cols, show="headings", height=22)
        for col, w in zip(cols, [40, 110, 160, 140, 80, 60, 90]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        self.tree.tag_configure("sin_stock", foreground="#b91c1c")
        self.tree.tag_configure("bajo",      foreground="#b45309")

        sb = ctk.CTkScrollbar(tabla, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        sb.pack(side="right", fill="y")

        # doble clic abre agregar stock directo
        self.tree.bind("<Double-1>", lambda e: self.agregar_stock())

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        buscar = self.search_var.get().strip()
        for r in get_productos(buscar):
            estado = "✅ OK"      if r["stock"] > 5 else ("⚠️ Bajo"  if r["stock"] > 0 else "❌ Agotado")
            tag    = ""           if r["stock"] > 5 else ("bajo"     if r["stock"] > 0 else "sin_stock")
            self.tree.insert("", "end", iid=r["id"], values=(
                r["id"], r["cat"], r["nombre"], r["variante"] or "—",
                f"Q{r['precio']:.2f}", r["stock"], estado), tags=(tag,))

    def _sel(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un producto primero.")
            return None
        return int(sel[0])

    def editar(self):
        pid = self._sel()
        if pid is None: return
        EditarProductoDialog(self, get_producto(pid), self.refresh)

    def eliminar(self):
        pid = self._sel()
        if pid is None: return
        prod = get_producto(pid)
        nombre = f"{prod['nombre']} {prod['variante']}".strip()
        if messagebox.askyesno("Confirmar",
                f"¿Eliminar '{nombre}'?\nEsta acción no se puede deshacer."):
            eliminar_producto(pid)
            self.refresh()

    def agregar_stock(self):
        pid = self._sel()
        if pid is None: return
        AgregarStockDialog(self, get_producto(pid), self.refresh)