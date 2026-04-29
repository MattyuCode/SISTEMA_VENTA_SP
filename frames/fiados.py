import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
from database import (get_fiados, get_fiado_detalle, agregar_fiado,
                       marcar_pagado, eliminar_fiado, get_stats_fiados,
                       limpiar_pagados_antiguos)
from config import *

class FiadosFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.filtro = "pendiente"
        self.search_var = ctk.StringVar()
        self.items_temp = []   # items del formulario actual

        self._build_top_bar()
        self._build_form()
        self._build_filtros()
        self._build_tabla()

    # ── Tarjetas de resumen ───────────────────────────────────────────────────
    def _build_top_bar(self):
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(0, 12))

    def _render_stats(self):
        for w in self.stats_frame.winfo_children():
            w.destroy()
        cant, total = get_stats_fiados()
        for titulo, val, color in [
            ("👥  Clientes con deuda",  str(cant),          NAVY),
            ("💰  Total por cobrar",    f"Q{total:.2f}",    ORANGE),
        ]:
            card = ctk.CTkFrame(self.stats_frame, width=260, height=80,
                                corner_radius=10, fg_color=WHITE,
                                border_width=1, border_color=BORDER)
            card.pack(side="left", padx=(0, 12))
            card.pack_propagate(False)
            ctk.CTkFrame(card, height=4, corner_radius=0, fg_color=color).pack(fill="x")
            ctk.CTkLabel(card, text=titulo, font=ctk.CTkFont(size=12),
                         text_color=TEXT_MUTED).pack(pady=(8, 2))
            ctk.CTkLabel(card, text=val,
                         font=ctk.CTkFont(size=20, weight="bold"),
                         text_color=color).pack()

    # ── Formulario: Cliente + Items + Total ───────────────────────────────────
    def _build_form(self):
        form = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10,
                            border_width=1, border_color=BORDER)
        form.pack(fill="x", pady=(0, 12))
        ctk.CTkFrame(form, height=4, corner_radius=0, fg_color=ORANGE).pack(fill="x")

        inner = ctk.CTkFrame(form, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(inner, text="Registrar nueva deuda",
                     text_color=NAVY,
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).pack(anchor="w", pady=(0, 8))

        # Cliente (una sola vez)
        cli_frame = ctk.CTkFrame(inner, fg_color="transparent")
        cli_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(cli_frame, text="Cliente:", text_color=NAVY,
                     font=ctk.CTkFont(size=13, weight="bold"), width=70,
                     anchor="w").pack(side="left", padx=(0, 8))
        self.cliente_e = ctk.CTkEntry(cli_frame, width=300,
                                       placeholder_text="Ej: Juan Pérez")
        self.cliente_e.pack(side="left")

        # Fila para agregar productos — TODO EN UNA LÍNEA
        add_frame = ctk.CTkFrame(inner, fg_color=GRAY_BG, corner_radius=8)
        add_frame.pack(fill="x", pady=(0, 8))

        row = ctk.CTkFrame(add_frame, fg_color="transparent")
        row.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(row, text="Producto:", text_color=NAVY,
                     font=ctk.CTkFont(size=12, weight="bold")
                     ).pack(side="left", padx=(0, 6))
        self.prod_e = ctk.CTkEntry(row, placeholder_text="Ej: Lapicero Bic rojo")
        self.prod_e.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkLabel(row, text="Cant:", text_color=NAVY,
                     font=ctk.CTkFont(size=12, weight="bold")
                     ).pack(side="left", padx=(0, 4))
        self.cant_e = ctk.CTkEntry(row, width=55, placeholder_text="1")
        self.cant_e.insert(0, "1")
        self.cant_e.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(row, text="Precio Q:", text_color=NAVY,
                     font=ctk.CTkFont(size=12, weight="bold")
                     ).pack(side="left", padx=(0, 4))
        self.prec_e = ctk.CTkEntry(row, width=80, placeholder_text="0.00")
        self.prec_e.pack(side="left", padx=(0, 8))

        ctk.CTkButton(row, text="+ Agregar", height=32, width=100,
                      fg_color=NAVY, hover_color="#1a3d6e",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self.agregar_item).pack(side="left")

        # Lista de items agregados
        self.items_tree = ttk.Treeview(inner,
            columns=("Producto","Cant","Precio","Subtotal"),
            show="headings", height=4)
        for col, w in zip(("Producto","Cant","Precio","Subtotal"),
                           [320, 60, 90, 100]):
            self.items_tree.heading(col, text=col)
            self.items_tree.column(col, width=w, anchor="center")
        self.items_tree.pack(fill="x", pady=(0, 6))
        self.items_tree.bind("<Delete>", lambda e: self.quitar_item())

        # Total + botones finales
        final = ctk.CTkFrame(inner, fg_color="transparent")
        final.pack(fill="x")

        ctk.CTkButton(final, text="🗑️ Quitar item",
                      fg_color="transparent", border_width=1, border_color=BORDER,
                      text_color=NAVY, hover_color=GRAY_BG,
                      height=36, command=self.quitar_item).pack(side="left")

        self.total_lbl = ctk.CTkLabel(final, text="Total: Q0.00",
                                       font=ctk.CTkFont(size=16, weight="bold"),
                                       text_color=ORANGE)
        self.total_lbl.pack(side="left", padx=20)

        ctk.CTkButton(final, text="💾  Guardar deuda", height=36,
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self.guardar).pack(side="right")

    # ── Filtros ───────────────────────────────────────────────────────────────
    def _build_filtros(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 8))

        self.btn_pend = ctk.CTkButton(bar, text="📌  Pendientes",
            width=130, height=32, corner_radius=8,
            command=lambda: self._set_filtro("pendiente"))
        self.btn_pend.pack(side="left", padx=(0, 6))

        self.btn_pag = ctk.CTkButton(bar, text="✅  Historial pagados",
            width=160, height=32, corner_radius=8,
            command=lambda: self._set_filtro("pagado"))
        self.btn_pag.pack(side="left", padx=(0, 6))

        ctk.CTkEntry(bar, placeholder_text="🔍  Buscar cliente...",
                     textvariable=self.search_var, width=240).pack(side="right")
        self.search_var.trace_add("write", lambda *_: self.refresh())

        self._actualizar_botones_filtro()

    def _set_filtro(self, nuevo):
        self.filtro = nuevo
        self._actualizar_botones_filtro()
        self.refresh()

    def _actualizar_botones_filtro(self):
        for k, b in {"pendiente": self.btn_pend, "pagado": self.btn_pag}.items():
            if k == self.filtro:
                b.configure(fg_color=NAVY, text_color=WHITE, hover_color="#1a3d6e")
            else:
                b.configure(fg_color="transparent", text_color=NAVY,
                             hover_color=GRAY_BG, border_width=1, border_color=BORDER)

    # ── Tabla de deudas ───────────────────────────────────────────────────────
    def _build_tabla(self):
        # Botones PRIMERO (van al fondo con side="bottom")
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(side="bottom", fill="x", pady=(8, 0))
        ctk.CTkButton(btns, text="💵  Pagar",
                      fg_color="#16a34a", hover_color="#15803d",
                      height=36, width=140,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self.pagar).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btns, text="👁️  Ver detalle",
                      fg_color=NAVY, hover_color="#1a3d6e",
                      height=36, width=140,
                      command=self.ver_detalle).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btns, text="🗑️  Eliminar",
                      fg_color="#dc2626", hover_color="#b91c1c",
                      height=36, width=140,
                      command=self.eliminar).pack(side="left")
        ctk.CTkLabel(btns,
            text="🧹 Los pagados se eliminan después de 7 días",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=11)).pack(side="right")

        # Tabla después (ocupa el espacio restante)
        tabla = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10,
                             border_width=1, border_color=BORDER)
        tabla.pack(fill="both", expand=True)
        ctk.CTkFrame(tabla, height=4, corner_radius=0, fg_color=NAVY).pack(fill="x")

        cols = ("ID","Fecha","Cliente","Productos","Items","Total","Días","Estado")
        self.tree = ttk.Treeview(tabla, columns=cols, show="headings", height=10)
        for col, w in zip(cols, [40, 110, 140, 280, 50, 80, 60, 110]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        self.tree.tag_configure("vencido",  foreground="#b91c1c")
        self.tree.tag_configure("reciente", foreground="#166534")
        self.tree.tag_configure("pagado",   foreground="#6b7280")

        sb = ctk.CTkScrollbar(tabla, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        sb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda e: self.ver_detalle())

    # ── Lógica del formulario ─────────────────────────────────────────────────
    def agregar_item(self):
        prod = self.prod_e.get().strip()
        if not prod:
            messagebox.showwarning("Aviso", "Escribe el nombre del producto."); return
        try:
            cant   = int(self.cant_e.get() or "1")
            precio = float(self.prec_e.get())
            if cant <= 0 or precio <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error",
                "Cantidad debe ser entero positivo y precio mayor a 0."); return

        subtotal = cant * precio
        self.items_temp.append({"producto": prod, "cantidad": cant,
                                 "precio": precio, "subtotal": subtotal})
        self._render_items_temp()
        self.prod_e.delete(0, "end")
        self.cant_e.delete(0, "end"); self.cant_e.insert(0, "1")
        self.prec_e.delete(0, "end")
        self.prod_e.focus()

    def quitar_item(self):
        sel = self.items_tree.selection()
        if not sel: return
        idx = int(sel[0])
        self.items_temp.pop(idx)
        self._render_items_temp()

    def _render_items_temp(self):
        self.items_tree.delete(*self.items_tree.get_children())
        total = 0.0
        for i, it in enumerate(self.items_temp):
            total += it["subtotal"]
            self.items_tree.insert("", "end", iid=i, values=(
                it["producto"], it["cantidad"],
                f"Q{it['precio']:.2f}", f"Q{it['subtotal']:.2f}"))
        self.total_lbl.configure(text=f"Total: Q{total:.2f}")

    def guardar(self):
        cliente = self.cliente_e.get().strip()
        if not cliente:
            messagebox.showwarning("Aviso", "Escribe el nombre del cliente."); return
        if not self.items_temp:
            messagebox.showwarning("Aviso", "Agrega al menos un producto."); return

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        agregar_fiado(fecha, cliente, self.items_temp)

        self.cliente_e.delete(0, "end")
        self.items_temp.clear()
        self._render_items_temp()
        self.refresh()
        messagebox.showinfo("Guardado", "✅ Deuda registrada correctamente.")

    # ── Tabla / acciones ──────────────────────────────────────────────────────
    def refresh(self):
        limpiar_pagados_antiguos(dias=7)
        self._render_stats()
        self.tree.delete(*self.tree.get_children())
        filas = get_fiados(self.filtro, self.search_var.get().strip())
        ahora = datetime.now()
        for f in filas:
            fecha_reg = datetime.strptime(f["fecha"], "%Y-%m-%d %H:%M:%S")
            dias = (ahora - fecha_reg).days
            if f["estado"] == "pagado":
                if f["fecha_pago"]:
                    fpago = datetime.strptime(f["fecha_pago"], "%Y-%m-%d %H:%M:%S")
                    dias_pag = (ahora - fpago).days
                    estado_txt = f"✅ Pagado hace {dias_pag}d"
                else:
                    estado_txt = "✅ Pagado"
                tag = "pagado"
            else:
                estado_txt = "⏰ Pendiente"
                tag = "vencido" if dias >= 2 else "reciente"

            resumen_corto = f["resumen"]
            if len(resumen_corto) > 50:
                resumen_corto = resumen_corto[:47] + "..."

            self.tree.insert("", "end", iid=f["id"], values=(
                f["id"],
                fecha_reg.strftime("%d/%m %H:%M"),
                f["cliente"],
                resumen_corto,
                f["num_items"],
                f"Q{f['total']:.2f}",
                f"{dias}d",
                estado_txt
            ), tags=(tag,))

    def _sel(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un registro primero.")
            return None
        return int(sel[0])

    def ver_detalle(self):
        fid = self._sel()
        if fid is None: return
        DetalleDeudaDialog(self, fid)

    def pagar(self):
        fid = self._sel()
        if fid is None: return
        vals = self.tree.item(fid, "values")
        if "Pagado" in vals[7]:
            messagebox.showinfo("Aviso", "Esta deuda ya está pagada."); return
        if messagebox.askyesno("Confirmar pago",
                f"¿Confirmar pago de {vals[2]}?\n\n"
                f"Total: {vals[5]}\n"
                f"Items: {vals[4]}\n\n"
                f"Se moverá al historial por 7 días."):
            marcar_pagado(fid, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.refresh()

    def eliminar(self):
        fid = self._sel()
        if fid is None: return
        if messagebox.askyesno("Confirmar",
                "¿Eliminar esta deuda permanentemente?"):
            eliminar_fiado(fid)
            self.refresh()


# ── Diálogo para ver detalle de una deuda ─────────────────────────────────────
class DetalleDeudaDialog(ctk.CTkToplevel):
    def __init__(self, parent, fid):
        super().__init__(parent)
        self.title("Detalle de la deuda")
        self.geometry("520x480")
        self.grab_set()
        self.configure(fg_color=GRAY_BG)

        ctk.CTkFrame(self, height=5, corner_radius=0, fg_color=ORANGE).pack(fill="x")
        inner = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=0)
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        # Buscar info de la deuda
        deudas = get_fiados("todos")
        deuda = next((d for d in deudas if d["id"] == fid), None)
        if not deuda:
            ctk.CTkLabel(inner, text="Deuda no encontrada").pack()
            return

        # Cabecera
        ctk.CTkLabel(inner, text=f"📋 Deuda #{fid}",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=NAVY).pack(anchor="w")
        ctk.CTkLabel(inner, text=f"Cliente: {deuda['cliente']}",
                     font=ctk.CTkFont(size=13),
                     text_color=NAVY).pack(anchor="w", pady=(2, 2))
        ctk.CTkLabel(inner, text=f"Fecha: {deuda['fecha']}",
                     text_color=TEXT_MUTED,
                     font=ctk.CTkFont(size=11)).pack(anchor="w")
        estado = "✅ Pagado" if deuda["estado"] == "pagado" else "⏰ Pendiente"
        ctk.CTkLabel(inner, text=f"Estado: {estado}",
                     text_color=TEXT_MUTED,
                     font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(0, 12))

        # ── Botón cerrar y total PRIMERO (quedan fijos abajo) ─────────────
        ctk.CTkButton(inner, text="Cerrar", height=36,
                      fg_color=NAVY, hover_color="#1a3d6e",
                      command=self.destroy).pack(side="bottom", fill="x", pady=(10, 0))

        total_frame = ctk.CTkFrame(inner, fg_color=GRAY_BG, corner_radius=8,
                                    height=50)
        total_frame.pack(side="bottom", fill="x", pady=(8, 0))
        total_frame.pack_propagate(False)

        ctk.CTkLabel(total_frame, text="TOTAL:",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=NAVY).pack(side="left", padx=16)
        ctk.CTkLabel(total_frame, text=f"Q{deuda['total']:.2f}",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=ORANGE).pack(side="right", padx=16)

        # ── Tabla después (ocupa el espacio restante) ─────────────────────
        cols = ("Producto","Cantidad","Precio","Subtotal")
        tree = ttk.Treeview(inner, columns=cols, show="headings")
        for col, w in zip(cols, [220, 70, 80, 90]):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")
        tree.pack(fill="both", expand=True, pady=(0, 0))

        items = get_fiado_detalle(fid)
        for it in items:
            tree.insert("", "end", values=(
                it["producto"], it["cantidad"],
                f"Q{it['precio']:.2f}", f"Q{it['subtotal']:.2f}"))