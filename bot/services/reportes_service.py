import smtplib
from datetime import datetime
from email.message import EmailMessage
from io import BytesIO

import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from bot.config import DESTINATARIO, EMAIL_PASS, REMITENTE

SHEET_NAME = "Reporte"
REPORT_TITLE = "Reporte De Tickets"
HEADER_ROW = 3
DATA_START_ROW = 4

STATUS_COLORS = {
    "Abierto": "C6EFCE",
    "Cerrado": "FFC7CE",
    "En Proceso": "FFD966",
}

COLUMN_WIDTHS = {
    "A": 7,
    "B": 12,
    "C": 12,
    "D": 40,
    "E": 10,
    "F": 20,
    "G": 12,
    "H": 40,
    "I": 20,
}


def generar_excel(tickets):
    df = ordenar_dataframe(construir_dataframe(tickets))
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=SHEET_NAME, startrow=2)

        ws = writer.sheets[SHEET_NAME]
        ws["A1"] = REPORT_TITLE
        ws["A2"] = f"Fecha de Reporte: {datetime.now().strftime('%d-%m-%Y (%H:%M:%S)')}"
        ws["A1"].font = Font(size=14, bold=True)

        aplicar_estilos_reporte(ws)

    output.seek(0)
    return output


def construir_dataframe(tickets):
    data = []

    for ticket in tickets:
        data.append(
            {
                "ID": ticket.id,
                "Usuario": ticket.usuario,
                "Área": ticket.area,
                "Descripción": ticket.descripcion,
                "Estado": ticket.estado,
                "Fecha Creacion": _formatear_fecha(ticket.fecha_creacion),
                "TI Asignado": ticket.asignado_a or "Sin asignar",
                "Observacion TI": ticket.observacion or "Sin observaciones",
                "Fecha Actualiz.": _formatear_fecha(ticket.fecha_actualizacion),
            }
        )

    return pd.DataFrame(data)


def ordenar_dataframe(df):
    return df.sort_values(by="ID", ascending=False)


def aplicar_estilos_reporte(ws):
    aplicar_estilos_generales(ws)
    aplicar_estilo_headers(ws)
    auto_ajustar_columnas(ws)
    aplicar_filtros(ws)
    congelar_encabezado(ws)
    aplicar_colores_estado(ws)
    resaltar_nulos(ws)
    ajustar_columnas_especiales(ws)
    aplicar_bordes(ws)


def aplicar_estilos_generales(ws):
    for row in ws.iter_rows(min_row=DATA_START_ROW):
        for cell in row:
            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
                wrap_text=True,
            )

    for col in ["D", "I"]:
        for cell in ws[col]:
            cell.alignment = Alignment(
                horizontal="left",
                vertical="center",
                wrap_text=True,
            )


def aplicar_estilo_headers(ws):
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", fill_type="solid")

    for cell in ws[HEADER_ROW]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    ws.row_dimensions[HEADER_ROW].height = 20


def auto_ajustar_columnas(ws):
    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter

        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))

        ws.column_dimensions[col_letter].width = max_length + 2


def aplicar_filtros(ws):
    ws.auto_filter.ref = f"A{HEADER_ROW}:I{ws.max_row}"


def congelar_encabezado(ws):
    ws.freeze_panes = "A4"


def aplicar_colores_estado(ws):
    for row in ws.iter_rows(min_row=DATA_START_ROW):
        estado = row[4].value
        color = STATUS_COLORS.get(estado)

        if not color:
            continue

        fill = PatternFill(start_color=color, fill_type="solid")

        for cell in row:
            cell.fill = fill


def resaltar_nulos(ws):
    null_fill = PatternFill(start_color="EEECE1", fill_type="solid")

    for cell in ws["G"]:
        if cell.value == "Sin asignar":
            cell.fill = null_fill

    for cell in ws["H"]:
        if cell.value == "Sin observaciones":
            cell.fill = null_fill


def ajustar_columnas_especiales(ws):
    for col, width in COLUMN_WIDTHS.items():
        ws.column_dimensions[col].width = width


def aplicar_bordes(ws):
    thin = Side(style="thin", color="000000")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for row in ws.iter_rows(min_row=HEADER_ROW):
        for cell in row:
            cell.border = border


def enviar_report_correo(archivo_bytes, nombre_archivo):
    msg = EmailMessage()
    msg["Subject"] = f"Reporte Generado: {nombre_archivo}"
    msg["From"] = f"TI-BOT SOPORTE (No-Reply) <{REMITENTE}>"
    msg["To"] = DESTINATARIO
    msg.set_content(
        "Adjunto encontraras el reporte solicitado desde el Bot de Telegram TI-BOT."
    )

    payload = (
        archivo_bytes.getvalue()
        if hasattr(archivo_bytes, "getvalue")
        else archivo_bytes
    )

    msg.add_attachment(
        payload,
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=nombre_archivo,
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(REMITENTE, EMAIL_PASS)
        smtp.send_message(msg)


def _formatear_fecha(fecha):
    return fecha.strftime("%d-%m-%Y %H:%M:%S") if fecha else ""