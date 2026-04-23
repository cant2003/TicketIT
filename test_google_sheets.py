from bot.services.google_sheets_service import (
    export_sheet_as_xlsx,
    sync_tickets_to_sheet,
    verificar_conexion_google,
)


def main():
    info = verificar_conexion_google()
    print("Spreadsheet:", info["spreadsheet_title"])
    print("Pestañas:", info["sheet_titles"])

    sync_tickets_to_sheet()
    print("Sincronización OK")

    archivo = export_sheet_as_xlsx()
    print("Exportación OK, bytes:", len(archivo.getvalue()))


if __name__ == "__main__":
    main()