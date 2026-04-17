from bot.services.google_sheets_service import (
    verificar_conexion_google,
    sync_tickets_to_sheet,
    export_sheet_as_xlsx,
)

info = verificar_conexion_google()
print("Spreadsheet:", info["spreadsheet_title"])
print("Pestañas:", info["sheet_titles"])

sync_tickets_to_sheet()
print("Sincronización OK")

archivo = export_sheet_as_xlsx()
print("Exportación OK, bytes:", len(archivo.getvalue()))