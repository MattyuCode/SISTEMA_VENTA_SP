import customtkinter as ctk
from config import *
from tkinter import messagebox, ttk
import webbrowser

from database import (get_precio_documentos, eliminar_precio_documento,
                      guardar_precio_documento,
                      get_precio_mantenimientos, eliminar_precio_mantenimiento,
                      guardar_precio_mantenimiento,
                      get_categorias, sincronizar_producto_desde_doc)


class PrecioDocumentosMantenimientosFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        # ── Botones de pestañas ───────────────────────────────────────────
        tabs_frame = ctk.CTkFrame(self, fg_color="transparent")
        tabs_frame.pack(fill="x", pady=(0, 12))

        center = ctk.CTkFrame(tabs_frame, fg_color="transparent")
        center.pack(anchor="center")

        self.btn_docs = ctk.CTkButton(center,
                      text="📄  Precio de documentos",
                      height=36, corner_radius=8,
                      command=lambda: self._set_tab("documentos"))
        self.btn_docs.pack(side="left", padx=(0, 6))

        self.btn_mant = ctk.CTkButton(center,
                      text="🔧  Precio de mantenimientos",
                      height=36, corner_radius=8,
                      command=lambda: self._set_tab("mantenimientos"))
        self.btn_mant.pack(side="left")

        # ── Panel documentos ──────────────────────────────────────────────
        self.panel_docs = PanelDocumentos(self, app)
        self.panel_mant = PanelMantenimientos(self, app)

        # Mostrar documentos por defecto
        self._set_tab("documentos")

    def _set_tab(self, tab):
        self.tab_actual = tab
        if tab == "documentos":
            self.btn_docs.configure(fg_color=ORANGE, hover_color="#ea6c0a",
                                     text_color=WHITE, font=ctk.CTkFont(size=13, weight="bold"))
            self.btn_mant.configure(fg_color="transparent", hover_color=GRAY_BG,
                                     text_color=NAVY, border_width=1, border_color=BORDER,
                                     font=ctk.CTkFont(size=13))
            self.panel_mant.pack_forget()
            self.panel_docs.pack(fill="both", expand=True)
            self.panel_docs.refresh()
        else:
            self.btn_mant.configure(fg_color=ORANGE, hover_color="#ea6c0a",
                                     text_color=WHITE, font=ctk.CTkFont(size=13, weight="bold"))
            self.btn_docs.configure(fg_color="transparent", hover_color=GRAY_BG,
                                     text_color=NAVY, border_width=1, border_color=BORDER,
                                     font=ctk.CTkFont(size=13))
            self.panel_docs.pack_forget()
            self.panel_mant.pack(fill="both", expand=True)
            self.panel_mant.refresh()

    def refresh(self):
        if hasattr(self, "tab_actual"):
            if self.tab_actual == "documentos":
                self.panel_docs.refresh()
            else:
                self.panel_mant.refresh()


