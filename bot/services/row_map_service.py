from backend.db import SheetRowMap, get_db, get_db_tx


def obtener_fila_ticket(ticket_id: int):
    with get_db() as db:
        registro = (
            db.query(SheetRowMap)
            .filter(SheetRowMap.ticket_id == ticket_id)
            .first()
        )
        return registro.row_number if registro else None


def guardar_fila_ticket(ticket_id: int, row_number: int):
    with get_db_tx() as db:
        registro = (
            db.query(SheetRowMap)
            .filter(SheetRowMap.ticket_id == ticket_id)
            .first()
        )

        if registro:
            registro.row_number = row_number
        else:
            registro = SheetRowMap(
                ticket_id=ticket_id,
                row_number=row_number,
            )
            db.add(registro)

        db.flush()
        db.refresh(registro)
        return registro