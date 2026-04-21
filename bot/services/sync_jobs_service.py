from backend.db import SessionLocal, SyncJob


def crear_job_sync(ticket_id: int, accion: str = "insertar"):
    db = SessionLocal()
    try:
        # 🔍 buscar si ya existe un job activo para este ticket
        job_existente = (
            db.query(SyncJob)
            .filter(
                SyncJob.ticket_id == ticket_id,
                SyncJob.estado.in_(["pendiente", "procesando"]),
            )
            .first()
        )

        if job_existente:
            print(
                f"Ya existe job activo para ticket {ticket_id} "
                f"(job_id={job_existente.id})"
            )
            return job_existente

        # ✅ si no existe, crear nuevo
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

        print(f"Nuevo job creado (id={job.id}) para ticket {ticket_id}")

        return job

    finally:
        db.close()


def reactivar_job(job_id: int):
    db = SessionLocal()
    try:
        job = db.query(SyncJob).filter(SyncJob.id == job_id).first()

        if not job:
            raise ValueError("Job no encontrado")

        job.estado = "pendiente"
        job.reintentos = 0
        job.mensaje_error = None

        db.commit()
        db.refresh(job)

        print(f"Job {job.id} reactivado")

        return job

    finally:
        db.close()