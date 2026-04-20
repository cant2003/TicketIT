from io import BytesIO

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from bot.config import (
    GOOGLE_SERVICE_ACCOUNT_FILE,
    GOOGLE_SPREADSHEET_ID,
    GOOGLE_SHEET_NAME,
)
from bot.services import reportes_service as rs

from bot.services.row_map_service import obtener_fila_ticket, guardar_fila_ticket

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _get_credentials():
    if not GOOGLE_SERVICE_ACCOUNT_FILE:
        raise ValueError("Falta GOOGLE_SERVICE_ACCOUNT_FILE en .env")

    return Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )


def _get_sheets_service():
    creds = _get_credentials()
    return build("sheets", "v4", credentials=creds)


def _get_drive_service():
    creds = _get_credentials()
    return build("drive", "v3", credentials=creds)


def _resolver_sheet_name():
    sheets = _get_sheets_service()
    respuesta = sheets.spreadsheets().get(
        spreadsheetId=GOOGLE_SPREADSHEET_ID
    ).execute()

    pestañas = respuesta.get("sheets", [])
    titulos = [
        s.get("properties", {}).get("title", "")
        for s in pestañas
    ]

    if GOOGLE_SHEET_NAME and GOOGLE_SHEET_NAME in titulos:
        return GOOGLE_SHEET_NAME

    if not titulos:
        raise ValueError("El spreadsheet no tiene pestañas disponibles")

    return titulos[0]


_cached_sheet_name = None

def _get_cached_sheet_name():
    global _cached_sheet_name

    if _cached_sheet_name:
        return _cached_sheet_name

    sheets = _get_sheets_service()
    respuesta = sheets.spreadsheets().get(
        spreadsheetId=GOOGLE_SPREADSHEET_ID
    ).execute()

    pestañas = respuesta.get("sheets", [])
    titulos = [
        s.get("properties", {}).get("title", "")
        for s in pestañas
    ]

    if GOOGLE_SHEET_NAME and GOOGLE_SHEET_NAME in titulos:
        _cached_sheet_name = GOOGLE_SHEET_NAME
    elif titulos:
        _cached_sheet_name = titulos[0]
    else:
        raise ValueError("El spreadsheet no tiene pestañas")

    return _cached_sheet_name


def _sheet_range(a1_range: str) -> str:
    sheet_name = _get_cached_sheet_name()
    safe_sheet_name = sheet_name.replace("'", "''")
    return f"'{safe_sheet_name}'!{a1_range}"


def _normalizar_valor(valor):
    return "" if valor is None else str(valor)


def _ticket_to_row(ticket):
    return [
        _normalizar_valor(ticket.id),
        _normalizar_valor(ticket.usuario),
        _normalizar_valor(ticket.area),
        _normalizar_valor(ticket.descripcion),
        _normalizar_valor(ticket.estado),
        _normalizar_valor(
            ticket.fecha_creacion.strftime("%d-%m-%Y %H:%M:%S")
            if ticket.fecha_creacion else ""
        ),
        _normalizar_valor(ticket.asignado_a or "Sin asignar"),
        _normalizar_valor(ticket.observacion or "Sin observaciones"),
        _normalizar_valor(
            ticket.fecha_actualizacion.strftime("%d-%m-%Y %H:%M:%S")
            if ticket.fecha_actualizacion else ""
        ),
    ]


def _headers():
    return [
        "ID",
        "Usuario",
        "Area",
        "Descripcion",
        "Estado",
        "Fecha Creacion",
        "TI Asignado",
        "Observacion TI",
        "Fecha Actualiz.",
    ]


def inicializar_sheet_si_esta_vacia():
    """
    Crea título, timestamp y headers si la hoja está vacía.
    No toca filas existentes.
    """
    sheets = _get_sheets_service()

    lectura = sheets.spreadsheets().values().get(
        spreadsheetId=GOOGLE_SPREADSHEET_ID,
        range=_sheet_range("A1:I3"),
    ).execute()

    values = lectura.get("values", [])

    if values:
        return

    payload = [
        ["Reporte de Tickets"],
        [f"Última sincronización: {rs.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"],
        _headers(),
    ]

    sheets.spreadsheets().values().update(
        spreadsheetId=GOOGLE_SPREADSHEET_ID,
        range=_sheet_range("A1"),
        valueInputOption="RAW",
        body={"values": payload},
    ).execute()


def actualizar_timestamp_sheet():
    sheets = _get_sheets_service()

    sheets.spreadsheets().values().update(
        spreadsheetId=GOOGLE_SPREADSHEET_ID,
        range=_sheet_range("A2"),
        valueInputOption="RAW",
        body={
            "values": [[
                f"Última sincronización: {rs.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
            ]]
        },
    ).execute()


