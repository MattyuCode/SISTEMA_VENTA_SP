import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
from database import get_ventas, get_ventas_hoy, get_ventas_anuladas_hoy, get_detalle_venta, get_observaciones_hoy, anular_venta
from config import *
from frames.ctk_calendar import CTkCalendar


class HistorialFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._fecha_sel = date.today()
        self._cal_popup = None

        # ── Barra superior con botón de reporte ───────────────────────────
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(top_bar, text="Ventas registradas",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=NAVY).pack(side="left")

        # ── Buscador por nombre de producto ───────────────────────────────
        self.buscar_var = ctk.StringVar()
        buscar_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        buscar_box.pack(side="left", padx=(12, 0))
        self.buscar_entry = ctk.CTkEntry(
            buscar_box, textvariable=self.buscar_var,
            placeholder_text="🔍  Buscar producto vendido...",
            width=260, height=30)
        self.buscar_entry.pack(side="left")
        ctk.CTkButton(buscar_box, text="✕", width=30, height=30,
                      fg_color="transparent", hover_color=GRAY_BG,
                      text_color=NAVY,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=lambda: self.buscar_var.set("")).pack(side="left", padx=(4, 0))
        self.buscar_var.trace_add("write", lambda *_: self.refresh())

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

        # ── Botones Hoy / Ayer ────────────────────────────────────────────
        ctk.CTkButton(top_bar, text="Ayer", width=55, height=28,
                      fg_color="transparent", border_width=1, border_color=BORDER,
                      text_color=NAVY, hover_color=GRAY_BG,
                      command=self._set_ayer).pack(side="right", padx=(0, 4))

        ctk.CTkButton(top_bar, text="Hoy", width=55, height=28,
                      fg_color="transparent", border_width=1, border_color=BORDER,
                      text_color=NAVY, hover_color=GRAY_BG,
                      command=self._set_hoy).pack(side="right", padx=(0, 6))

        # ── Botón calendario ──────────────────────────────────────────────
        self.fecha_btn = ctk.CTkButton(top_bar,
                         text=f"📅  {date.today().strftime('%d/%m/%Y')}",
                         width=140, height=28,
                         fg_color="transparent", border_width=1, border_color=BORDER,
                         text_color=NAVY, hover_color=GRAY_BG,
                         font=ctk.CTkFont(size=12),
                         command=self._toggle_cal)
        self.fecha_btn.pack(side="right", padx=(0, 6))

        ctk.CTkLabel(top_bar, text="Fecha:",
                     text_color=NAVY,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="right", padx=(0, 6))

        # ── Panel divisible (arrastrable vertical) ────────────────────────
        self.pw = tk.PanedWindow(self, orient=tk.VERTICAL,
                                 sashwidth=8, sashrelief="raised",
                                 bg="#cbd5e1", handlesize=0)
        # (se hace pack al final, después de los botones fijos)

        # ── Tabla ventas ──────────────────────────────────────────────────
        top = ctk.CTkFrame(self.pw, fg_color=WHITE, corner_radius=10,
                           border_width=1, border_color=BORDER)
        ctk.CTkFrame(top, height=4, corner_radius=0, fg_color=NAVY).pack(fill="x")
        self.pw.add(top, minsize=120, height=240)

        self.tree = ttk.Treeview(top,
            columns=("ID", "Fecha", "Total", "Descuento", "Productos"),
            show="headings", height=8)
        for col, w, anchor in zip(
                ("ID", "Fecha", "Total", "Descuento", "Productos"),
                [50, 160, 90, 90, 400],
                ["center", "center", "center", "center", "w"]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor=anchor)
        self.tree.tag_configure("anulada", foreground="#9ca3af")
        self.tree.pack(fill="both", expand=True, padx=1, pady=1)
        self.tree.bind("<<TreeviewSelect>>", self.mostrar_detalle)

        # ── Detalle venta ─────────────────────────────────────────────────
        det = ctk.CTkFrame(self.pw, fg_color=WHITE, corner_radius=10,
                           border_width=1, border_color=BORDER)
        ctk.CTkFrame(det, height=4, corner_radius=0, fg_color=ORANGE).pack(fill="x")
        self.pw.add(det, minsize=140)
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

        # ── Botones FIJOS abajo (fuera del panel divisible) ────────────────
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(side="bottom", fill="x", padx=4, pady=(6, 4))
        # El panel divisible ocupa el resto del espacio
        self.pw.pack(side="top", fill="both", expand=True)
        ctk.CTkButton(btn_bar,
                      text="🖨️  Imprimir Factura",
                      height=34, fg_color=ORANGE, hover_color="#ea6c0a",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._imprimir_factura).pack(side="right")
        ctk.CTkButton(btn_bar,
                      text="🚫  Anular venta",
                      height=34, fg_color="#dc2626", hover_color="#b91c1c",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._anular_venta).pack(side="right", padx=(0, 8))

    # ── Calendario popup ──────────────────────────────────────────────────────
    def _toggle_cal(self):
        if self._cal_popup and self._cal_popup.winfo_exists():
            self._cal_popup.destroy()
            self._cal_popup = None
            return

        self._cal_popup = ctk.CTkToplevel(self)
        self._cal_popup.overrideredirect(True)
        self._cal_popup.attributes("-topmost", True)

        cal = CTkCalendar(self._cal_popup, max_date=date.today())
        cal.set_date(self._fecha_sel)
        cal.pack()

        self._cal_popup.update_idletasks()
        x = self.fecha_btn.winfo_rootx()
        y = self.fecha_btn.winfo_rooty() + self.fecha_btn.winfo_height() + 4
        self._cal_popup.geometry(f"+{x}+{y}")

        _orig = cal._select
        def _select_wrap(d):
            _orig(d)
            self._fecha_sel = cal.get_date()
            self.fecha_btn.configure(
                text=f"📅  {self._fecha_sel.strftime('%d/%m/%Y')}")
            self._cal_popup.destroy()
            self._cal_popup = None
            self.refresh()
        cal._select = _select_wrap

    # ── Helpers de fecha ──────────────────────────────────────────────────────
    def _set_hoy(self):
        self._fecha_sel = date.today()
        self.fecha_btn.configure(
            text=f"📅  {self._fecha_sel.strftime('%d/%m/%Y')}")
        self.refresh()

    def _set_ayer(self):
        self._fecha_sel = date.today() - timedelta(days=1)
        self.fecha_btn.configure(
            text=f"📅  {self._fecha_sel.strftime('%d/%m/%Y')}")
        self.refresh()

    def _get_fecha_seleccionada(self):
        if self._fecha_sel > date.today():
            messagebox.showwarning("Aviso", "No puedes seleccionar fechas futuras.")
            return None
        return self._fecha_sel.strftime("%Y-%m-%d")

    # ── Refresh y detalle ─────────────────────────────────────────────────────
    def refresh(self):
        fecha = self._fecha_sel.strftime("%Y-%m-%d")
        buscar = self.buscar_var.get().strip().lower() if hasattr(self, "buscar_var") else ""
        self.tree.delete(*self.tree.get_children())

        normales = [
            (v["id"], v["fecha"], f"Q{v['total']:.2f}",
             f"-Q{v['descuento']:.2f}" if v.get("descuento", 0) > 0 else "—",
             v["resumen"], False)
            for v in get_ventas_hoy(fecha)
        ]
        anuladas = [
            (v["id"], v["fecha"], f"Q{v['total']:.2f}", "—",
             "🚫 ANULADA — " + ", ".join(f"{it['producto']} x{it['cantidad']}" for it in v.get("items", [])),
             True)
            for v in get_ventas_anuladas_hoy(fecha)
        ]

        filas = sorted(normales + anuladas, key=lambda x: x[0], reverse=True)
        # Filtrar por nombre de producto vendido
        if buscar:
            filas = [f for f in filas if buscar in f[4].lower()]

        for vid, fecha_v, total, desc, resumen, anulada in filas:
            self.tree.insert("", "end", iid=vid, values=(vid, fecha_v, total, desc, resumen),
                             tags=("anulada",) if anulada else ())

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
        from database import get_ventas_hoy, get_fiados_hoy, get_ventas_anuladas_hoy

        fecha = self._get_fecha_seleccionada()
        if fecha is None: return

        ventas        = get_ventas_hoy(fecha)
        observaciones = get_observaciones_hoy(fecha)
        fiados        = get_fiados_hoy(fecha)
        anuladas      = get_ventas_anuladas_hoy(fecha)

        if not ventas and not observaciones and not fiados and not anuladas:
            messagebox.showinfo("Sin datos",
                f"No hay ventas, observaciones ni fiados registrados el {fecha}.")
            return

        try:
            ruta = generar_pdf(ventas, observaciones, fiados, fecha, anuladas=anuladas)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}")
            return

        if solo_pdf:
            messagebox.showinfo("PDF generado", f"PDF guardado en:\n{ruta}")
            import subprocess
            subprocess.Popen(f'explorer /select,"{ruta}"')
            return

        return ruta

    def _anular_venta(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Selecciona la venta que quieres anular.")
            return
        venta_id = int(sel[0])
        row = self.tree.item(venta_id, "values")

        # Ya anulada
        if "ANULADA" in str(row[4]):
            messagebox.showinfo("Ya anulada", "Esta venta ya está anulada.")
            return

        if not messagebox.askyesno(
            "Confirmar anulación",
            f"¿Anular la venta #{venta_id} por {row[2]}?\n\n"
            "• La venta quedará marcada como ANULADA (no se borra)\n"
            "• El stock de los productos se devolverá al inventario\n"
            "• No se contará en los totales ni reportes\n\n"
            "Esta acción no se puede deshacer."):
            return

        try:
            anular_venta(venta_id)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        messagebox.showinfo("Venta anulada",
                            f"✅ Venta #{venta_id} anulada.\n"
                            "El stock fue devuelto al inventario.")
        self.refresh()
        self.det_tree.delete(*self.det_tree.get_children())
        # Refrescar inventario e inicio si existen
        for key in ("inventario", "inicio"):
            fr = getattr(self.app, "frames", {}).get(key)
            if fr and hasattr(fr, "refresh"):
                fr.refresh()

    def _imprimir_factura(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Selecciona una venta de la lista primero.")
            return

        venta_id = int(sel[0])
        row = self.tree.item(venta_id, "values")
        fecha_str = row[1]          # "2026-06-02 15:20:48"
        total_str = row[2]          # "Q960.00"
        total = float(total_str.replace("Q", "").replace(",", ""))

        items = get_detalle_venta(venta_id)

        # ── Diálogo datos cliente ─────────────────────────────────────────
        dlg = ctk.CTkToplevel(self)
        dlg.title("Datos del cliente para factura")
        dlg.resizable(False, False)
        dlg.attributes("-topmost", True)
        dlg.grab_set()

        dlg.update_idletasks()
        w, h = 400, 310
        sx = dlg.winfo_screenwidth()
        sy = dlg.winfo_screenheight()
        dlg.geometry(f"{w}x{h}+{(sx-w)//2}+{(sy-h)//2}")

        ctk.CTkLabel(dlg, text="Datos del cliente",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=NAVY).pack(pady=(14, 6))

        campos = [
            ("Nombre / Razón social", "nombre",    "FE Y ALEGRIA"),
            ("NIT",                   "nit",        "C/F"),
            ("Dirección",             "direccion",  ""),
            ("Teléfono",              "telefono",   ""),
            ("E-mail",                "email",      "N/D"),
        ]
        vars_ = {}
        form = ctk.CTkFrame(dlg, fg_color="transparent")
        form.pack(fill="x", padx=20)
        for label, key, placeholder in campos:
            row_f = ctk.CTkFrame(form, fg_color="transparent")
            row_f.pack(fill="x", pady=2)
            ctk.CTkLabel(row_f, text=label, width=160, anchor="w",
                         text_color=NAVY,
                         font=ctk.CTkFont(size=12)).pack(side="left")
            var = ctk.StringVar()
            vars_[key] = var
            ctk.CTkEntry(row_f, textvariable=var,
                         placeholder_text=placeholder,
                         width=200).pack(side="left")

        def _confirmar():
            info = {k: v.get().strip() or ph
                    for (_, k, ph), v in zip(campos, vars_.values())}
            dlg.destroy()
            self._generar_factura_pdf(venta_id, items, total, fecha_str, info)

        ctk.CTkButton(dlg, text="Generar e Imprimir",
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=_confirmar).pack(pady=(10, 4))
        ctk.CTkButton(dlg, text="Cancelar",
                      fg_color="transparent", border_width=1,
                      border_color=BORDER, text_color=NAVY,
                      command=dlg.destroy).pack()

    def _generar_factura_pdf(self, venta_id, items, total, fecha_str, cliente_info):
        from frames.reporte import generar_factura
        import subprocess, os

        from config import recurso
        logo_path = recurso("imagenes/SP Black.png")
        if not os.path.exists(logo_path):
            logo_path = None

        try:
            ruta = generar_factura(venta_id, items, total,
                                   fecha_str, cliente_info, logo_path)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar la factura:\n{e}")
            return

        messagebox.showinfo("Factura generada",
                            f"Factura guardada:\n{os.path.basename(ruta)}\n\n"
                            "Se abrirá la carpeta para que la imprimas.")
        # Abrir la carpeta con la factura seleccionada (no abre el PDF)
        try:
            subprocess.Popen(f'explorer /select,"{ruta}"')
        except Exception:
            os.startfile(os.path.dirname(ruta))

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