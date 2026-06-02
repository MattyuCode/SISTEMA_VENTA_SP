import customtkinter as ctk
from tkinter import ttk, messagebox
from database import (get_productos, get_producto, eliminar_producto,
                      agregar_stock, get_mayoreos, get_categorias)
from config import *
from frames.dialogos import EditarProductoDialog, AgregarStockDialog
from frames.categorias import CategoriasModal

# Categorías gestionadas exclusivamente desde "Precios Doc y Mantenimientos"
CATS_SOLO_DOC = {"Tramite de Documentos", "Boletas"}


class InventarioFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.search_var = ctk.StringVar()
        self.cat_var    = ctk.StringVar(value="Todas")

        self._build_top()
        self._build_botones()
        self._build_tabla()

    # ── Barra superior: buscador + selector categoría ─────────────────────────
    def _build_top(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 8))

        # ── Selector de categoría (izquierda) ─────────────────────────────
        ctk.CTkLabel(top, text="📂  Categoría:",
                     text_color=NAVY,
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).pack(side="left", padx=(0, 6))

        self.cat_menu = ctk.CTkOptionMenu(
            top,
            variable=self.cat_var,
            values=["Todas"] + get_categorias(),
            width=200, height=34,
            fg_color=WHITE,
            button_color=NAVY,
            button_hover_color=ORANGE,
            text_color=TEXT_MAIN,
            dropdown_fg_color=WHITE,
            dropdown_hover_color=GRAY_BG,
            dropdown_text_color=TEXT_MAIN,
            command=lambda _: self.refresh())
        self.cat_menu.pack(side="left", padx=(0, 4))

        ctk.CTkButton(top, text="🗂️",
                      width=34, height=34,
                      fg_color=NAVY, hover_color="#1a3d6e",
                      text_color=WHITE,
                      font=ctk.CTkFont(size=15),
                      command=self._abrir_categorias).pack(side="left", padx=(0, 12))

        # ── Buscador (derecha) ────────────────────────────────────────────
        search_box = ctk.CTkFrame(top, fg_color="transparent")
        search_box.pack(side="right")

        self.search_entry = ctk.CTkEntry(
            search_box,
            placeholder_text="🔍  Buscar producto...",
            textvariable=self.search_var,
            width=260)
        self.search_entry.pack(side="left")

        ctk.CTkButton(search_box, text="✕", width=32, height=28,
                      fg_color="transparent", hover_color=GRAY_BG,
                      text_color=NAVY,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=lambda: self.search_var.set("")
                      ).pack(side="left", padx=(4, 0))

        self.search_var.trace_add("write", lambda *_: self.refresh())

    def _abrir_categorias(self):
        """Abre el modal de categorías y refresca el inventario al cerrar."""
        CategoriasModal(self, on_close=self.refresh)

    # ── Botones de acción ─────────────────────────────────────────────────────
    def _build_botones(self):
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

        self.resultado_lbl = ctk.CTkLabel(
            btns, text="",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=12))
        self.resultado_lbl.pack(side="right")

    # ── Tabla ─────────────────────────────────────────────────────────────────
    def _build_tabla(self):
        tabla = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10,
                             border_width=1, border_color=BORDER)
        tabla.pack(fill="both", expand=True)

        cols = ("ID", "Categoría", "Producto",
                "Precio Unitario", "Precio Mayoreo", "Stock", "Estado")
        self.tree = ttk.Treeview(tabla, columns=cols,
                                  show="headings", height=22)
        for col, w in zip(cols, [40, 160, 220, 110, 220, 70, 100]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)

        self.tree.tag_configure("sin_stock", foreground="#b91c1c")
        self.tree.tag_configure("bajo",      foreground="#b45309")
        self.tree.tag_configure("servicio",  foreground="#7c3aed")

        sb = ctk.CTkScrollbar(tabla, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        sb.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self.agregar_stock())

    # ── Refresh ───────────────────────────────────────────────────────────────
    def refresh(self):
        # Actualizar opciones del menú por si se agregó una nueva categoría
        nuevas = ["Todas"] + get_categorias()
        self.cat_menu.configure(values=nuevas)

        # Si la categoría activa ya no existe, resetear
        if self.cat_var.get() not in nuevas:
            self.cat_var.set("Todas")

        self.tree.delete(*self.tree.get_children())
        buscar     = self.search_var.get().strip()
        cat_filtro = None if self.cat_var.get() == "Todas" else self.cat_var.get()
        filas      = get_productos(buscar, cat_filtro)

        for r in filas:
            if r.get("tipo") == "Servicio":
                estado    = "🔧 Servicio"
                stock_txt = "∞"
                tag       = "servicio"
            elif r["stock"] > 5:
                estado    = "✅ OK"
                stock_txt = str(r["stock"])
                tag       = ""
            elif r["stock"] > 0:
                estado    = "⚠️ Bajo"
                stock_txt = str(r["stock"])
                tag       = "bajo"
            else:
                estado    = "❌ Agotado"
                stock_txt = "0"
                tag       = "sin_stock"

            mayoreos    = get_mayoreos(r["id"])
            mayoreo_txt = ("  |  ".join(
                f"{p['nombre']}: Q{p['precio']:.2f}" for p in mayoreos)
                if mayoreos else "—")

            self.tree.insert("", "end", iid=r["id"], values=(
                r["id"], r["cat"], r["nombre"],
                f"Q{r['precio']:.2f}",
                mayoreo_txt,
                stock_txt,
                estado
            ), tags=(tag,))

        total = len(filas)
        self.resultado_lbl.configure(
            text=f"{total} producto{'s' if total != 1 else ''} "
                 f"encontrado{'s' if total != 1 else ''}")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _sel(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un producto primero.")
            return None
        return int(sel[0])

    def _es_categoria_protegida(self, pid):
        """Retorna True si el producto pertenece a una categoría gestionada desde Precios Doc."""
        prod = get_producto(pid)
        if prod["cat"] in CATS_SOLO_DOC:
            messagebox.showinfo(
                "⚠️  Acción no permitida aquí",
                f"'{prod['nombre']}' pertenece a '{prod['cat']}'.\n\n"
                "Esta categoría se gestiona desde:\n"
                "📄  Precios Doc y Mantenimientos\n\n"
                "Edita o elimina el registro desde allí y\n"
                "los cambios se reflejarán en el inventario.",
            )
            return True
        return False

    def editar(self):
        pid = self._sel()
        if pid is None: return
        if self._es_categoria_protegida(pid): return
        EditarProductoDialog(self, get_producto(pid), self.refresh)

    def eliminar(self):
        pid = self._sel()
        if pid is None: return
        if self._es_categoria_protegida(pid): return
        prod = get_producto(pid)
        if messagebox.askyesno("Confirmar",
                f"¿Eliminar '{prod['nombre']}'?\n"
                f"Esta acción no se puede deshacer."):
            eliminar_producto(pid)
            self.refresh()

    def agregar_stock(self):
        pid = self._sel()
        if pid is None: return
        if self._es_categoria_protegida(pid): return
        prod = get_producto(pid)
        if prod.get("tipo") == "Servicio":
            messagebox.showinfo("Servicio",
                "Los servicios no tienen stock — siempre disponibles.")
            return
        AgregarStockDialog(self, prod, self.refresh)