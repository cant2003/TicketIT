import smtplib
from datetime import datetime
from email.message import EmailMessage

from backend.db import Ticket, get_db, get_db_tx
from bot.config import DESTINATARIO, EMAIL_PASS, REMITENTE
from bot.services.sync_jobs_service import crear_job_sync
from bot.services.usuarios_service import (
    obtener_o_crear_usuario,
    obtener_o_crear_usuario_ti,
    obtener_telegram_ids_ti,
)
from bot.ui.keyboards import boton_volver_menu


def _ahora():
    return datetime.utcnow()


def obtener_tickets_abiertos():
    with get_db() as db:
        return db.query(Ticket).filter(Ticket.estado == "Abierto").all()


def obtener_tickets_en_proceso(usuario):
    with get_db() as db:
        return (
            db.query(Ticket)
            .filter(
                Ticket.estado == "En Proceso",
                Ticket.asignado_a == usuario,
            )
            .all()
        )


def obtener_ticket(ticket_id):
    with get_db() as db:
        return db.query(Ticket).filter(Ticket.id == ticket_id).first()


def tomar_ticket(ticket_id, usuario, telegram_id):
    usuario_ti = obtener_o_crear_usuario_ti(usuario, telegram_id)

    with get_db_tx() as db:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

        if not ticket:
            raise ValueError("Ticket no encontrado")

        if ticket.estado == "En Proceso":
            raise ValueError("Ya está en proceso")

        ticket.estado = "En Proceso"
        ticket.asignado_a = usuario
        ticket.asignado_ti_id = usuario_ti.id
        ticket.fecha_actualizacion = _ahora()

        db.flush()
        db.refresh(ticket)

        ticket_id_sync = ticket.id

    try:
        crear_job_sync(ticket_id_sync)
    except Exception as e:
        print("Error sincronizando Google Sheets al tomar ticket:", e)

    return ticket


def crear_ticket(data):
    usuario = obtener_o_crear_usuario(
        nombre=data["usuario"],
        chat_id=data["chat_id"],
    )

    with get_db_tx() as db:
        ticket = Ticket(
            usuario=data["usuario"],
            chat_id=str(data["chat_id"]),
            usuario_id=usuario.id,
            area=data["area"],
            descripcion=data["descripcion"],
            estado="Abierto",
        )

        db.add(ticket)
        db.flush()
        db.refresh(ticket)

        ticket_id_sync = ticket.id

    try:
        crear_job_sync(ticket_id_sync)
    except Exception as e:
        print("Error sincronizando Google Sheets al crear ticket:", e)

    return ticket


def cerrar_ticket_con_observacion(ticket_id, observacion, usuario, telegram_id):
    usuario_ti = obtener_o_crear_usuario_ti(usuario, telegram_id)

    with get_db_tx() as db:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

        if not ticket:
            raise ValueError("Ticket no encontrado")

        if ticket.estado == "Cerrado":
            raise ValueError("El ticket ya se encuentra cerrado")

        ticket.estado = "Cerrado"
        ticket.observacion = observacion
        ticket.asignado_a = usuario
        ticket.asignado_ti_id = usuario_ti.id
        ticket.fecha_actualizacion = _ahora()

        db.flush()
        db.refresh(ticket)

        ticket_id_sync = ticket.id

    try:
        crear_job_sync(ticket_id_sync)
    except Exception as e:
        print("Error sincronizando Google Sheets al cerrar ticket:", e)

    return ticket


def enviar_correo(ticket_id):
    with get_db() as db:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

        if not ticket:
            print(f"No se encontró ticket {ticket_id} para enviar correo")
            return

        fecha_str = ticket.fecha_creacion.strftime("%d-%m-%Y %H:%M:%S")

        msg = EmailMessage()
        msg["Subject"] = f"🆕 Ticket Abierto #{ticket.id}, {fecha_str}"
        msg["From"] = f"TI-BOT SOPORTE (No-Reply) <{REMITENTE}>"
        msg["To"] = DESTINATARIO

        contenido = f"""Se ha abierto un nuevo ticket.

ID: {ticket.id}
Usuario: {ticket.usuario if ticket.usuario else "No especificado"}
Descripción: {ticket.descripcion if ticket.descripcion else "Sin descripción"}
Fecha: {fecha_str}
"""

        msg.set_content(contenido)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(REMITENTE, EMAIL_PASS)
            smtp.send_message(msg)
    except Exception as e:
        print("Error al enviar correo: ", e)


async def notificar_ti(context, ticket):
    mensaje = (
        f"🆕 Nuevo ticket\n"
        f"ID: {ticket.id}\n"
        f"Usuario: {ticket.usuario}\n"
        f"Área: {ticket.area}\n"
        f"Descripción: {ticket.descripcion}"
    )

    for telegram_id in obtener_telegram_ids_ti():
        try:
            await context.bot.send_message(
                chat_id=telegram_id,
                text=mensaje,
                reply_markup=boton_volver_menu(),
            )
        except Exception as e:
            print(f"Error enviando a {telegram_id}:", e)