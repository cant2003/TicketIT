from backend.db import SessionLocal, SheetRowMap


def obtener_fila_ticket(ticket_id: int):
    db = SessionLocal()
    try:
        registro = db.query(SheetRowMap).filter(SheetRowMap.ticket_id == ticket_id).first()
        return registro.row_number if registro else None
    finally:
        db.close()


def guardar_fila_ticket(ticket_id: int, row_number: int):
    db = SessionLocal()
    try:
        registro = db.query(SheetRowMap).filter(SheetRowMap.ticket_id == ticket_id).first()

        if registro:
            registro.row_number = row_number
        else:
            registro = SheetRowMap(
                ticket_id=ticket_id,
                row_number=row_number,
            )
            db.add(registro)

        db.commit()
        db.refresh(registro)
        return registro
    finally:
        db.close()