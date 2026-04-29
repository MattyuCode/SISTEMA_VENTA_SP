import os
import requests
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer, HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

# ── Configuración WhatsApp API ────────────────────────────────────────────────
WA_URL_BASE   = "http://localhost:5001"
WA_URL_ARCHIVO= f"{WA_URL_BASE}/enviar-archivo"
WA_URL_MENSAJE= f"{WA_URL_BASE}/enviar-mensaje"

# Número destino en formato: "502XXXXXXXX" (sin +, sin @c.us — tu API lo formatea sola)
WA_NUMERO     = "50245412844"   # ← CAMBIA ESTO por tu número

MESES_ES = {
    "January":"enero",   "February":"febrero", "March":"marzo",
    "April":"abril",     "May":"mayo",         "June":"junio",
    "July":"julio",      "August":"agosto",    "September":"septiembre",
    "October":"octubre", "November":"noviembre","December":"diciembre",
}

def fecha_es(fecha_str):
    """Convierte '2026-04-20' → '20 de abril de 2026'"""
    dt = datetime.strptime(fecha_str, "%Y-%m-%d")
    mes_en = dt.strftime("%B")
    mes_es = MESES_ES.get(mes_en, mes_en)
    return f"{dt.day} de {mes_es} de {dt.year}"

NAVY   = colors.HexColor("#0d2b55")
ORANGE = colors.HexColor("#F97316")

