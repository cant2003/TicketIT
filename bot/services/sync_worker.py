import time

from backend.db import SyncJob, Ticket, get_db, get_db_tx
from bot.services.google_sheets_service import upsert_ticket_en_sheet

MAX_REINTENTOS = 3
TIEMPO_ESPERA_SIN_JOBS = 2
TIEMPO_ESPERA_TRAS_ERROR = 3


def resetear_jobs_procesando():
    with get_db_tx() as db:
        jobs_reiniciados = (
            db.query(SyncJob)
            .filter(SyncJob.estado == "procesando")
            .update({SyncJob.estado: "pendiente"})
        )

        if jobs_reiniciados:
            print(f"Jobs en proceso reiniciados: {jobs_reiniciados}")


def obtener_job_pendiente():
    with get_db() as db:
        return (
            db.query(SyncJob)
            .filter(SyncJob.estado == "pendiente")
            .order_by(SyncJob.id.asc())
            .first()
        )


def marcar_job_procesando(job_id: int):
    with get_db_tx() as db:
        job = db.query(SyncJob).filter(SyncJob.id == job_id).first()

        if not job:
            raise ValueError("Job no encontrado")

        job.estado = "procesando"
        db.flush()
        db.refresh(job)

        return job.ticket_id


def obtener_ticket(ticket_id: int):
    with get_db() as db:
        return db.query(Ticket).filter(Ticket.id == ticket_id).first()


def marcar_job_completado(job_id: int):
    with get_db_tx() as db:
        job = db.query(SyncJob).filter(SyncJob.id == job_id).first()

        if not job:
            raise ValueError("Job no encontrado")

        job.estado = "completado"
        job.mensaje_error = None

        db.flush()


def marcar_job_error(job_id: int, error: Exception):
    with get_db_tx() as db:
        job = db.query(SyncJob).filter(SyncJob.id == job_id).first()

        if not job:
            raise ValueError("Job no encontrado")

        job.reintentos += 1
        job.mensaje_error = str(error)

        if job.reintentos < MAX_REINTENTOS:
            job.estado = "pendiente"
            print(
                f"Job {job.id} falló "
                f"(intento {job.reintentos}/{MAX_REINTENTOS}). "
                f"Se reintentará. Error: {error}"
            )
        else:
            job.estado = "error"
            print(
                f"Job {job.id} falló definitivamente tras "
                f"{job.reintentos} intentos. Error: {error}"
            )

        db.flush()


def procesar_job(job):
    job_id = job.id

    try:
        print(f"Procesando job {job.id} para ticket {job.ticket_id}")

        ticket_id = marcar_job_procesando(job_id)
        ticket = obtener_ticket(ticket_id)

        if not ticket:
            raise ValueError("Ticket no encontrado")

        upsert_ticket_en_sheet(ticket)
        marcar_job_completado(job_id)

        print(f"Job {job_id} completado correctamente")

    except Exception as e:
        marcar_job_error(job_id, e)
        time.sleep(TIEMPO_ESPERA_TRAS_ERROR)


def iniciar_worker():
    print("Worker de sincronización iniciado...")
    resetear_jobs_procesando()

    while True:
        try:
            job = obtener_job_pendiente()

            if not job:
                time.sleep(TIEMPO_ESPERA_SIN_JOBS)
                continue

            procesar_job(job)

        except Exception as e:
            print(f"Error general en worker: {e}")
            time.sleep(TIEMPO_ESPERA_TRAS_ERROR)


if __name__ == "__main__":
    iniciar_worker()