import time

from backend.db import SessionLocal, SyncJob, Ticket
from bot.services.google_sheets_service import upsert_ticket_en_sheet

MAX_REINTENTOS = 3
TIEMPO_ESPERA_SIN_JOBS = 2
TIEMPO_ESPERA_TRAS_ERROR = 3


def obtener_job_pendiente(db):
    return (
        db.query(SyncJob)
        .filter(SyncJob.estado == "pendiente")
        .order_by(SyncJob.id.asc())
        .first()
    )


def procesar_job(job, db):
    try:
        print(f"Procesando job {job.id} para ticket {job.ticket_id}")

        job.estado = "procesando"
        db.commit()

        ticket = db.query(Ticket).filter(Ticket.id == job.ticket_id).first()

        if not ticket:
            raise Exception("Ticket no encontrado")

        upsert_ticket_en_sheet(ticket)

        job.estado = "completado"
        job.mensaje_error = None

        print(f"Job {job.id} completado correctamente")

    except Exception as e:
        job.reintentos += 1
        job.mensaje_error = str(e)

        if job.reintentos < MAX_REINTENTOS:
            job.estado = "pendiente"
            print(
                f"Job {job.id} falló "
                f"(intento {job.reintentos}/{MAX_REINTENTOS}). "
                f"Se reintentará. Error: {e}"
            )
        else:
            job.estado = "error"
            print(
                f"Job {job.id} falló definitivamente tras "
                f"{job.reintentos} intentos. Error: {e}"
            )

        time.sleep(TIEMPO_ESPERA_TRAS_ERROR)

    finally:
        db.commit()


def iniciar_worker():
    print("🟢 Worker de sincronización iniciado...")

    while True:
        db = SessionLocal()

        try:
            job = obtener_job_pendiente(db)

            if not job:
                time.sleep(TIEMPO_ESPERA_SIN_JOBS)
                continue

            procesar_job(job, db)

        except Exception as e:
            print(f"Error general en worker: {e}")
            time.sleep(TIEMPO_ESPERA_TRAS_ERROR)

        finally:
            db.close()


if __name__ == "__main__":
    iniciar_worker()    