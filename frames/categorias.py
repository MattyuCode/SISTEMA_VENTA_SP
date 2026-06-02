import customtkinter as ctk
from tkinter import ttk, messagebox
from database import (get_categorias_detalle, crear_categoria,
                      editar_categoria, eliminar_categoria)
from config import *


# ── Modal completo de Gestión de Categorías ───────────────────────────────────
class CategoriasModal(ctk.CTkToplevel):
    """
    Ventana modal para crear, editar y eliminar categorías.
    Uso:
        CategoriasModal(parent, on_close=callback)
    El callback se llama al cerrar para que el frame padre refresque sus dropdowns.
    """
    def __init__(self, parent, on_close=None):
        super().__init__(parent)
        self.on_close = on_close
        self.title("Gestión de Categorías")
        self.geometry("520x480")
        self.resizable(False, False)
        self.configure(fg_color=GRAY_BG)
        self.grab_set()
        self.lift()
        self.after(50, self.focus_force)
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

        self._build()
        self.refresh()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build(self):
        # Encabezado
        hdr = ctk.CTkFrame(self, fg_color=NAVY, corner_radius=0, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🗂️  Gestión de Categorías",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=WHITE).pack(side="left", padx=16, pady=12)

        # Botón Nueva
        ctk.CTkButton(hdr, text="➕  Nueva",
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      width=100, height=32,
                      command=self._nueva).pack(side="right", padx=12, pady=10)

        # Tabla
        card = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10,
                            border_width=1, border_color=BORDER)
        card.pack(fill="both", expand=True, padx=14, pady=(12, 6))

        cols = ("ID", "Nombre de categoría", "Productos")
        self.tree = ttk.Treeview(card, columns=cols, show="headings", height=12)
        anchos = {"ID": 50, "Nombre de categoría": 300, "Productos": 110}
        alinea = {"ID": "center", "Nombre de categoría": "w", "Productos": "center"}
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=anchos[col], anchor=alinea[col])

        self.tree.tag_configure("con_prods", foreground=NAVY)
        self.tree.tag_configure("sin_prods", foreground=TEXT_MUTED)

        sb = ctk.CTkScrollbar(card, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        sb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda _: self._editar())

        # Contador
        self.lbl_total = ctk.CTkLabel(self, text="",
                                      text_color=TEXT_MUTED,
                                      font=ctk.CTkFont(size=11))
        self.lbl_total.pack(anchor="e", padx=16)

        # Botones acción
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=14, pady=(4, 0))

        ctk.CTkButton(btns, text="✏️  Editar nombre",
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      width=150, height=34,
                      command=self._editar).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text="🗑️  Eliminar",
                      fg_color="#dc2626", hover_color="#b91c1c",
                      width=120, height=34,
                      command=self._eliminar).pack(side="left")
        ctk.CTkButton(btns, text="Cerrar",
                      fg_color="transparent", hover_color=GRAY_BG2,
                      text_color=TEXT_MUTED, border_width=1, border_color=BORDER,
                      width=90, height=34,
                      command=self._cerrar).pack(side="right")

        # Nota informativa
        nota = ctk.CTkFrame(self, fg_color=GRAY_BG2, corner_radius=8)
        nota.pack(fill="x", padx=14, pady=(8, 12))
        ctk.CTkLabel(nota,
                     text="ℹ️  No puedes eliminar una categoría con productos asignados."
                          "  Primero reasígnalos desde Inventario.",
                     font=ctk.CTkFont(size=11),
                     text_color=TEXT_MUTED,
                     wraplength=460).pack(padx=10, pady=6)

    # ── Refresh ───────────────────────────────────────────────────────────────
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        filas = get_categorias_detalle()
        for r in filas:
            tag = "con_prods" if r["count"] > 0 else "sin_prods"
            self.tree.insert("", "end", iid=r["id"], values=(
                r["id"], r["nombre"],
                f"{r['count']} prod." if r["count"] > 0 else "vacía"
            ), tags=(tag,))
        total = len(filas)
        self.lbl_total.configure(
            text=f"{total} categoría{'s' if total != 1 else ''} registrada{'s' if total != 1 else ''}")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _sel(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona una categoría primero.", parent=self)
            return None, None
        cid = int(sel[0])
        nombre = self.tree.item(sel[0], "values")[1]
        return cid, nombre

    def _cerrar(self):
        if self.on_close:
            self.on_close()
        self.destroy()

    # ── Acciones ──────────────────────────────────────────────────────────────
    def _nueva(self):
        _NombreDialog(self, "Nueva categoría", on_save=self._guardar_nueva)

    def _guardar_nueva(self, nombre):
        try:
            crear_categoria(nombre)
            self.refresh()
            messagebox.showinfo("✅ Listo", f"Categoría '{nombre}' creada.", parent=self)
        except ValueError as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _editar(self):
        cid, nombre_actual = self._sel()
        if cid is None:
            return
        _NombreDialog(self, "Editar categoría",
                      nombre_inicial=nombre_actual,
                      on_save=lambda n: self._guardar_edicion(cid, n))

    def _guardar_edicion(self, cid, nuevo_nombre):
        try:
            editar_categoria(cid, nuevo_nombre)
            self.refresh()
            messagebox.showinfo("✅ Listo", f"Categoría renombrada a '{nuevo_nombre}'.", parent=self)
        except ValueError as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _eliminar(self):
        cid, nombre = self._sel()
        if cid is None:
            return
        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar la categoría '{nombre}'?\n\n"
            "Solo es posible si no tiene productos asignados.",
            parent=self
        ):
            return
        try:
            eliminar_categoria(cid)
            self.refresh()
            messagebox.showinfo("✅ Listo", f"Categoría '{nombre}' eliminada.", parent=self)
        except ValueError as e:
            messagebox.showerror("No se puede eliminar", str(e), parent=self)


# ── Sub-diálogo: ingresar nombre ──────────────────────────────────────────────
class _NombreDialog(ctk.CTkToplevel):
    def __init__(self, parent, titulo, nombre_inicial="", on_save=None):
        super().__init__(parent)
        self.on_save = on_save
        self.title(titulo)
        self.geometry("360x170")
        self.resizable(False, False)
        self.configure(fg_color=GRAY_BG)
        self.grab_set()
        self.lift()
        self.after(50, self.focus_force)

        ctk.CTkLabel(self, text=titulo,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=NAVY).pack(pady=(18, 4))
        ctk.CTkLabel(self, text="Nombre:",
                     font=ctk.CTkFont(size=12),
                     text_color=TEXT_MUTED).pack()

        self.entry = ctk.CTkEntry(self, width=290, height=36,
                                  placeholder_text="Ej: Papelería, Útiles, Servicios…")
        self.entry.pack(pady=(5, 12))
        if nombre_inicial:
            self.entry.insert(0, nombre_inicial)
        self.entry.bind("<Return>", lambda _: self._guardar())

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack()
        ctk.CTkButton(btns, text="💾  Guardar",
                      fg_color=NAVY, hover_color="#1a3d6e",
                      width=120, height=34,
                      command=self._guardar).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Cancelar",
                      fg_color="transparent", hover_color=GRAY_BG2,
                      text_color=TEXT_MUTED, border_width=1, border_color=BORDER,
                      width=100, height=34,
                      command=self.destroy).pack(side="left")

    def _guardar(self):
        nombre = self.entry.get().strip()
        if not nombre:
            messagebox.showwarning("Aviso", "El nombre no puede estar vacío.", parent=self)
            return
        if self.on_save:
            self.on_save(nombre)
        self.destroy()
