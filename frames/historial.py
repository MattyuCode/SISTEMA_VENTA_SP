import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
from tkcalendar import DateEntry
from database import get_ventas, get_detalle_venta, get_observaciones_hoy
from config import *


class HistorialFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        # ── Barra superior con botón de reporte ───────────────────────────
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(top_bar, text="Ventas registradas",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=NAVY).pack(side="left")

        ctk.CTkButton(top_bar,
                      text="📲  Enviar reporte del día por WhatsApp",
                      height=36, fg_color=ORANGE, hover_color="#ea6c0a",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self.enviar_reporte).pack(side="right")

        ctk.CTkButton(top_bar,
                      text="📄  Solo generar PDF",
                      height=36, fg_color=NAVY, hover_color="#1a3d6e",
                      font=ctk.CTkFont(size=13),
                      command=lambda: self.generar(solo_pdf=True)).pack(
                      side="right", padx=(0, 8))

        # ── Selector de fecha en la misma fila ────────────────────────────
        ctk.CTkButton(top_bar, text="Ayer", width=60, height=28,
                      fg_color="transparent", border_width=1, border_color=BORDER,
                      text_color=NAVY, hover_color=GRAY_BG,
                      command=self._set_ayer).pack(side="right", padx=(0, 6))

        ctk.CTkButton(top_bar, text="Hoy", width=60, height=28,
                      fg_color="transparent", border_width=1, border_color=BORDER,
                      text_color=NAVY, hover_color=GRAY_BG,
                      command=self._set_hoy).pack(side="right", padx=(0, 6))

        self.cal = DateEntry(top_bar,
                             width=12,
                             background="#0d2b55",
                             foreground="white",
                             borderwidth=2,
                             date_pattern="yyyy-mm-dd",
                             maxdate=date.today(),
                             font=("Segoe UI", 11))
        self.cal.pack(side="right", padx=(0, 6))

        ctk.CTkLabel(top_bar, text="📅  Fecha del reporte:",
                     text_color=NAVY,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="right", padx=(0, 6))

        # ── Tabla ventas ──────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10,
                           border_width=1, border_color=BORDER)
        top.pack(fill="x", pady=(0, 12))
        ctk.CTkFrame(top, height=4, corner_radius=0, fg_color=NAVY).pack(fill="x")

        self.tree = ttk.Treeview(top,
            columns=("ID", "Fecha", "Total", "Descuento", "Productos"),
            show="headings", height=8)
        for col, w, anchor in zip(
                ("ID", "Fecha", "Total", "Descuento", "Productos"),
                [50, 160, 90, 90, 400],
                ["center", "center", "center", "center", "w"]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor=anchor)
        self.tree.pack(fill="x", padx=1, pady=1)
        self.tree.bind("<<TreeviewSelect>>", self.mostrar_detalle)

        # ── Detalle venta ─────────────────────────────────────────────────
        det = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10,
                           border_width=1, border_color=BORDER)
        det.pack(fill="both", expand=True)
        ctk.CTkFrame(det, height=4, corner_radius=0, fg_color=ORANGE).pack(fill="x")
        ctk.CTkLabel(det, text="Detalle de la venta seleccionada",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=NAVY).pack(anchor="w", padx=12, pady=(8, 4))

        self.det_tree = ttk.Treeview(det,
            columns=("Producto", "Cantidad", "Precio unit.", "Descuento", "Subtotal"),
            show="headings", height=8)
        for col, w, anchor in zip(
                ("Producto", "Cantidad", "Precio unit.", "Descuento", "Subtotal"),
                [200, 80, 110, 100, 110],
                ["w", "center", "center", "center", "center"]):
            self.det_tree.heading(col, text=col)
            self.det_tree.column(col, width=w, anchor=anchor)
        self.det_tree.tag_configure("con_descuento", foreground="#dc2626")
        self.det_tree.pack(fill="both", expand=True, padx=1, pady=(0, 1))

    # ── Helpers de fecha ──────────────────────────────────────────────────────
    def _set_hoy(self):
        self.cal.set_date(date.today())

    def _set_ayer(self):
        self.cal.set_date(date.today() - timedelta(days=1))

    def _get_fecha_seleccionada(self):
        fecha = self.cal.get_date()
        if fecha > date.today():
            messagebox.showwarning("Aviso", "No puedes seleccionar fechas futuras.")
            return None
        return fecha.strftime("%Y-%m-%d")

    # ── Refresh y detalle ─────────────────────────────────────────────────────
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for v in get_ventas():
            desc_txt = f"-Q{v['descuento']:.2f}" if v.get("descuento", 0) > 0 else "—"
            self.tree.insert("", "end", iid=v["id"], values=(
                v["id"], v["fecha"], f"Q{v['total']:.2f}",
                desc_txt, v["resumen"]))

    def mostrar_detalle(self, event):
        sel = self.tree.selection()
        if not sel: return
        self.det_tree.delete(*self.det_tree.get_children())
        for r in get_detalle_venta(int(sel[0])):
            desc      = r.get("descuento", 0.0) or 0.0
            desc_txt  = f"-Q{desc:.2f}" if desc > 0 else "—"
            sub_final = max(0.0, r["subtotal"] - desc)
            tag       = "con_descuento" if desc > 0 else ""
            self.det_tree.insert("", "end", values=(
                r["prod"], r["cantidad"],
                f"Q{r['precio_unit']:.2f}",
                desc_txt,
                f"Q{sub_final:.2f}"
            ), tags=(tag,))

    def generar(self, solo_pdf=False):
        from frames.reporte import generar_pdf
        from database import get_ventas_hoy, get_fiados_hoy

        fecha = self._get_fecha_seleccionada()
        if fecha is None: return

        ventas        = get_ventas_hoy(fecha)
        observaciones = get_observaciones_hoy(fecha)
        fiados        = get_fiados_hoy(fecha)

        if not ventas and not observaciones and not fiados:
            messagebox.showinfo("Sin datos",
                f"No hay ventas, observaciones ni fiados registrados el {fecha}.")
            return

        try:
            ruta = generar_pdf(ventas, observaciones, fiados, fecha)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}")
            return

        if solo_pdf:
            messagebox.showinfo("PDF generado", f"PDF guardado en:\n{ruta}")
            import subprocess
            subprocess.Popen(f'explorer /select,"{ruta}"')
            return

        return ruta

    def enviar_reporte(self):
        from frames.reporte import enviar_reporte_whatsapp
        ruta = self.generar(solo_pdf=False)
        if ruta is None: return

        ok, mensaje = enviar_reporte_whatsapp(ruta)
        if ok:
            messagebox.showinfo("Enviado",
                f"✅ {mensaje}\n\nEl PDF también quedó guardado en:\n{ruta}")
        else:
            messagebox.showerror("Error al enviar",
                f"{mensaje}\n\nEl PDF fue guardado en:\n{ruta}")