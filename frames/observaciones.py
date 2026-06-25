import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
from database import (get_observaciones_hoy, get_observaciones_todas,
                      agregar_observacion, eliminar_observacion)
from config import *
from frames.ctk_calendar import CTkCalendar

class ObservacionesFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._fecha_sel = date.today()
        self._ver_todos = False
        self._cal_popup = None

        # ── Formulario ────────────────────────────────────────────────────
        form = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10,
                            border_width=1, border_color=BORDER)
        form.pack(fill="x", pady=(0, 12))
        ctk.CTkFrame(form, height=4, corner_radius=0, fg_color=ORANGE).pack(fill="x")

        inner_form = ctk.CTkFrame(form, fg_color="transparent")
        inner_form.pack(fill="x", padx=16, pady=12)

        # Fila: concepto + monto + botón
        ctk.CTkLabel(inner_form, text="Concepto", text_color=NAVY,
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
                     row=0, column=0, sticky="w", padx=(0,12))
        ctk.CTkLabel(inner_form, text="Monto (Q)", text_color=NAVY,
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
                     row=0, column=1, sticky="w", padx=(0,12))

        self.concepto_entry = ctk.CTkEntry(inner_form, width=380,
                                            placeholder_text="Ej: Compra de bolsas")
        self.concepto_entry.grid(row=1, column=0, padx=(0,12), pady=(4,0))

        self.monto_entry = ctk.CTkEntry(inner_form, width=120,
                                         placeholder_text="0.00")
        self.monto_entry.grid(row=1, column=1, padx=(0,12), pady=(4,0))

        ctk.CTkButton(inner_form, text="➕  Agregar", height=36,
                      fg_color=ORANGE, hover_color="#ea6c0a",
                      font=ctk.CTkFont(weight="bold"),
                      command=self.agregar).grid(row=1, column=2, pady=(4,0))

        # ── Fecha opcional del gasto ──────────────────────────────────────
        self._fecha_nueva = None  # None = usar fecha/hora actual
        ctk.CTkLabel(inner_form, text="Fecha del gasto (opcional)", text_color=NAVY,
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
                     row=0, column=3, sticky="w", padx=(40, 0))
        fecha_box = ctk.CTkFrame(inner_form, fg_color="transparent")
        fecha_box.grid(row=1, column=3, sticky="w", padx=(40, 0), pady=(4, 0))
        self.fecha_nueva_btn = ctk.CTkButton(
            fecha_box, text="📅  Hoy (automático)", width=170, height=36,
            fg_color="transparent", border_width=1, border_color=BORDER,
            text_color=NAVY, hover_color=GRAY_BG,
            font=ctk.CTkFont(size=12), command=self._toggle_cal_nueva)
        self.fecha_nueva_btn.pack(side="left")
        ctk.CTkButton(fecha_box, text="✕", width=30, height=36,
                      fg_color="transparent", hover_color=GRAY_BG, text_color=NAVY,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._limpiar_fecha_nueva).pack(side="left", padx=(4, 0))
        self._cal_nueva_popup = None

        # ── Tabla del día ─────────────────────────────────────────────────
        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.pack(fill="both", expand=True)

        # Izquierda: registros de hoy
        izq = ctk.CTkFrame(mid, fg_color=WHITE, corner_radius=10,
                           border_width=1, border_color=BORDER)
        izq.pack(side="left", fill="both", expand=True, padx=(0,10))
        ctk.CTkFrame(izq, height=4, corner_radius=0, fg_color=NAVY).pack(fill="x")

        hdr = ctk.CTkFrame(izq, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(8,4))
        self.fecha_lbl = ctk.CTkLabel(hdr,
            text=f"📅  Gastos del {datetime.now().strftime('%d/%m/%Y')}",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=NAVY)
        self.fecha_lbl.pack(side="left")

        # Botones de navegación de fecha (derecha)
        ctk.CTkButton(hdr, text="Ver todos", width=80, height=26,
                      fg_color=NAVY, hover_color="#1a3d6e", text_color=WHITE,
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=self._set_todos).pack(side="right", padx=(4, 0))
        self.fecha_btn = ctk.CTkButton(hdr,
            text=f"📅  {date.today().strftime('%d/%m/%Y')}",
            width=120, height=26,
            fg_color="transparent", border_width=1, border_color=BORDER,
            text_color=NAVY, hover_color=GRAY_BG,
            font=ctk.CTkFont(size=11), command=self._toggle_cal)
        self.fecha_btn.pack(side="right", padx=(4, 0))
        ctk.CTkButton(hdr, text="Ayer", width=50, height=26,
                      fg_color="transparent", border_width=1, border_color=BORDER,
                      text_color=NAVY, hover_color=GRAY_BG,
                      command=self._set_ayer).pack(side="right", padx=(4, 0))
        ctk.CTkButton(hdr, text="Hoy", width=50, height=26,
                      fg_color="transparent", border_width=1, border_color=BORDER,
                      text_color=NAVY, hover_color=GRAY_BG,
                      command=self._set_hoy).pack(side="right", padx=(4, 0))

        cols = ("ID","Fecha/Hora","Concepto","Monto")
        self.tree = ttk.Treeview(izq, columns=cols, show="headings", height=14)
        for col, w in zip(cols, [40, 140, 340, 100]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=1, pady=(0,1))

        ctk.CTkButton(izq, text="🗑️  Eliminar seleccionado",
                      fg_color="#dc2626", hover_color="#b91c1c",
                      height=32, command=self.eliminar).pack(
                      pady=8, padx=12, anchor="w")

        # Derecha: resumen
        der = ctk.CTkFrame(mid, fg_color=WHITE, corner_radius=10,
                           border_width=1, border_color=BORDER, width=200)
        der.pack(side="right", fill="y")
        der.pack_propagate(False)
        ctk.CTkFrame(der, height=4, corner_radius=0, fg_color=ORANGE).pack(fill="x")

        ctk.CTkLabel(der, text="Resumen del día",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=NAVY).pack(pady=(12,16))

        self.total_lbl = ctk.CTkLabel(der, text="Q0.00",
                                       font=ctk.CTkFont(size=28, weight="bold"),
                                       text_color=ORANGE)
        self.total_lbl.pack()
        ctk.CTkLabel(der, text="total gastado hoy",
                     text_color=TEXT_MUTED,
                     font=ctk.CTkFont(size=11)).pack(pady=(2,20))

        self.cant_lbl = ctk.CTkLabel(der, text="0",
                                      font=ctk.CTkFont(size=22, weight="bold"),
                                      text_color=NAVY)
        self.cant_lbl.pack()
        ctk.CTkLabel(der, text="registros hoy",
                     text_color=TEXT_MUTED,
                     font=ctk.CTkFont(size=11)).pack(pady=(2,0))

    # ── Fecha opcional del nuevo gasto ────────────────────────────────────────
    def _limpiar_fecha_nueva(self):
        self._fecha_nueva = None
        self.fecha_nueva_btn.configure(text="📅  Hoy (automático)")

    def _toggle_cal_nueva(self):
        if self._cal_nueva_popup and self._cal_nueva_popup.winfo_exists():
            self._cal_nueva_popup.destroy()
            self._cal_nueva_popup = None
            return
        self._cal_nueva_popup = ctk.CTkToplevel(self)
        self._cal_nueva_popup.overrideredirect(True)
        self._cal_nueva_popup.attributes("-topmost", True)
        cal = CTkCalendar(self._cal_nueva_popup, max_date=date.today())
        cal.set_date(self._fecha_nueva or date.today())
        cal.pack()
        self._cal_nueva_popup.update_idletasks()
        x = self.fecha_nueva_btn.winfo_rootx()
        y = self.fecha_nueva_btn.winfo_rooty() + self.fecha_nueva_btn.winfo_height() + 4
        self._cal_nueva_popup.geometry(f"+{x}+{y}")
        _orig = cal._select
        def _wrap(d):
            _orig(d)
            self._fecha_nueva = cal.get_date()
            self.fecha_nueva_btn.configure(
                text=f"📅  {self._fecha_nueva.strftime('%d/%m/%Y')}")
            self._cal_nueva_popup.destroy()
            self._cal_nueva_popup = None
        cal._select = _wrap

    # ── Navegación de fecha ───────────────────────────────────────────────────
    def _set_hoy(self):
        self._ver_todos = False
        self._fecha_sel = date.today()
        self.fecha_btn.configure(text=f"📅  {self._fecha_sel.strftime('%d/%m/%Y')}")
        self.refresh()

    def _set_ayer(self):
        self._ver_todos = False
        self._fecha_sel = date.today() - timedelta(days=1)
        self.fecha_btn.configure(text=f"📅  {self._fecha_sel.strftime('%d/%m/%Y')}")
        self.refresh()

    def _set_todos(self):
        self._ver_todos = True
        self.refresh()

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
        def _wrap(d):
            _orig(d)
            self._ver_todos = False
            self._fecha_sel = cal.get_date()
            self.fecha_btn.configure(text=f"📅  {self._fecha_sel.strftime('%d/%m/%Y')}")
            self._cal_popup.destroy()
            self._cal_popup = None
            self.refresh()
        cal._select = _wrap

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        if self._ver_todos:
            rows = get_observaciones_todas()
            self.fecha_lbl.configure(text="📅  Todos los gastos")
        else:
            fecha = self._fecha_sel.strftime("%Y-%m-%d")
            rows = get_observaciones_hoy(fecha)
            self.fecha_lbl.configure(
                text=f"📅  Gastos del {self._fecha_sel.strftime('%d/%m/%Y')}")

        total = 0.0
        for r in rows:
            # Si veo todos o una fecha pasada, muestro fecha completa; si es hoy, solo hora
            if self._ver_todos:
                fecha_hora = r["fecha"][:16].replace("-", "/")  # YYYY/MM/DD HH:MM
            else:
                fecha_hora = r["fecha"][11:16]  # HH:MM
            self.tree.insert("", "end", iid=r["id"], values=(
                r["id"], fecha_hora, r["concepto"], f"Q{r['monto']:.2f}"))
            total += r["monto"]
        self.total_lbl.configure(text=f"Q{total:.2f}")
        self.cant_lbl.configure(text=str(len(rows)))

    def agregar(self):
        concepto = self.concepto_entry.get().strip()
        monto_s  = self.monto_entry.get().strip()
        if not concepto:
            messagebox.showwarning("Aviso", "Escribe el concepto del gasto."); return
        try:
            monto = float(monto_s)
            if monto <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "El monto debe ser un número mayor a 0."); return

        ahora = datetime.now()
        if self._fecha_nueva is not None:
            # Fecha elegida + hora actual
            fecha = f"{self._fecha_nueva.strftime('%Y-%m-%d')} {ahora.strftime('%H:%M:%S')}"
            fecha_destino = self._fecha_nueva
        else:
            fecha = ahora.strftime("%Y-%m-%d %H:%M:%S")
            fecha_destino = date.today()

        agregar_observacion(fecha, monto, concepto)
        self.concepto_entry.delete(0, "end")
        self.monto_entry.delete(0, "end")
        self._limpiar_fecha_nueva()

        # Mostrar la fecha donde quedó el gasto
        self._ver_todos = False
        self._fecha_sel = fecha_destino
        self.fecha_btn.configure(text=f"📅  {fecha_destino.strftime('%d/%m/%Y')}")
        self.refresh()

    def eliminar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un registro primero."); return
        if messagebox.askyesno("Confirmar", "¿Eliminar este registro?"):
            eliminar_observacion(int(sel[0]))
            self.refresh()