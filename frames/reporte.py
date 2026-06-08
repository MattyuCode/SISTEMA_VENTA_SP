import os
import requests
from datetime import datetime
from num2words import num2words
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer, HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas as rl_canvas

# ── Configuración WhatsApp API ────────────────────────────────────────────────
WA_URL_BASE   = "http://localhost:5001"
WA_URL_ARCHIVO= f"{WA_URL_BASE}/enviar-archivo"
WA_URL_MENSAJE= f"{WA_URL_BASE}/enviar-mensaje"

WA_NUMERO     = "50245412844"

MESES_ES = {
    "January":"enero",   "February":"febrero", "March":"marzo",
    "April":"abril",     "May":"mayo",         "June":"junio",
    "July":"julio",      "August":"agosto",    "September":"septiembre",
    "October":"octubre", "November":"noviembre","December":"diciembre",
}

def fecha_es(fecha_str):
    dt = datetime.strptime(fecha_str, "%Y-%m-%d")
    mes_en = dt.strftime("%B")
    mes_es = MESES_ES.get(mes_en, mes_en)
    return f"{dt.day} de {mes_es} de {dt.year}"

NAVY   = colors.HexColor("#0d2b55")
ORANGE = colors.HexColor("#F97316")

# ── Generar PDF ───────────────────────────────────────────────────────────────
def generar_pdf(ventas, observaciones, fiados, fecha, anuladas=None):

    carpeta_base = os.path.join(os.path.expanduser("~"), "Documents", "SISTEMA_SP", "Reportes")
    os.makedirs(carpeta_base, exist_ok=True)

    hora_actual = datetime.now().strftime("%H%M%S")
    nombre_archivo = f"reporte_{fecha}_{hora_actual}.pdf"
    ruta = os.path.join(carpeta_base, nombre_archivo)
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
    total_descuentos = 0.0
    total_pagos_fiados = 0.0

    if not ventas and not any(f["estado"] == "pagado" for f in fiados):
        elements.append(Paragraph("No hubo ventas este día.", normal))
    else:
        # Ahora tiene columna Descuento
        data = [["#", "Hora", "Producto", "Cantidad", "Precio", "Descuento", "Subtotal", "Total"]]
        estilos_fila = []

        # Estilos para el nombre del producto (se ajustan en varias líneas)
        prodv_style_bold = ParagraphStyle("prodv_b", fontSize=8, leading=9.5,
                                           fontName="Helvetica-Bold", textColor=NAVY)
        prodv_style = ParagraphStyle("prodv", fontSize=8, leading=9.5,
                                      fontName="Helvetica", textColor=colors.HexColor("#374151"))

        fila_idx = 1
        for i, v in enumerate(ventas, 1):
            hora = v["fecha"][11:16]
            items = v.get("items", [])
            descuento_v = v.get("descuento", 0) or 0

            if items:
                # Primera fila: cabecera + primer item
                it = items[0]
                desc_item = it.get("descuento", 0.0)
                desc_txt = f"-Q{desc_item:.2f}" if desc_item > 0 else "—"
                sub_final = max(0.0, it["subtotal"] - desc_item)
                data.append([str(i), hora,
                             Paragraph(it["producto"], prodv_style_bold),
                             str(it["cantidad"]),
                             f"Q{it['precio']:.2f}",
                             desc_txt,
                             f"Q{sub_final:.2f}",
                             f"Q{v['total']:.2f}"])
                estilos_fila.append(("cabecera", fila_idx, desc_item > 0))
                fila_idx += 1

                # Resto de items
                for it in items[1:]:
                    desc_item = it.get("descuento", 0.0)
                    desc_txt = f"-Q{desc_item:.2f}" if desc_item > 0 else "—"
                    sub_final = max(0.0, it["subtotal"] - desc_item)
                    data.append(["", "",
                                 Paragraph(it["producto"], prodv_style),
                                 str(it["cantidad"]),
                                 f"Q{it['precio']:.2f}",
                                 desc_txt,
                                 f"Q{sub_final:.2f}",
                                 ""])
                    if desc_item > 0:
                        estilos_fila.append(("item_descuento", fila_idx, True))
                    fila_idx += 1
            else:
                data.append([str(i), hora, "", "", "", "",
                             "—", f"Q{v['total']:.2f}"])
                estilos_fila.append(("cabecera", fila_idx, False))
                fila_idx += 1

            if descuento_v > 0:
                total_descuentos += descuento_v
            total_dia += v["total"]

        # Filas de pagos de fiados de hoy
        fiados_pagados_hoy = [f for f in fiados if f["estado"] == "pagado"]
        filas_pagos = []
        for f in fiados_pagados_hoy:
            hora_pago = f["fecha"][11:16]
            data.append(["💵", hora_pago,
                         f"{f['cliente']} pagó su deuda",
                         "", "", "", "",
                         f"Q{f['total']:.2f}"])
            filas_pagos.append(fila_idx)
            total_pagos_fiados += f["total"]
            fila_idx += 1

        total_ingreso = total_dia + total_pagos_fiados
        data.append(["", "", "", "", "", "", "TOTAL VENTAS DEL DÍA",
                     f"Q{total_ingreso:.2f}"])

        tabla = Table(data,
                      colWidths=[0.6 * cm, 1.1 * cm, 5.8 * cm, 1.5 * cm, 1.6 * cm, 1.7 * cm, 1.8 * cm, 1.9 * cm],
                      repeatRows=1)

        estilo = [
            # Header
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ALIGN", (2, 0), (2, 0), "LEFT"),
            # Cuerpo
            ("FONTSIZE", (0, 1), (-1, -2), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 1), (1, -2), "CENTER"),
            ("ALIGN", (3, 1), (6, -2), "CENTER"),
            ("ALIGN", (5, 1), (5, -2), "RIGHT"),
            ("ALIGN", (6, 1), (6, -2), "CENTER"),
            ("ALIGN", (7, 1), (7, -2), "RIGHT"),
            ("GRID", (0, 0), (-1, -2), 0.3, colors.HexColor("#e2e8f0")),
            # Total final
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0f4f8")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, -1), (-1, -1), 10),
            ("TEXTCOLOR", (0, -1), (-1, -1), NAVY),
            ("ALIGN", (6, -1), (6, -1), "RIGHT"),
            ("ALIGN", (7, -1), (7, -1), "RIGHT"),
            ("LINEABOVE", (0, -1), (-1, -1), 2, ORANGE),
            ("TOPPADDING", (0, -1), (-1, -1), 8),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
        ]

        # Estilos por tipo de fila
        for tipo, idx, tiene_desc in estilos_fila:
            if tipo == "cabecera":
                estilo.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#f0f4f8")))
                estilo.append(("FONTNAME", (0, idx), (-1, idx), "Helvetica-Bold"))
                estilo.append(("TEXTCOLOR", (0, idx), (-1, idx), NAVY))
                estilo.append(("TEXTCOLOR", (7, idx), (7, idx), ORANGE))
                estilo.append(("FONTSIZE", (0, idx), (-1, idx), 9))
                if tiene_desc:
                    estilo.append(("TEXTCOLOR", (5, idx), (5, idx), colors.HexColor("#dc2626")))  # ← col 5 = Descuento
                    estilo.append(("FONTNAME", (5, idx), (5, idx), "Helvetica-Bold"))
            elif tipo == "item_descuento":
                estilo.append(("TEXTCOLOR", (5, idx), (5, idx), colors.HexColor("#dc2626")))  # ← col 5 = Descuento
                estilo.append(("FONTNAME", (5, idx), (5, idx), "Helvetica-Bold"))

        # Filas de pagos de fiados (verde)
        for idx in filas_pagos:
            estilo.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#ecfdf5")))
            estilo.append(("FONTNAME", (0, idx), (-1, idx), "Helvetica-Bold"))
            estilo.append(("TEXTCOLOR", (0, idx), (-1, idx), colors.HexColor("#166534")))
            estilo.append(("TEXTCOLOR", (7, idx), (7, idx), colors.HexColor("#15803d")))
            estilo.append(("FONTSIZE", (0, idx), (-1, idx), 9))
            estilo.append(("ALIGN", (2, idx), (2, idx), "LEFT"))

        tabla.setStyle(TableStyle(estilo))
        elements.append(tabla)

    elements.append(Spacer(1, 0.5*cm))

    # ── Ventas anuladas (solo referencia, NO afecta el total) ──────────────────
    if anuladas:
        elements.append(HRFlowable(width="100%", thickness=0.5,
                                    color=colors.HexColor("#e2e8f0"), spaceAfter=8))
        elements.append(Paragraph("Ventas anuladas (solo referencia)", bold))
        elements.append(Paragraph(
            "Estas ventas fueron anuladas y NO se cuentan en el total del día.",
            ParagraphStyle("nota_anul", fontSize=8,
                            textColor=colors.HexColor("#9ca3af"))))
        elements.append(Spacer(1, 0.15*cm))

        prod_anul_style = ParagraphStyle("prod_anul", fontSize=8, leading=9.5,
                                          fontName="Helvetica",
                                          textColor=colors.HexColor("#6b7280"))

        data_an = [["#", "Hora", "Producto", "Cant", "Precio", "Descuento", "Subtotal", "Total"]]
        for i, v in enumerate(anuladas, 1):
            hora = v["fecha"][11:16]
            items = v.get("items", [])
            if items:
                it0 = items[0]
                d0 = it0.get("descuento", 0.0) or 0.0
                data_an.append([str(i), hora,
                                Paragraph(it0["producto"], prod_anul_style),
                                str(it0["cantidad"]),
                                f"Q{it0['precio']:.2f}",
                                f"-Q{d0:.2f}" if d0 > 0 else "—",
                                f"Q{max(0.0, it0['subtotal'] - d0):.2f}",
                                f"Q{v['total']:.2f}"])
                for it in items[1:]:
                    d = it.get("descuento", 0.0) or 0.0
                    data_an.append(["", "",
                                    Paragraph(it["producto"], prod_anul_style),
                                    str(it["cantidad"]),
                                    f"Q{it['precio']:.2f}",
                                    f"-Q{d:.2f}" if d > 0 else "—",
                                    f"Q{max(0.0, it['subtotal'] - d):.2f}",
                                    ""])
            else:
                data_an.append([str(i), hora,
                                Paragraph("(sin detalle)", prod_anul_style),
                                "", "", "", "", f"Q{v['total']:.2f}"])

        tabla_an = Table(data_an,
            colWidths=[0.6*cm, 1.2*cm, 5.0*cm, 1.0*cm, 1.6*cm, 1.8*cm, 1.8*cm, 1.8*cm],
            repeatRows=1)
        tabla_an.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,0), colors.HexColor("#9ca3af")),
            ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
            ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,0), 8),
            ("ALIGN",        (0,0), (-1,0), "CENTER"),
            ("ALIGN",        (2,0), (2,0), "LEFT"),
            ("FONTSIZE",     (0,1), (-1,-1), 8),
            ("TEXTCOLOR",    (0,1), (-1,-1), colors.HexColor("#6b7280")),
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN",        (0,1), (1,-1), "CENTER"),
            ("ALIGN",        (3,1), (7,-1), "CENTER"),
            ("GRID",         (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, colors.HexColor("#f9fafb")]),
            ("TOPPADDING",   (0,1), (-1,-1), 4),
            ("BOTTOMPADDING",(0,1), (-1,-1), 4),
        ]))
        elements.append(tabla_an)
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

        # Estilos que se ajustan en varias líneas si el texto es largo
        cliente_style = ParagraphStyle("cliente_fi", fontSize=8, leading=9.5,
                                        fontName="Helvetica-Bold", textColor=NAVY)
        prod_style_bold = ParagraphStyle("prod_fi_b", fontSize=8, leading=9.5,
                                          fontName="Helvetica-Bold", textColor=NAVY)
        prod_style = ParagraphStyle("prod_fi", fontSize=8, leading=9.5,
                                     fontName="Helvetica", textColor=colors.HexColor("#374151"))

        for f in fiados:
            hora   = f["fecha"][11:16]
            estado = "Pagado" if f["estado"] == "pagado" else "Pendiente"
            items  = f.get("items", [])

            cliente_p = Paragraph(f["cliente"], cliente_style)

            if items:
                # Primer producto en la MISMA fila que el cliente
                it0 = items[0]
                data_fi.append([hora, cliente_p,
                                Paragraph(it0["producto"], prod_style_bold),
                                str(it0["cantidad"]),
                                f"Q{it0['precio']:.2f}",
                                f"Q{it0['subtotal']:.2f}",
                                estado, f"Q{f['total']:.2f}"])
                cabeceras_fi.append((fila_idx, f["estado"]))
                fila_idx += 1

                # Productos restantes en filas siguientes
                for it in items[1:]:
                    data_fi.append(["", "",
                                    Paragraph(it["producto"], prod_style),
                                    str(it["cantidad"]),
                                    f"Q{it['precio']:.2f}",
                                    f"Q{it['subtotal']:.2f}",
                                    "", ""])
                    fila_idx += 1
            else:
                data_fi.append([hora, cliente_p, "", "", "", "", estado, f"Q{f['total']:.2f}"])
                cabeceras_fi.append((fila_idx, f["estado"]))
                fila_idx += 1

            total_fiados += f["total"]

        data_fi.append(["", "", "", "", "", "", "TOTAL FIADOS", f"Q{total_fiados:.2f}"])

        tabla_fi = Table(data_fi,
            colWidths=[1.1*cm, 3.6*cm, 3.3*cm, 0.9*cm, 1.7*cm, 1.8*cm, 2.0*cm, 1.8*cm],
            repeatRows=1)

        estilo_fi = [
            ("BACKGROUND",    (0,0), (-1,0), NAVY),
            ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,0), 8.5),
            ("ALIGN",         (0,0), (-1,0), "CENTER"),
            ("ALIGN",         (2,0), (2,0), "LEFT"),
            ("FONTSIZE",      (0,1), (-1,-2), 8),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN",         (0,1), (0,-2), "CENTER"),
            ("ALIGN",         (1,1), (1,-2), "LEFT"),
            ("ALIGN",         (3,1), (7,-2), "CENTER"),
            ("ALIGN",         (5,1), (5,-2), "RIGHT"),
            ("ALIGN",         (7,1), (7,-2), "RIGHT"),
            ("GRID",          (0,0), (-1,-2), 0.3, colors.HexColor("#e2e8f0")),
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

        for idx, estado in cabeceras_fi:
            estilo_fi.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#f0f4f8")))
            estilo_fi.append(("FONTNAME",   (0, idx), (-1, idx), "Helvetica-Bold"))
            estilo_fi.append(("TEXTCOLOR",  (0, idx), (-1, idx), NAVY))
            estilo_fi.append(("TEXTCOLOR",  (7, idx), (7, idx), ORANGE))
            estilo_fi.append(("FONTSIZE",   (0, idx), (-1, idx), 9))
            color_estado = colors.HexColor("#16a34a") if estado == "pagado" else colors.HexColor("#b45309")
            estilo_fi.append(("TEXTCOLOR",  (6, idx), (6, idx), color_estado))

        tabla_fi.setStyle(TableStyle(estilo_fi))
        elements.append(tabla_fi)

    # ── Resumen final ─────────────────────────────────────────────────────────
    elements.append(Spacer(1, 0.5*cm))

    total_fiados_pendientes = sum(
        f["total"] for f in fiados if f["estado"] == "pendiente"
    )

    ingresos = total_dia + total_pagos_fiados
    neto     = ingresos - total_gastos

    resumen_data = [
        ["Total ventas (bruto)",  f"+Q{total_dia + total_descuentos:.2f}"],
        ["Descuentos aplicados",  f"-Q{total_descuentos:.2f}"],
        ["Pagos de fiados hoy",   f"+Q{total_pagos_fiados:.2f}"],
        ["Ingreso total",         f"Q{ingresos:.2f}"],
        ["Total gastos",          f"-Q{total_gastos:.2f}"],
        ["Fiados pendientes hoy", f"Q{total_fiados_pendientes:.2f}"],
        ["NETO DEL DÍA",          f"Q{neto:.2f}"],
    ]

    resumen = Table(resumen_data, colWidths=[10*cm, 5*cm])
    resumen.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",  (0,0), (-1,-2), 10),
        ("ALIGN",     (1,0), (1,-1), "RIGHT"),
        ("TEXTCOLOR", (0,0), (-1,-2), colors.HexColor("#374151")),
        ("TOPPADDING",    (0,0), (-1,-2), 3),
        ("BOTTOMPADDING", (0,0), (-1,-2), 3),
        # Ventas bruto (verde)
        ("TEXTCOLOR", (1,0), (1,0), colors.HexColor("#15803d")),
        # Descuentos (rojo)
        ("TEXTCOLOR", (1,1), (1,1), colors.HexColor("#dc2626")),
        # Pagos fiados (verde)
        ("TEXTCOLOR", (1,2), (1,2), colors.HexColor("#15803d")),
        # Ingreso total (bold navy)
        ("FONTNAME",  (0,3), (-1,3), "Helvetica-Bold"),
        ("TEXTCOLOR", (0,3), (-1,3), NAVY),
        ("LINEABOVE", (0,3), (-1,3), 0.5, colors.HexColor("#e2e8f0")),
        # Gastos (rojo)
        ("TEXTCOLOR", (1,4), (1,4), colors.HexColor("#b91c1c")),
        # Fiados pendientes (naranja)
        ("TEXTCOLOR", (0,5), (-1,5), colors.HexColor("#b45309")),
        ("FONTSIZE",  (0,5), (-1,5), 9),
        # NETO DEL DÍA
        ("BACKGROUND",(0,-1), (-1,-1), NAVY),
        ("TEXTCOLOR", (0,-1), (-1,-1), colors.white),
        ("FONTNAME",  (0,-1), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,-1), (-1,-1), 13),
        ("TOPPADDING",    (0,-1), (-1,-1), 8),
        ("BOTTOMPADDING", (0,-1), (-1,-1), 8),
    ]))
    elements.append(resumen)

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