def buscar_fila_por_ticket_id(ticket_id):
    """
    Busca el ticket por ID en la columna A, desde la fila 4 hacia abajo.
    Devuelve el número de fila real de Google Sheets o None.
    """
    sheets = _get_sheets_service()

    lectura = sheets.spreadsheets().values().get(
        spreadsheetId=GOOGLE_SPREADSHEET_ID,
        range=_sheet_range("A4:A"),
    ).execute()

    values = lectura.get("values", [])

    ticket_id = str(ticket_id).strip()

    for index, row in enumerate(values, start=4):
        if row and str(row[0]).strip() == ticket_id:
            return index

    return None


def upsert_ticket_en_sheet(ticket):
    """
    Si el ticket ya tiene fila registrada localmente, actualiza directo.
    Si no, lo agrega al final y guarda su fila.
    """
    inicializar_sheet_si_esta_vacia()

    sheets = _get_sheets_service()
    fila = _ticket_to_row(ticket)

    fila_existente = obtener_fila_ticket(ticket.id)

    if fila_existente:
        try:
            sheets.spreadsheets().values().update(
                spreadsheetId=GOOGLE_SPREADSHEET_ID,
                range=_sheet_range(f"A{fila_existente}:I{fila_existente}"),
                valueInputOption="RAW",
                body={"values": [fila]},
            ).execute()
        except Exception:
        # fallback: volver a insertar si la fila ya no existe
            respuesta = sheets.spreadsheets().values().append(
                spreadsheetId=GOOGLE_SPREADSHEET_ID,
                range=_sheet_range("A4:I"),
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": [fila]},
            ).execute()

            updated_range = respuesta.get("updates", {}).get("updatedRange", "")
            if "!" in updated_range:
                rango_sin_hoja = updated_range.split("!")[1]
                fila_inicio = rango_sin_hoja.split(":")[0]
                numero_fila = int("".join(filter(str.isdigit, fila_inicio)))
                guardar_fila_ticket(ticket.id, numero_fila)
    else:
        respuesta = sheets.spreadsheets().values().append(
            spreadsheetId=GOOGLE_SPREADSHEET_ID,
            range=_sheet_range("A4:I"),
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [fila]},
        ).execute()

        updated_range = respuesta.get("updates", {}).get("updatedRange", "")
        # ejemplo: "'Tickets'!A7:I7"
        if "!" in updated_range:
            rango_sin_hoja = updated_range.split("!")[1]
            fila_inicio = rango_sin_hoja.split(":")[0]
            numero_fila = int("".join(filter(str.isdigit, fila_inicio)))
            guardar_fila_ticket(ticket.id, numero_fila)

    actualizar_timestamp_sheet()

def sync_tickets_to_sheet():
    """
    Reconstrucción completa.
    Déjala solo para mantenimiento/manual.
    """
    sheets = _get_sheets_service()
    tickets = rs.tickets_todos()
    df = rs.construir_dataframe(tickets)
    df = rs.ordenar_dataframe(df)

    headers = list(df.columns)
    rows = []
    for _, row in df.iterrows():
        rows.append([_normalizar_valor(v) for v in row.tolist()])

    values = [
        ["Reporte de Tickets"],
        [f"Última sincronización: {rs.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"],
        headers,
        *rows,
    ]

    sheets.spreadsheets().values().clear(
        spreadsheetId=GOOGLE_SPREADSHEET_ID,
        range=_sheet_range("A:I"),
        body={},
    ).execute()

    sheets.spreadsheets().values().update(
        spreadsheetId=GOOGLE_SPREADSHEET_ID,
        range=_sheet_range("A1"),
        valueInputOption="RAW",
        body={"values": values},
    ).execute()


def export_sheet_as_xlsx():
    drive = _get_drive_service()

    contenido = drive.files().export(
        fileId=GOOGLE_SPREADSHEET_ID,
        mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ).execute()

    output = BytesIO(contenido)
    output.seek(0)
    return output


def verificar_conexion_google():
    sheets = _get_sheets_service()
    respuesta = sheets.spreadsheets().get(
        spreadsheetId=GOOGLE_SPREADSHEET_ID
    ).execute()

    titulo = respuesta.get("properties", {}).get("title", "Sin título")
    pestañas = [
        s.get("properties", {}).get("title", "Sin nombre")
        for s in respuesta.get("sheets", [])
    ]

    return {
        "spreadsheet_title": titulo,
        "sheet_titles": pestañas,
    }