# ── Generar PDF ───────────────────────────────────────────────────────────────
def generar_pdf(ventas, observaciones, fiados, fecha):
    """
    ventas        = lista de dicts {fecha, total, resumen}
    observaciones = lista de dicts {fecha, monto, concepto}
    fiados        = lista de dicts {fecha, cliente, total, estado, resumen}
    fecha         = str "YYYY-MM-DD"
    """
    nombre_archivo = f"reporte_{fecha}.pdf"
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", nombre_archivo)
    ruta = os.path.normpath(ruta)

    doc = SimpleDocTemplate(ruta, pagesize=letter,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    titulo_style = ParagraphStyle("titulo", fontSize=18, textColor=NAVY,
                                   alignment=TA_CENTER, spaceAfter=4,
                                   fontName="Helvetica-Bold")
    sub_style    = ParagraphStyle("sub", fontSize=11, textColor=ORANGE,
                                   alignment=TA_CENTER, spaceAfter=2,
                                   fontName="Helvetica-Bold")
    normal       = ParagraphStyle("normal", fontSize=9, spaceAfter=2,
                                   fontName="Helvetica")
    bold         = ParagraphStyle("bold", fontSize=10, spaceAfter=4,
                                   fontName="Helvetica-Bold", textColor=NAVY)

    elements = []
    elements.append(Paragraph("Soluciones Plus", titulo_style))
    elements.append(Paragraph("Reporte de ventas del día", sub_style))
    elements.append(Paragraph(fecha_es(fecha),
        ParagraphStyle("fecha", fontSize=10, alignment=TA_CENTER,
                        textColor=colors.grey)))
    elements.append(Spacer(1, 0.4*cm))
    elements.append(HRFlowable(width="100%", thickness=2, color=ORANGE, spaceAfter=10))

    # ── Ventas ────────────────────────────────────────────────────────────────
    elements.append(Paragraph("Ventas del día", bold))
    total_dia = 0.0
    total_pagos_fiados = 0.0
    if not ventas and not any(f["estado"] == "pagado" for f in fiados):
        elements.append(Paragraph("No hubo ventas este día.", normal))
    else:
        data = [["#", "Hora", "Producto", "Cantidad", "Precio", "Subtotal", "Total"]]
        estilos_fila = []

        fila_idx = 1
        for i, v in enumerate(ventas, 1):
            hora = v["fecha"][11:16]
            items = v.get("items", [])

            # Fila de cabecera de la venta
            data.append([str(i), hora, "", "", "", "", f"Q{v['total']:.2f}"])
            estilos_fila.append(("cabecera", fila_idx))
            fila_idx += 1

            for it in items:
                data.append(["", "",
                             it["producto"],
                             str(it["cantidad"]),
                             f"Q{it['precio']:.2f}",
                             f"Q{it['subtotal']:.2f}",
                             ""])
                fila_idx += 1

            total_dia += v["total"]

        # ── Filas de pagos de fiados de hoy ───────────────────────────────
        fiados_pagados_hoy = [f for f in fiados if f["estado"] == "pagado"]
        filas_pagos = []
        for f in fiados_pagados_hoy:
            hora_pago = f["fecha"][11:16]   # fecha ya viene con la hora del pago
            data.append(["💵", hora_pago,
                         f"{f['cliente']} pagó su deuda",
                         "", "", "",
                         f"Q{f['total']:.2f}"])
            filas_pagos.append(fila_idx)
            total_pagos_fiados += f["total"]
            fila_idx += 1

        # Total final (ventas + pagos de fiados)
        total_ingreso = total_dia + total_pagos_fiados
        data.append(["", "", "", "", "", "TOTAL VENTAS DEL DÍA",
                     f"Q{total_ingreso:.2f}"])

        tabla = Table(data,
            colWidths=[0.8*cm, 1.2*cm, 6.5*cm, 1.8*cm, 1.8*cm, 1.9*cm, 2*cm],
            repeatRows=1)

        estilo = [
            # Header
            ("BACKGROUND",   (0,0), (-1,0), NAVY),
            ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
            ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,0), 9),
            ("ALIGN",        (0,0), (-1,0), "CENTER"),
            ("ALIGN",        (2,0), (2,0), "LEFT"),
            # Cuerpo
            ("FONTSIZE",     (0,1), (-1,-2), 8),
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN",        (0,1), (1,-2), "CENTER"),
            ("ALIGN",        (3,1), (5,-2), "CENTER"),
            ("ALIGN",        (5,1), (5,-2), "RIGHT"),
            ("ALIGN",        (6,1), (6,-2), "RIGHT"),
            ("GRID",         (0,0), (-1,-2), 0.3, colors.HexColor("#e2e8f0")),
            # Total final
            ("BACKGROUND",   (0,-1), (-1,-1), colors.HexColor("#f0f4f8")),
            ("FONTNAME",     (0,-1), (-1,-1), "Helvetica-Bold"),
            ("FONTSIZE",     (0,-1), (-1,-1), 10),
            ("TEXTCOLOR",    (0,-1), (-1,-1), NAVY),
            ("ALIGN",        (5,-1), (5,-1), "RIGHT"),
            ("ALIGN",        (6,-1), (6,-1), "RIGHT"),
            ("LINEABOVE",    (0,-1), (-1,-1), 2, ORANGE),
            ("TOPPADDING",   (0,-1), (-1,-1), 8),
            ("BOTTOMPADDING",(0,-1), (-1,-1), 8),
        ]

        # Cabeceras de ventas
        for tipo, idx in estilos_fila:
            if tipo == "cabecera":
                estilo.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#f0f4f8")))
                estilo.append(("FONTNAME",   (0, idx), (-1, idx), "Helvetica-Bold"))
                estilo.append(("TEXTCOLOR",  (0, idx), (-1, idx), NAVY))
                estilo.append(("TEXTCOLOR",  (6, idx), (6, idx), ORANGE))
                estilo.append(("FONTSIZE",   (0, idx), (-1, idx), 9))

        # Filas de pagos de fiados (verde para destacar el ingreso)
        for idx in filas_pagos:
            estilo.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#ecfdf5")))
            estilo.append(("FONTNAME",   (0, idx), (-1, idx), "Helvetica-Bold"))
            estilo.append(("TEXTCOLOR",  (0, idx), (-1, idx), colors.HexColor("#166534")))
            estilo.append(("TEXTCOLOR",  (6, idx), (6, idx), colors.HexColor("#15803d")))
            estilo.append(("FONTSIZE",   (0, idx), (-1, idx), 9))
            estilo.append(("ALIGN",      (2, idx), (2, idx), "LEFT"))

        tabla.setStyle(TableStyle(estilo))
        elements.append(tabla)

    elements.append(Spacer(1, 0.5*cm))

    # ── Observaciones ─────────────────────────────────────────────────────────
    elements.append(HRFlowable(width="100%", thickness=0.5,
                                color=colors.HexColor("#e2e8f0"), spaceAfter=8))
    elements.append(Paragraph("Gastos / Observaciones del día", bold))
    total_gastos = 0.0
    if not observaciones:
        elements.append(Paragraph("No hubo gastos registrados.", normal))
    else:
        data_obs = [["Hora", "Concepto", "Monto"]]
        for o in observaciones:
            hora = o["fecha"][11:16]
            data_obs.append([hora, o["concepto"], f"Q{o['monto']:.2f}"])
            total_gastos += o["monto"]
        data_obs.append(["", "TOTAL GASTOS", f"Q{total_gastos:.2f}"])

        tabla_obs = Table(data_obs, colWidths=[1.5*cm, 12*cm, 2.5*cm])
        tabla_obs.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), NAVY),
            ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,0), 9),
            ("ALIGN",         (0,0), (-1,0), "CENTER"),
            ("FONTNAME",      (0,1), (-1,-2), "Helvetica"),
            ("FONTSIZE",      (0,1), (-1,-2), 8),
            ("ROWBACKGROUNDS",(0,1), (-1,-2), [colors.white, colors.HexColor("#f8fafc")]),
            ("ALIGN",         (2,1), (2,-1), "RIGHT"),
            ("GRID",          (0,0), (-1,-2), 0.3, colors.HexColor("#e2e8f0")),
            ("BACKGROUND",    (0,-1), (-1,-1), colors.HexColor("#f0f4f8")),
            ("FONTNAME",      (0,-1), (-1,-1), "Helvetica-Bold"),
            ("TEXTCOLOR",     (1,-1), (2,-1), colors.HexColor("#dc2626")),
            ("LINEABOVE",     (0,-1), (-1,-1), 1.5, colors.HexColor("#dc2626")),
        ]))
        elements.append(tabla_obs)

    # ── Fiados del día ────────────────────────────────────────────────────────
    elements.append(Spacer(1, 0.3*cm))
    elements.append(HRFlowable(width="100%", thickness=0.5,
                                color=colors.HexColor("#e2e8f0"), spaceAfter=8))
    elements.append(Paragraph("Fiados — pagos de hoy y pendientes", bold))

    total_fiados = 0.0
    if not fiados:
        elements.append(Paragraph("No hubo fiados registrados hoy.", normal))
    else:
        data_fi = [["Hora", "Cliente", "Producto", "Cant", "Precio", "Subtotal", "Estado", "Total"]]
        cabeceras_fi = []
        fila_idx = 1

        for f in fiados:
            hora = f["fecha"][11:16]
            estado = "Pagado" if f["estado"] == "pagado" else "Pendiente"
            items = f.get("items", [])

            # Fila cabecera del fiado
            data_fi.append([hora, f["cliente"], "", "", "", "", estado, f"Q{f['total']:.2f}"])
            cabeceras_fi.append((fila_idx, f["estado"]))
            fila_idx += 1

            # Items
            for it in items:
                data_fi.append(["", "",
                                it["producto"],
                                str(it["cantidad"]),
                                f"Q{it['precio']:.2f}",
                                f"Q{it['subtotal']:.2f}",
                                "", ""])
                fila_idx += 1

            total_fiados += f["total"]

        # Total
        data_fi.append(["", "", "", "", "", "", "TOTAL FIADOS", f"Q{total_fiados:.2f}"])

        tabla_fi = Table(data_fi,
            colWidths=[1.2*cm, 3*cm, 5*cm, 1.3*cm, 1.5*cm, 1.6*cm, 1.5*cm, 1.9*cm],
            repeatRows=1)

        estilo_fi = [
            # Header
            ("BACKGROUND",    (0,0), (-1,0), NAVY),
            ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,0), 8.5),
            ("ALIGN",         (0,0), (-1,0), "CENTER"),
            ("ALIGN",         (2,0), (2,0), "LEFT"),
            # Cuerpo
            ("FONTSIZE",      (0,1), (-1,-2), 8),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN",         (0,1), (1,-2), "CENTER"),
            ("ALIGN",         (3,1), (7,-2), "CENTER"),
            ("ALIGN",         (5,1), (5,-2), "RIGHT"),
            ("ALIGN",         (7,1), (7,-2), "RIGHT"),
            ("GRID",          (0,0), (-1,-2), 0.3, colors.HexColor("#e2e8f0")),
            # Total
            ("BACKGROUND",    (0,-1), (-1,-1), colors.HexColor("#f0f4f8")),
            ("FONTNAME",      (0,-1), (-1,-1), "Helvetica-Bold"),
            ("FONTSIZE",      (0,-1), (-1,-1), 10),
            ("TEXTCOLOR",     (0,-1), (-1,-1), colors.HexColor("#b45309")),
            ("ALIGN",         (6,-1), (6,-1), "RIGHT"),
            ("ALIGN",         (7,-1), (7,-1), "RIGHT"),
            ("LINEABOVE",     (0,-1), (-1,-1), 2, ORANGE),
            ("TOPPADDING",    (0,-1), (-1,-1), 8),
            ("BOTTOMPADDING", (0,-1), (-1,-1), 8),
        ]

        # Estilo a las cabeceras de cada fiado
        for idx, estado in cabeceras_fi:
            estilo_fi.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#f0f4f8")))
            estilo_fi.append(("FONTNAME",   (0, idx), (-1, idx), "Helvetica-Bold"))
            estilo_fi.append(("TEXTCOLOR",  (0, idx), (-1, idx), NAVY))
            estilo_fi.append(("TEXTCOLOR",  (7, idx), (7, idx), ORANGE))
            estilo_fi.append(("FONTSIZE",   (0, idx), (-1, idx), 9))
            # color del estado según si pagado o pendiente
            color_estado = colors.HexColor("#16a34a") if estado == "pagado" else colors.HexColor("#b45309")
            estilo_fi.append(("TEXTCOLOR",  (6, idx), (6, idx), color_estado))

        tabla_fi.setStyle(TableStyle(estilo_fi))
        elements.append(tabla_fi)

    # ── Resumen final ─────────────────────────────────────────────────────────
    elements.append(Spacer(1, 0.5*cm))

    # Solo los fiados que quedaron pendientes hoy (no los pagados)
    total_fiados_pendientes = sum(
        f["total"] for f in fiados if f["estado"] == "pendiente"
    )

    ingresos = total_dia + total_pagos_fiados
    neto = ingresos - total_gastos

    resumen_data = [
        ["Total ventas",         f"+Q{total_dia:.2f}"],
        ["Pagos de fiados hoy",  f"+Q{total_pagos_fiados:.2f}"],
        ["Ingreso total",        f"Q{ingresos:.2f}"],
        ["Total gastos",         f"-Q{total_gastos:.2f}"],
        ["Fiados pendientes hoy",f"Q{total_fiados_pendientes:.2f}"],
        ["NETO DEL DÍA",         f"Q{neto:.2f}"],
    ]

    resumen = Table(resumen_data, colWidths=[10*cm, 5*cm])
    resumen.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",  (0,0), (-1,-2), 10),
        ("ALIGN",     (1,0), (1,-1), "RIGHT"),
        ("TEXTCOLOR", (0,0), (-1,-2), colors.HexColor("#374151")),
        ("TOPPADDING",    (0,0), (-1,-2), 3),
        ("BOTTOMPADDING", (0,0), (-1,-2), 3),

        # Ingresos (verde)
        ("TEXTCOLOR", (1,0), (1,1), colors.HexColor("#15803d")),
        # Ingreso total (bold navy)
        ("FONTNAME",  (0,2), (-1,2), "Helvetica-Bold"),
        ("TEXTCOLOR", (0,2), (-1,2), NAVY),
        ("LINEABOVE", (0,2), (-1,2), 0.5, colors.HexColor("#e2e8f0")),
        # Gastos (rojo)
        ("TEXTCOLOR", (1,3), (1,3), colors.HexColor("#b91c1c")),
        # Fiados pendientes (naranja informativo)
        ("TEXTCOLOR", (0,4), (-1,4), colors.HexColor("#b45309")),
        ("FONTSIZE",  (0,4), (-1,4), 9),

        # NETO DEL DÍA — destacado
        ("BACKGROUND",(0,-1), (-1,-1), NAVY),
        ("TEXTCOLOR", (0,-1), (-1,-1), colors.white),
        ("FONTNAME",  (0,-1), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,-1), (-1,-1), 13),
        ("TOPPADDING",    (0,-1), (-1,-1), 8),
        ("BOTTOMPADDING", (0,-1), (-1,-1), 8),
    ]))
    elements.append(resumen)

    # Nota aclaratoria
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        "* Los fiados pendientes no afectan el neto hasta que el cliente pague.",
        ParagraphStyle("nota", fontSize=8, textColor=colors.grey,
                        alignment=TA_RIGHT)))

    elements.append(Spacer(1, 0.6*cm))
    elements.append(HRFlowable(width="100%", thickness=2, color=NAVY))
    elements.append(Paragraph(
        f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} — Soluciones Plus",
        ParagraphStyle("pie", fontSize=8, textColor=colors.grey,
                        alignment=TA_CENTER)))

    doc.build(elements)
    return ruta