# ── Panel de documentos ───────────────────────────────────────────────────────
class PanelDocumentos(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", pady=(0, 8))

        ctk.CTkButton(btns, text="➕  Nuevo",
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      width=120, height=34,
                      command=self.nuevo).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btns, text="✏️  Editar",
                      fg_color=NAVY, hover_color="#1a3d6e",
                      width=120, height=34,
                      command=self.editar).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btns, text="🗑️  Eliminar",
                      fg_color="#dc2626", hover_color="#b91c1c",
                      width=120, height=34,
                      command=self.eliminar).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btns, text="🌐  Abrir link",
                      fg_color="#0891b2", hover_color="#0e7490",
                      width=120, height=34,
                      command=self.abrir_link).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btns, text="📦  → Inventario",
                      fg_color="#16a34a", hover_color="#15803d",
                      width=140, height=34,
                      command=self.sincronizar).pack(side="left")

        tabla = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10,
                             border_width=1, border_color=BORDER)
        tabla.pack(fill="both", expand=True)
        ctk.CTkFrame(tabla, height=4, corner_radius=0, fg_color=NAVY).pack(fill="x")

        cols = ("ID", "Nombre", "Precio", "Precio descargar", "Precio validaciones", "Link validaciones")
        self.tree = ttk.Treeview(tabla, columns=cols, show="headings", height=20)
        for col, w, anchor in zip(cols,
                                   [40, 200, 100, 130, 150, 250],
                                   ["center", "w", "center", "center", "center", "w"]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor=anchor)
        self.tree.tag_configure("con_link", foreground="#0891b2")

        sb = ctk.CTkScrollbar(tabla, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        sb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self._abrir_link_doble_clic)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for r in get_precio_documentos():
            tiene_link  = bool(r["link_validaciones"])
            tag         = "con_link" if tiene_link else ""
            precio_desc = f"Q{r['precio_descargar']:.2f}" if r["precio_descargar"] is not None else "—"
            precio_val  = f"Q{r['precio_validaciones']:.2f}" if r["precio_validaciones"] is not None else "—"
            self.tree.insert("", "end", iid=r["id"], values=(
                r["id"], r["nombre"],
                f"Q{r['precio']:.2f}",
                precio_desc, precio_val,
                r["link_validaciones"] or "—"), tags=(tag,))

    def _sel(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un registro primero.")
            return None
        return int(sel[0])

    def _abrir_link_doble_clic(self, event):
        fid = self._sel()
        if fid is None: return
        link = self.tree.item(fid, "values")[5]
        if link and link != "—":
            webbrowser.open(link)
        else:
            messagebox.showinfo("Sin link", "Este documento no tiene link.")

    def abrir_link(self):
        fid = self._sel()
        if fid is None: return
        link = self.tree.item(fid, "values")[5]
        if link and link != "—":
            webbrowser.open(link)
        else:
            messagebox.showinfo("Sin link", "Este documento no tiene link.")

    def sincronizar(self):
        fid = self._sel()
        if fid is None:
            return
        vals   = self.tree.item(fid, "values")
        nombre = vals[1]
        precio = float(vals[2].replace("Q", ""))
        _SincronizarDialog(self, nombre, precio, self.refresh)

    def nuevo(self):
        DialogDocumento(self, None, self.refresh)

    def editar(self):
        fid = self._sel()
        if fid is None: return
        DialogDocumento(self, fid, self.refresh)

    def eliminar(self):
        fid = self._sel()
        if fid is None: return
        if messagebox.askyesno("Confirmar", "¿Eliminar este registro?"):
            eliminar_precio_documento(fid)
            self.refresh()


# ── Panel de mantenimientos ───────────────────────────────────────────────────
class PanelMantenimientos(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", pady=(0, 8))

        ctk.CTkButton(btns, text="➕  Nuevo",
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      width=120, height=34,
                      command=self.nuevo).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btns, text="✏️  Editar",
                      fg_color=NAVY, hover_color="#1a3d6e",
                      width=120, height=34,
                      command=self.editar).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btns, text="🗑️  Eliminar",
                      fg_color="#dc2626", hover_color="#b91c1c",
                      width=120, height=34,
                      command=self.eliminar).pack(side="left")

        tabla = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10,
                             border_width=1, border_color=BORDER)
        tabla.pack(fill="both", expand=True)
        ctk.CTkFrame(tabla, height=4, corner_radius=0, fg_color=NAVY).pack(fill="x")

        cols = ("ID", "Nombre", "Precio", "Observaciones")
        self.tree = ttk.Treeview(tabla, columns=cols, show="headings", height=20)
        for col, w, anchor in zip(cols,
                                   [40, 250, 100, 400],
                                   ["center", "w", "center", "w"]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor=anchor)

        sb = ctk.CTkScrollbar(tabla, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        sb.pack(side="right", fill="y")

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for r in get_precio_mantenimientos():
            self.tree.insert("", "end", iid=r["id"], values=(
                r["id"], r["nombre"],
                f"Q{r['precio']:.2f}",
                r["observaciones"] or "—"))

    def _sel(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un registro primero.")
            return None
        return int(sel[0])

    def nuevo(self):
        DialogMantenimiento(self, None, self.refresh)

    def editar(self):
        fid = self._sel()
        if fid is None: return
        DialogMantenimiento(self, fid, self.refresh)

    def eliminar(self):
        fid = self._sel()
        if fid is None: return
        if messagebox.askyesno("Confirmar", "¿Eliminar este registro?"):
            eliminar_precio_mantenimiento(fid)
            self.refresh()


# ── Diálogo documentos ────────────────────────────────────────────────────────
class DialogDocumento(ctk.CTkToplevel):
    def __init__(self, parent, fid, callback):
        super().__init__(parent)
        self.title("Nuevo documento" if fid is None else "Editar documento")
        self.geometry("440x580")
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color=GRAY_BG)
        self.lift()
        self.after(50, self.focus_force)
        self.callback = callback
        self.fid = fid

        ctk.CTkFrame(self, height=5, corner_radius=0, fg_color=ORANGE).pack(fill="x")
        inner = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=0)
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        def campo(label, placeholder=""):
            ctk.CTkLabel(inner, text=label, text_color=NAVY,
                         font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            e = ctk.CTkEntry(inner, placeholder_text=placeholder)
            e.pack(fill="x", pady=(2, 8))
            return e

        self.e_nombre    = campo("Nombre", "Ej: Solvencia Fiscal")
        self.e_precio    = campo("Precio cobrar (Q)", "0.00")
        self.e_descargar = campo("Precio descargar (Q)", "dejar vacío si no aplica")
        self.e_validacion= campo("Precio validaciones (Q)", "dejar vacío si no aplica")
        self.e_link      = campo("Link validaciones (opcional)", "https://...")

        if fid is not None:
            from database import get_precio_documento
            r = get_precio_documento(fid)
            self.e_nombre.insert(0, r["nombre"])
            self.e_precio.insert(0, str(r["precio"]))
            self.e_descargar.insert(0, str(r["precio_descargar"]) if r["precio_descargar"] else "")
            self.e_validacion.insert(0, str(r["precio_validaciones"]) if r["precio_validaciones"] else "")
            self.e_link.insert(0, r["link_validaciones"] or "")

        # ── Sección: también registrar en inventario ──────────────────────
        ctk.CTkFrame(inner, height=1, fg_color=BORDER).pack(fill="x", pady=(4, 10))

        self.sync_var = ctk.BooleanVar(value=False)
        sync_row = ctk.CTkFrame(inner, fg_color="transparent")
        sync_row.pack(fill="x", pady=(0, 4))
        ctk.CTkCheckBox(sync_row,
                        text="📦  Registrar también como producto vendible",
                        variable=self.sync_var,
                        text_color=NAVY,
                        fg_color=NAVY,
                        hover_color="#1a3d6e",
                        font=ctk.CTkFont(size=12, weight="bold"),
                        command=self._toggle_sync).pack(anchor="w")

        self.sync_frame = ctk.CTkFrame(inner, fg_color=GRAY_BG, corner_radius=8)

        ctk.CTkLabel(self.sync_frame, text="Categoría de inventario:",
                     text_color=NAVY,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(8, 2))

        cats = get_categorias()
        self.cat_var = ctk.StringVar(value=cats[0] if cats else "")
        ctk.CTkOptionMenu(self.sync_frame,
                          variable=self.cat_var,
                          values=cats if cats else ["Sin categorías"],
                          fg_color=WHITE, button_color=NAVY,
                          button_hover_color=ORANGE, text_color=TEXT_MAIN
                          ).pack(fill="x", padx=10, pady=(0, 4))

        ctk.CTkLabel(self.sync_frame,
                     text="💡 El nombre y precio se toman automáticamente de arriba.",
                     text_color=TEXT_MUTED,
                     font=ctk.CTkFont(size=10)).pack(anchor="w", padx=10, pady=(0, 8))

        # ── Guardar ───────────────────────────────────────────────────────
        ctk.CTkButton(inner, text="💾  Guardar", height=40,
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      font=ctk.CTkFont(weight="bold"),
                      command=self._guardar).pack(fill="x", pady=(8, 0))

    def _toggle_sync(self):
        if self.sync_var.get():
            self.sync_frame.pack(fill="x", pady=(0, 8),
                                 before=self.sync_frame.master.winfo_children()[-1])
        else:
            self.sync_frame.pack_forget()

    def _guardar(self):
        nombre = self.e_nombre.get().strip()
        if not nombre:
            messagebox.showerror("Error", "El nombre es obligatorio.", parent=self); return
        try:
            precio = float(self.e_precio.get())
        except ValueError:
            messagebox.showerror("Error", "El precio debe ser un número.", parent=self); return
        try:
            descargar = float(self.e_descargar.get()) if self.e_descargar.get().strip() else None
        except ValueError:
            messagebox.showerror("Error", "Precio descargar inválido.", parent=self); return
        try:
            validacion = float(self.e_validacion.get()) if self.e_validacion.get().strip() else None
        except ValueError:
            messagebox.showerror("Error", "Precio validaciones inválido.", parent=self); return

        link = self.e_link.get().strip() or None
        guardar_precio_documento(self.fid, nombre, precio, descargar, validacion, link)

        # Sincronizar con inventario si el checkbox está activo
        if self.sync_var.get():
            try:
                resultado = sincronizar_producto_desde_doc(nombre, precio, self.cat_var.get())
                accion = "creado" if resultado == "creado" else "actualizado"
                messagebox.showinfo(
                    "✅ Guardado",
                    f"Documento guardado.\n\n"
                    f"📦 Producto '{nombre}' {accion} en '{self.cat_var.get()}'.",
                    parent=self)
            except ValueError as e:
                messagebox.showwarning("Documento guardado, pero…", str(e), parent=self)
        else:
            messagebox.showinfo("✅ Guardado", f"'{nombre}' guardado correctamente.", parent=self)

        self.callback()
        self.destroy()


# ── Diálogo mantenimientos ────────────────────────────────────────────────────
class DialogMantenimiento(ctk.CTkToplevel):
    def __init__(self, parent, fid, callback):
        super().__init__(parent)
        self.title("Nuevo mantenimiento" if fid is None else "Editar mantenimiento")
        self.geometry("420x300")
        self.grab_set()
        self.configure(fg_color=GRAY_BG)
        self.callback = callback
        self.fid = fid

        ctk.CTkFrame(self, height=5, corner_radius=0, fg_color=ORANGE).pack(fill="x")
        inner = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=0)
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        def campo(label, placeholder=""):
            ctk.CTkLabel(inner, text=label, text_color=NAVY,
                         font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            e = ctk.CTkEntry(inner, placeholder_text=placeholder)
            e.pack(fill="x", pady=(2, 8))
            return e

        self.e_nombre      = campo("Nombre", "Ej: Formateo de computadora")
        self.e_precio      = campo("Precio (Q)", "0.00")
        self.e_observacion = campo("Observaciones (opcional)", "Ej: Incluye instalación de Windows")

        if fid is not None:
            from database import get_precio_mantenimiento
            r = get_precio_mantenimiento(fid)
            self.e_nombre.insert(0, r["nombre"])
            self.e_precio.insert(0, str(r["precio"]))
            self.e_observacion.insert(0, r["observaciones"] or "")

        ctk.CTkButton(inner, text="💾  Guardar", height=40,
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      font=ctk.CTkFont(weight="bold"),
                      command=self._guardar).pack(fill="x")

    def _guardar(self):
        nombre = self.e_nombre.get().strip()
        if not nombre:
            messagebox.showerror("Error", "El nombre es obligatorio."); return
        try:
            precio = float(self.e_precio.get())
        except ValueError:
            messagebox.showerror("Error", "El precio debe ser un número."); return

        obs = self.e_observacion.get().strip() or None
        guardar_precio_mantenimiento(self.fid, nombre, precio, obs)
        self.callback()
        self.destroy()


# ── Mini diálogo: sincronizar fila existente con inventario ───────────────────
class _SincronizarDialog(ctk.CTkToplevel):
    def __init__(self, parent, nombre, precio, callback):
        super().__init__(parent)
        self.nombre   = nombre
        self.precio   = precio
        self.callback = callback
        self.title("Enviar a Inventario")
        self.geometry("380x240")
        self.resizable(False, False)
        self.configure(fg_color=GRAY_BG)
        self.grab_set()
        self.lift()
        self.after(50, self.focus_force)

        ctk.CTkFrame(self, height=5, corner_radius=0, fg_color="#16a34a").pack(fill="x")

        inner = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=0)
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(inner, text="📦  Registrar en Inventario",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=NAVY).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(inner,
                     text=f"Servicio:  {nombre}\nPrecio:    Q{precio:.2f}",
                     font=ctk.CTkFont(size=12),
                     text_color=TEXT_MUTED,
                     justify="left").pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(inner, text="Categoría destino:",
                     text_color=NAVY,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")

        cats = get_categorias()
        self.cat_var = ctk.StringVar(value=cats[0] if cats else "")
        ctk.CTkOptionMenu(inner,
                          variable=self.cat_var,
                          values=cats if cats else ["Sin categorías"],
                          fg_color=WHITE, button_color=NAVY,
                          button_hover_color=ORANGE, text_color=TEXT_MAIN
                          ).pack(fill="x", pady=(4, 12))

        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(fill="x")
        ctk.CTkButton(btns, text="📦  Enviar",
                      fg_color="#16a34a", hover_color="#15803d",
                      width=120, height=34,
                      command=self._enviar).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text="Cancelar",
                      fg_color="transparent", hover_color=GRAY_BG2,
                      text_color=TEXT_MUTED, border_width=1, border_color=BORDER,
                      width=100, height=34,
                      command=self.destroy).pack(side="left")

    def _enviar(self):
        try:
            resultado = sincronizar_producto_desde_doc(
                self.nombre, self.precio, self.cat_var.get())
            accion = "creado" if resultado == "creado" else "actualizado su precio"
            messagebox.showinfo(
                "✅ Listo",
                f"Producto '{self.nombre}' {accion}\nen categoría '{self.cat_var.get()}'.",
                parent=self)
            self.callback()
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Error", str(e), parent=self)