import customtkinter as ctk
from datetime import date
import calendar

MESES_ES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
DIAS_ES  = ["L","M","M","J","V","S","D"]

NAVY   = "#0d2b55"
ORANGE = "#F97316"


class CTkCalendar(ctk.CTkFrame):
    """
    Calendario emergente para CustomTkinter.
    Uso:
        cal = CTkCalendar(parent)
        cal.pack(...)
        fecha = cal.get_date()   # retorna date object
        cal.set_date(date.today())
    """
    def __init__(self, parent, max_date=None, **kwargs):
        super().__init__(parent, fg_color="white",
                         border_width=1, border_color="#e2e8f0",
                         corner_radius=10, **kwargs)
        self._max_date  = max_date or date.today()
        self._selected  = date.today()
        self._view_year = self._selected.year
        self._view_month= self._selected.month
        self._build()

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        # ── Header: mes/año + flechas ─────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=NAVY, corner_radius=0)
        header.pack(fill="x")

        ctk.CTkButton(header, text="‹", width=32, height=30,
                      fg_color="transparent", hover_color="#1a3d6e",
                      text_color="white", font=ctk.CTkFont(size=16),
                      command=self._prev_month).pack(side="left")

        ctk.CTkLabel(header,
                     text=f"{MESES_ES[self._view_month-1]} {self._view_year}",
                     text_color="white",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", expand=True)

        ctk.CTkButton(header, text="›", width=32, height=30,
                      fg_color="transparent", hover_color="#1a3d6e",
                      text_color="white", font=ctk.CTkFont(size=16),
                      command=self._next_month).pack(side="right")

        # ── Días de la semana ─────────────────────────────────────────────
        dias_frame = ctk.CTkFrame(self, fg_color="white")
        dias_frame.pack(fill="x", padx=6, pady=(6, 0))
        for d in DIAS_ES:
            ctk.CTkLabel(dias_frame, text=d, width=28,
                         text_color="#94a3b8",
                         font=ctk.CTkFont(size=11)).pack(side="left", expand=True)

        # ── Días del mes ──────────────────────────────────────────────────
        grid = ctk.CTkFrame(self, fg_color="white")
        grid.pack(fill="x", padx=6, pady=(2, 6))

        cal = calendar.monthcalendar(self._view_year, self._view_month)
        hoy = date.today()

        for semana in cal:
            row = ctk.CTkFrame(grid, fg_color="white")
            row.pack(fill="x")
            for dia in semana:
                if dia == 0:
                    ctk.CTkLabel(row, text="", width=28).pack(side="left", expand=True)
                else:
                    d = date(self._view_year, self._view_month, dia)
                    es_futuro   = d > self._max_date
                    es_hoy      = d == hoy
                    es_sel      = d == self._selected

                    if es_sel:
                        fg, tc, hover = ORANGE, "white", "#ea6c0a"
                    elif es_hoy:
                        fg, tc, hover = "#e2e8f0", NAVY, "#cbd5e1"
                    elif es_futuro:
                        fg, tc, hover = "white", "#cbd5e1", "white"
                    else:
                        fg, tc, hover = "white", "#374151", "#f1f5f9"

                    btn = ctk.CTkButton(row, text=str(dia),
                                        width=28, height=26,
                                        fg_color=fg,
                                        text_color=tc,
                                        hover_color=hover,
                                        corner_radius=6,
                                        font=ctk.CTkFont(size=11),
                                        state="disabled" if es_futuro else "normal",
                                        command=lambda d=d: self._select(d))
                    btn.pack(side="left", expand=True, padx=1, pady=1)

        # ── Botones Hoy / Ayer ────────────────────────────────────────────
        from datetime import timedelta
        footer = ctk.CTkFrame(self, fg_color="white")
        footer.pack(fill="x", padx=6, pady=(0, 6))

        ctk.CTkButton(footer, text="Hoy", height=26, width=70,
                      fg_color="transparent", border_width=1,
                      border_color="#e2e8f0", text_color=NAVY,
                      hover_color="#f1f5f9", font=ctk.CTkFont(size=11),
                      command=lambda: self._select(date.today())).pack(side="left", padx=(0, 4))

        ayer = date.today() - timedelta(days=1)
        ctk.CTkButton(footer, text="Ayer", height=26, width=70,
                      fg_color="transparent", border_width=1,
                      border_color="#e2e8f0", text_color=NAVY,
                      hover_color="#f1f5f9", font=ctk.CTkFont(size=11),
                      command=lambda: self._select(ayer)).pack(side="left")

    def _select(self, d):
        self._selected  = d
        self._view_year = d.year
        self._view_month= d.month
        self._build()

    def _prev_month(self):
        if self._view_month == 1:
            self._view_month = 12
            self._view_year -= 1
        else:
            self._view_month -= 1
        self._build()

    def _next_month(self):
        # No pasar del mes actual
        hoy = date.today()
        if (self._view_year, self._view_month) >= (hoy.year, hoy.month):
            return
        if self._view_month == 12:
            self._view_month = 1
            self._view_year += 1
        else:
            self._view_month += 1
        self._build()

    def get_date(self):
        return self._selected

    def set_date(self, d):
        if isinstance(d, str):
            from datetime import datetime
            d = datetime.strptime(d, "%Y-%m-%d").date()
        self._selected  = d
        self._view_year = d.year
        self._view_month= d.month
        self._build()