# ── Enviar por WhatsApp ───────────────────────────────────────────────────────
def enviar_reporte_whatsapp(ruta_pdf, numero=WA_NUMERO):
    try:
        fecha = datetime.now().strftime("%d/%m/%Y")
        caption = (f"📊 Reporte Soluciones Plus\n"
                   f"📅 {fecha}\n\n"
                   f"Reporte del día adjunto.")

        with open(ruta_pdf, "rb") as f:
            files = {"file": (os.path.basename(ruta_pdf), f, "application/pdf")}
            data  = {"number": numero, "caption": caption}
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


# ── Factura con 2 copias en una hoja ─────────────────────────────────────────
def _total_en_letras(total: float) -> str:
    entero = int(total)
    centavos = round((total - entero) * 100)
    texto = num2words(entero, lang="es").capitalize()
    if centavos:
        texto += f" con {centavos:02d}/100"
    return texto + " quetzales exactos"


def _dibujar_copia(c, x0, y0, ancho, alto, numero, fecha_str, items,
                   total, cliente_info, logo_path):
    """Dibuja UNA copia de la factura en el canvas en la posición (x0, y0)."""
    NAVY_RGB   = (0.051, 0.169, 0.333)
    ORANGE_RGB = (0.976, 0.451, 0.086)
    WHITE      = (1, 1, 1)
    GRAY_BG    = (0.941, 0.957, 0.973)

    margen = 0.4 * cm

    # ── Borde exterior ────────────────────────────────────────────────────────
    c.setStrokeColorRGB(*NAVY_RGB)
    c.setLineWidth(1)
    c.rect(x0, y0, ancho, alto)

    # ── Cabecera ──────────────────────────────────────────────────────────────
    cab_h = 2.2 * cm
    cab_y = y0 + alto - cab_h

    # fondo azul cabecera (columna central)
    col_logo_w  = 2.5 * cm
    col_fecha_w = 3.2 * cm
    col_tit_w   = ancho - col_logo_w - col_fecha_w

    # columna logo
    c.setFillColorRGB(*GRAY_BG)
    c.rect(x0, cab_y, col_logo_w, cab_h, fill=1, stroke=0)

    # columna título
    c.setFillColorRGB(*NAVY_RGB)
    c.rect(x0 + col_logo_w, cab_y, col_tit_w, cab_h, fill=1, stroke=0)

    # columna fecha/número
    c.setFillColorRGB(*GRAY_BG)
    c.rect(x0 + col_logo_w + col_tit_w, cab_y, col_fecha_w, cab_h, fill=1, stroke=0)

    # Logo (si existe)
    if logo_path and os.path.exists(logo_path):
        try:
            c.drawImage(logo_path,
                        x0 + 0.15 * cm, cab_y + 0.15 * cm,
                        width=col_logo_w - 0.3 * cm,
                        height=cab_h - 0.3 * cm,
                        preserveAspectRatio=True, mask="auto")
        except Exception:
            pass

    # Título empresa
    c.setFillColorRGB(*WHITE)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(x0 + col_logo_w + col_tit_w / 2,
                        cab_y + cab_h * 0.62,
                        "Soluciones Plus")
    c.setFont("Helvetica", 8)
    c.drawCentredString(x0 + col_logo_w + col_tit_w / 2,
                        cab_y + cab_h * 0.38,
                        "Cantón Yawa', San Mateo Ixtatán,")
    c.drawCentredString(x0 + col_logo_w + col_tit_w / 2,
                        cab_y + cab_h * 0.18,
                        "Huehutenango")

    # Fecha y número
    fecha_dt = datetime.strptime(fecha_str[:10], "%Y-%m-%d")
    fecha_fmt = fecha_dt.strftime("%d/%m/%Y")
    fecha_x = x0 + col_logo_w + col_tit_w + margen
    c.setFillColorRGB(*NAVY_RGB)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(fecha_x, cab_y + cab_h * 0.68, "Fecha:")
    c.drawString(fecha_x, cab_y + cab_h * 0.38, "Número:")
    c.setFont("Helvetica", 7.5)
    c.drawString(fecha_x + 1.3 * cm, cab_y + cab_h * 0.68, fecha_fmt)
    c.setFillColorRGB(*NAVY_RGB)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(fecha_x + 1.3 * cm, cab_y + cab_h * 0.38, f"SP {numero}")

    # ── Datos cliente ─────────────────────────────────────────────────────────
    cli_h = 1.6 * cm
    cli_y = cab_y - cli_h
    c.setFillColorRGB(*WHITE)
    c.rect(x0, cli_y, ancho, cli_h, fill=1, stroke=0)
    c.setStrokeColorRGB(*NAVY_RGB)
    c.setLineWidth(0.3)
    c.rect(x0, cli_y, ancho, cli_h)

    lx  = x0 + margen
    lx2 = x0 + ancho * 0.55
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColorRGB(*NAVY_RGB)

    c.drawString(lx,  cli_y + cli_h * 0.76, "Cliente:")
    c.drawString(lx,  cli_y + cli_h * 0.44, "Dirección :")
    c.drawString(lx,  cli_y + cli_h * 0.13, "E-mail:")
    c.drawString(lx2, cli_y + cli_h * 0.13, "Nit:")

    c.setFont("Helvetica", 7.5)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(lx  + 1.3 * cm, cli_y + cli_h * 0.76,
                 cliente_info.get("nombre", ""))
    c.drawString(lx  + 1.7 * cm, cli_y + cli_h * 0.44,
                 cliente_info.get("direccion", ""))
    c.drawString(lx  + 1.2 * cm, cli_y + cli_h * 0.13,
                 cliente_info.get("email", "N/D"))

    nit_val = cliente_info.get("nit", "C/F")
    tel_val = cliente_info.get("telefono", "")
    c.drawString(lx2 + 0.6 * cm, cli_y + cli_h * 0.13, nit_val)

    if tel_val:
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColorRGB(*NAVY_RGB)
        c.drawString(lx2 + 2 * cm, cli_y + cli_h * 0.13, "Teléfono:")
        c.setFont("Helvetica", 7.5)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(lx2 + 3.3 * cm, cli_y + cli_h * 0.13, tel_val)

    # ── Cabecera tabla ────────────────────────────────────────────────────────
    th = 0.55 * cm
    ty = cli_y - th
    cols = [1.2 * cm,
            ancho - 1.2*cm - 2.4*cm - 1.6*cm - 2.0*cm,
            2.4 * cm,
            1.6 * cm,
            2.0 * cm]
    cx = [x0]
    for w in cols:
        cx.append(cx[-1] + w)

    c.setFillColorRGB(*NAVY_RGB)
    c.rect(x0, ty, ancho, th, fill=1, stroke=0)
    c.setFillColorRGB(*WHITE)
    c.setFont("Helvetica-Bold", 7)
    headers = ["Cantidad", "Descripción", "P. Unitario", "Descuento", "Totales"]
    aligns  = ["center", "center", "center", "center", "center"]
    for i, (hdr, align) in enumerate(zip(headers, aligns)):
        col_cx = cx[i]
        col_w  = cols[i]
        if align == "center":
            c.drawCentredString(col_cx + col_w / 2, ty + th * 0.3, hdr)
        else:
            c.drawString(col_cx + 4, ty + th * 0.3, hdr)

    # ── Filas de items ────────────────────────────────────────────────────────
    fila_h  = 0.48 * cm
    pie_h   = 0.65 * cm
    # Calcular cuántas filas caben para que el pie quede pegado al fondo del recuadro
    espacio_filas = (ty - y0 - pie_h)
    max_fil = max(len(items), int(espacio_filas / fila_h))
    fy      = ty

    for i in range(max_fil):
        fy -= fila_h
        bg = WHITE if i % 2 == 0 else (0.973, 0.980, 0.988)
        c.setFillColorRGB(*bg)
        c.rect(x0, fy, ancho, fila_h, fill=1, stroke=0)
        c.setStrokeColorRGB(0.886, 0.910, 0.941)
        c.setLineWidth(0.3)
        c.rect(x0, fy, ancho, fila_h)

        c.setFillColorRGB(*NAVY_RGB)
        c.setFont("Helvetica", 7)

        if i < len(items):
            it  = items[i]
            qty = str(it.get("cantidad", ""))
            desc_prod = str(it.get("prod", ""))
            pu  = f"Q  {it.get('precio_unit', 0):.2f}"
            dsc = it.get("descuento", 0) or 0
            dsc_txt = f"Q  {dsc:.2f}" if dsc else "Q  -"
            sub = max(0.0, it.get("subtotal", 0) - dsc)
            tot = f"Q  {sub:.2f}"

            c.setFillColorRGB(0, 0, 0)
            c.drawCentredString(cx[0] + cols[0] / 2, fy + fila_h * 0.28, qty)
            c.setFillColorRGB(*NAVY_RGB)
            if desc_prod:
                # Ajustar la descripción al ancho real de la columna
                ancho_desc = cols[1] - 0.2 * cm
                fs = 7
                while fs >= 5 and c.stringWidth(desc_prod, "Helvetica", fs) > ancho_desc:
                    fs -= 0.5
                # Si aún no cabe con fuente mínima, recortar con "…"
                texto = desc_prod
                if c.stringWidth(texto, "Helvetica", fs) > ancho_desc:
                    while texto and c.stringWidth(texto + "…", "Helvetica", fs) > ancho_desc:
                        texto = texto[:-1]
                    texto += "…"
                c.setFont("Helvetica", fs)
                c.drawString(cx[1] + 3, fy + fila_h * 0.28, texto)
                c.setFont("Helvetica", 7)
            for j, val in enumerate([pu, dsc_txt, tot], start=2):
                c.drawCentredString(cx[j] + cols[j] / 2, fy + fila_h * 0.28, val)
        # Las filas vacías quedan en blanco (sin "Q -")

    # ── Pie: total en letras + total ─────────────────────────────────────────
    pie_y = fy - pie_h
    c.setFillColorRGB(*NAVY_RGB)
    c.rect(x0, pie_y, ancho, pie_h, fill=1, stroke=0)

    letras = _total_en_letras(total)
    c.setFillColorRGB(*WHITE)
    c.setFont("Helvetica-BoldOblique", 7)
    c.drawString(x0 + margen, pie_y + pie_h * 0.35, letras)

    # columna TOTAL (última columna, dentro del recuadro)
    tot_col_w = cols[-1]
    tot_col_x = cx[-2]
    c.setFillColorRGB(*ORANGE_RGB)
    c.rect(tot_col_x, pie_y, tot_col_w, pie_h, fill=1, stroke=0)

    # Etiqueta "TOTAL" justo a la izquierda de la caja naranja
    c.setFillColorRGB(*WHITE)
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(tot_col_x - 0.2 * cm, pie_y + pie_h * 0.32, "TOTAL")

    # Monto centrado en la caja naranja
    c.drawCentredString(tot_col_x + tot_col_w / 2,
                        pie_y + pie_h * 0.32,
                        f"Q {total:.2f}")


