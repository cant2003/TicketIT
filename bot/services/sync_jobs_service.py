from backend.db import SessionLocal, SyncJob


def crear_job_sync(ticket_id: int, accion: str = "insertar"):
    db = SessionLocal()
    try:
        job = SyncJob(
            ticket_id=ticket_id,
            accion=accion,
            estado="pendiente",
            reintentos=0,
            mensaje_error=None,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    finally:
        db.close()