from backend.db import SyncJob, get_db_tx


def crear_job_sync(ticket_id: int, accion: str = "insertar"):
    with get_db_tx() as db:
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

        job = SyncJob(
            ticket_id=ticket_id,
            accion=accion,
            estado="pendiente",
            reintentos=0,
            mensaje_error=None,
        )

        db.add(job)
        db.flush()
        db.refresh(job)

        print(f"Nuevo job creado (id={job.id}) para ticket {ticket_id}")

        return job

def reactivar_job(job_id: int):
    with get_db_tx() as db:
        job = db.query(SyncJob).filter(SyncJob.id == job_id).first()

        if not job:
            raise ValueError("Job no encontrado")

        job.estado = "pendiente"
        job.reintentos = 0
        job.mensaje_error = None

        db.flush()
        db.refresh(job)

        print(f"Job {job.id} reactivado")

        return job