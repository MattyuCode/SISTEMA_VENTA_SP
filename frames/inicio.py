import customtkinter as ctk
from tkinter import ttk
from datetime import datetime
from database import get_stats, get_stock_bajo
from config import *

class InicioFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()

        # ── Estadísticas ──────────────────────────────────────────────────
        hoy = datetime.now().strftime("%Y-%m-%d")
        mes = datetime.now().strftime("%Y-%m")
        total_prod, sin_stock, ventas_hoy, ventas_mes = get_stats(hoy, mes)

        # ── Tarjetas ──────────────────────────────────────────────────────
        cards_row = ctk.CTkFrame(self, fg_color="transparent")
        cards_row.pack(fill="x", pady=(0, 20))

        for title, val, color in [
            ("📦 Productos",  str(total_prod),          NAVY),
            ("⚠️ Sin stock",  str(sin_stock),            ORANGE),
            ("💰 Ventas hoy", f"Q{ventas_hoy:.2f}",     "#16a34a"),
            ("📅 Ventas mes", f"Q{ventas_mes:.2f}",     "#7c3aed"),
        ]:
            card = ctk.CTkFrame(cards_row, width=190, height=96,
                                corner_radius=12, fg_color=WHITE,
                                border_width=1, border_color=BORDER)
            card.pack(side="left", padx=(0, 12))
            card.pack_propagate(False)
            ctk.CTkFrame(card, height=4, corner_radius=0, fg_color=color).pack(fill="x")
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12),
                         text_color=TEXT_MUTED).pack(pady=(8, 2))
            ctk.CTkLabel(card, text=val,
                         font=ctk.CTkFont(size=22, weight="bold"),
                         text_color=color).pack()

        # ── Tabla stock bajo ──────────────────────────────────────────────
        ctk.CTkLabel(self, text="⚠️  Productos con stock bajo (≤ 5)",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=NAVY).pack(anchor="w", pady=(0, 8))

        tabla = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10,
                             border_width=1, border_color=BORDER)
        tabla.pack(fill="both", expand=True)

        cols = ("Producto", "Variante", "Categoría", "Stock", "Estado")
        tree = ttk.Treeview(tabla, columns=cols, show="headings", height=12)
        for col, w in zip(cols, [160, 140, 120, 70, 90]):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")
        tree.tag_configure("sin_stock", foreground="#b91c1c")
        tree.tag_configure("bajo",      foreground="#b45309")

        sb = ctk.CTkScrollbar(tabla, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        sb.pack(side="right", fill="y")

        rows = get_stock_bajo(limite=5)
        if not rows:
            tree.insert("", "end", values=(
                "", "", "Todo el inventario tiene stock suficiente.", "", ""))
        else:
            for r in rows:
                estado = "❌ Agotado" if r["stock"] == 0 else "⚠️ Bajo"
                tag    = "sin_stock"  if r["stock"] == 0 else "bajo"
                tree.insert("", "end", values=(
                    r["nombre"], r["variante"] or "—",
                    r["cat"], r["stock"], estado), tags=(tag,))