# ── Enviar por WhatsApp usando form-data ──────────────────────────────────────
def enviar_reporte_whatsapp(ruta_pdf, numero=WA_NUMERO):
    """
    Envía el PDF adjunto al WhatsApp del número indicado.
    Usa el endpoint /enviar-archivo con multipart/form-data.
    """
    try:
        fecha = datetime.now().strftime("%d/%m/%Y")
        caption = (f"📊 Reporte Soluciones Plus\n"
                   f"📅 {fecha}\n\n"
                   f"Reporte del día adjunto.")

        with open(ruta_pdf, "rb") as f:
            files = {
                "file": (os.path.basename(ruta_pdf), f, "application/pdf")
            }
            data = {
                "number":  numero,
                "caption": caption,
            }
            r = requests.post(WA_URL_ARCHIVO, files=files, data=data, timeout=30)

        if r.status_code == 200:
            return True, "Enviado correctamente"

        try:
            msg = r.json().get("message", r.text)
        except Exception:
            msg = r.text
        return False, f"Error {r.status_code}: {msg}"

    except requests.exceptions.ConnectionError:
        return False, ("No se pudo conectar con la API de WhatsApp.\n"
                       "Verifica que esté corriendo en http://localhost:5001")
    except requests.exceptions.Timeout:
        return False, "La API tardó demasiado en responder."
    except Exception as e:
        return False, f"Error inesperado: {e}"