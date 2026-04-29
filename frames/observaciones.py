import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
from database import get_observaciones_hoy, agregar_observacion, eliminar_observacion
from config import *

class ObservacionesFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

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

        cols = ("ID","Hora","Concepto","Monto")
        self.tree = ttk.Treeview(izq, columns=cols, show="headings", height=14)
        for col, w in zip(cols, [40, 80, 380, 100]):
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

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        hoy = datetime.now().strftime("%Y-%m-%d")
        rows = get_observaciones_hoy(hoy)
        total = 0.0
        for r in rows:
            hora = r["fecha"][11:16]  # HH:MM
            self.tree.insert("", "end", iid=r["id"], values=(
                r["id"], hora, r["concepto"], f"Q{r['monto']:.2f}"))
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

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        agregar_observacion(fecha, monto, concepto)
        self.concepto_entry.delete(0, "end")
        self.monto_entry.delete(0, "end")
        self.refresh()

    def eliminar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un registro primero."); return
        if messagebox.askyesno("Confirmar", "¿Eliminar este registro?"):
            eliminar_observacion(int(sel[0]))
            self.refresh()