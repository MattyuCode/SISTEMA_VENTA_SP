import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
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

        # ── Tabla ventas ──────────────────────────────────────────────────
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

        # ── Detalle venta ─────────────────────────────────────────────────
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

    def generar(self, solo_pdf=False):
        from frames.reporte import generar_pdf
        from database import get_ventas_hoy, get_fiados_hoy

        hoy = datetime.now().strftime("%Y-%m-%d")
        ventas        = get_ventas_hoy(hoy)
        observaciones = get_observaciones_hoy(hoy)
        fiados        = get_fiados_hoy(hoy)

        if not ventas and not observaciones and not fiados:
            messagebox.showinfo("Sin datos",
                "No hay ventas, observaciones ni fiados registrados hoy."); return

        try:
            ruta = generar_pdf(ventas, observaciones, fiados, hoy)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}")
            return

        if solo_pdf:
            messagebox.showinfo("PDF generado",
                f"PDF guardado en:\n{ruta}")
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