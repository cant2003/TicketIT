from io import BytesIO

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from bot.config import (
    GOOGLE_SERVICE_ACCOUNT_FILE,
    GOOGLE_SPREADSHEET_ID,
    GOOGLE_SHEET_NAME,
)
from bot.services import reportes_service as rs

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


def _normalizar_valor(valor):
    return "" if valor is None else str(valor)


def sync_tickets_to_sheet():
    """
    Sincroniza TODOS los tickets desde SQLite hacia Google Sheets.
    La BD sigue siendo la fuente real.
    """
    if not GOOGLE_SPREADSHEET_ID:
        raise ValueError("Falta GOOGLE_SPREADSHEET_ID en .env")

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

    sheets = _get_sheets_service()

    # Limpia solo valores; conserva formato si luego lo agregas en la hoja.
    sheets.spreadsheets().values().clear(
        spreadsheetId=GOOGLE_SPREADSHEET_ID,
        range=f"{GOOGLE_SHEET_NAME}!A:Z",
        body={},
    ).execute()

    sheets.spreadsheets().values().update(
        spreadsheetId=GOOGLE_SPREADSHEET_ID,
        range=f"{GOOGLE_SHEET_NAME}!A1",
        valueInputOption="RAW",
        body={"values": values},
    ).execute()


def export_sheet_as_xlsx():
    """
    Exporta el Google Sheet a XLSX y lo devuelve en memoria.
    """
    if not GOOGLE_SPREADSHEET_ID:
        raise ValueError("Falta GOOGLE_SPREADSHEET_ID en .env")

    drive = _get_drive_service()

    contenido = drive.files().export(
        fileId=GOOGLE_SPREADSHEET_ID,
        mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ).execute()

    output = BytesIO(contenido)
    output.seek(0)
    return output


def verificar_conexion_google():
    """
    Prueba simple para validar credenciales y acceso a la hoja.
    """
    sheets = _get_sheets_service()
    respuesta = sheets.spreadsheets().get(
        spreadsheetId=GOOGLE_SPREADSHEET_ID
    ).execute()
    return respuesta.get("properties", {}).get("title", "Sin título")