def generar_factura(venta_id, items, total, fecha_str, cliente_info, logo_path=None):
    """
    Genera un PDF con 2 copias de la factura en una hoja carta.
    Retorna la ruta del archivo generado.
    """
    carpeta = os.path.join(os.path.expanduser("~"), "Documents",
                           "SISTEMA_SP", "Facturas")
    os.makedirs(carpeta, exist_ok=True)

    # Nombre del archivo con el nombre del cliente (limpio para Windows)
    cliente_nombre = (cliente_info.get("nombre") or "Cliente").strip()
    cliente_limpio = "".join(ch for ch in cliente_nombre
                             if ch.isalnum() or ch in " _-").strip()
    cliente_limpio = cliente_limpio.replace(" ", "_") or "Cliente"

    hora = datetime.now().strftime("%H%M%S")
    nombre = f"SP{venta_id}_{cliente_limpio}_{hora}.pdf"
    ruta   = os.path.normpath(os.path.join(carpeta, nombre))

    pw, ph = letter          # 21.59 cm × 27.94 cm
    margen_hoja = 0.8 * cm

    c = rl_canvas.Canvas(ruta, pagesize=letter)

    # Cada copia ocupa la mitad de la hoja menos márgenes
    alto_copia = (ph - 3 * margen_hoja) / 2
    ancho_copia = pw - 2 * margen_hoja

    # Copia superior (cliente)
    _dibujar_copia(c,
                   x0=margen_hoja,
                   y0=margen_hoja + alto_copia + margen_hoja,
                   ancho=ancho_copia,
                   alto=alto_copia,
                   numero=venta_id,
                   fecha_str=fecha_str,
                   items=items,
                   total=total,
                   cliente_info=cliente_info,
                   logo_path=logo_path)

    # Línea punteada de corte
    linea_y = margen_hoja + alto_copia + margen_hoja / 2
    c.setDash(4, 4)
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.setLineWidth(0.6)
    c.line(margen_hoja, linea_y, pw - margen_hoja, linea_y)
    c.setDash()

    # Etiqueta de corte
    c.setFont("Helvetica", 6)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawCentredString(pw / 2, linea_y + 2, "✂  Cortar aquí  ✂")

    # Copia inferior (negocio)
    _dibujar_copia(c,
                   x0=margen_hoja,
                   y0=margen_hoja,
                   ancho=ancho_copia,
                   alto=alto_copia,
                   numero=venta_id,
                   fecha_str=fecha_str,
                   items=items,
                   total=total,
                   cliente_info=cliente_info,
                   logo_path=logo_path)

    c.save()
    return ruta