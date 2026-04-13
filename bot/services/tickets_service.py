from backend.db import SessionLocal, Ticket
from datetime import datetime
import smtplib
from email.message import EmailMessage
from bot.config import EMAIL_PASS,REMITENTE,DESTINATARIO,USUARIOS_TI
from bot.ui.keyboards import boton_volver_menu


def _ahora():
    ahora = datetime.now()
    return (
        ahora.strftime("%d-%m-%Y"),
        ahora.strftime("%H:%M:%S")
    )
#!---------------------------------------------------------

#! Obtencion de tickets abiertos
def obtener_tickets_abiertos():
    db = SessionLocal()
    tickets = db.query(Ticket).filter(Ticket.estado == "Abierto").all()
    db.close()
    return tickets
#!---------------------------------------------------------

#!Tickets en proceso
def obtener_tickets_en_proceso(usuario):
    db = SessionLocal()
    tickets = db.query(Ticket).filter(
        Ticket.estado == "En Proceso",
        Ticket.asignado_a == usuario
    ).all()
    db.close()
    return tickets
#!---------------------------------------------------------

#! Ticket particular 
def obtener_ticket(ticket_id):
    db = SessionLocal()
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    db.close()
    return ticket
#!---------------------------------------------------------

#! Tomar Ticket
def tomar_ticket(ticket_id, usuario):
    db = SessionLocal()
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        db.close()
        raise ValueError("Ticket no encontrado")

    if ticket.estado == "En Proceso":
        db.close()
        raise ValueError("Ya está en proceso")

    ticket.estado = "En Proceso"
    ticket.asignado_a = usuario

    fecha, hora = _ahora()
    ticket.fecha_actualizacion = fecha
    ticket.hora_actualizacion = hora

    db.commit()
    db.refresh(ticket)
    db.close()

    return ticket
#!---------------------------------------------------------

#!Cerrar Ticket
def cerrar_ticket(ticket_id):
    db = SessionLocal()
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        db.close()
        raise ValueError("Ticket no encontrado")

    ticket.estado = "Cerrado"

    fecha, hora = _ahora()
    ticket.fecha_actualizacion = fecha
    ticket.hora_actualizacion = hora

    db.commit()
    db.refresh(ticket)
    db.close()

    return ticket
#!---------------------------------------------------------

#! Crear ticket
def crear_ticket(data):
    db = SessionLocal()

    fecha, hora = _ahora()

    ticket = Ticket(
        usuario=data["usuario"],
        area=data["area"],
        descripcion=data["descripcion"],
        estado="Abierto",
        fecha_creacion=fecha,
        hora_creacion=hora,
        fecha_actualizacion=fecha,
        hora_actualizacion=hora,
        chat_id=str(data["chat_id"])
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    db.close()

    return ticket
# !___________________________________________________
def cerrar_ticket_con_observacion(ticket_id, observacion, usuario):
    db = SessionLocal()

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        db.close()
        raise ValueError("Ticket no encontrado")
    
    if ticket.estado == "Cerrado":
        db.close()
        raise ValueError("El ticket ya se encuentra cerrado")

    ticket.estado = "Cerrado"
    ticket.observacion = observacion

    if not ticket.asignado_a:
        ticket.asignado_a = usuario

    ahora = datetime.now()
    ticket.fecha_actualizacion = ahora.strftime("%d-%m-%Y")
    ticket.hora_actualizacion = ahora.strftime("%H:%M:%S")

    db.commit()
    db.refresh(ticket)
    db.close()

    return ticket
#! ------------------------------------
def enviar_correo(id_ticket, usuario=None, descripcion=None, fecha_creacion=None):

    msg = EmailMessage()
    msg['Subject'] = f"🆕 Ticket Abierto #{id_ticket}, {fecha_creacion}"
    msg['From'] = f'TI-BOT SOPORTE (No-Reply) <{REMITENTE}>'
    msg['To'] = DESTINATARIO

    contenido = f"""Se ha abierto un nuevo ticket.

ID: {id_ticket}
Usuario: {usuario if usuario else 'No especificado'}
Descripción: {descripcion if descripcion else 'Sin descripción'}
"""

    msg.set_content(contenido)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as smtp: 
            smtp.login(REMITENTE, EMAIL_PASS)
            smtp.send_message(msg)
    except Exception as e:
        print("Error al enviar correo: ", e)

#!__________________________________________________
async def notificar_ti(context, ticket):
    mensaje = (
        f"🆕 Nuevo ticket\n"
        f"ID: {ticket.id}\n"
        f"Usuario: {ticket.usuario}\n"
        f"Área: {ticket.area}\n"
        f"Descripción: {ticket.descripcion}"
    )

    for chat_id in USUARIOS_TI:
        try:
            await context.bot.send_message(chat_id=chat_id, text=mensaje, reply_markup=boton_volver_menu())
        except Exception as e:
            print(f"Error enviando a {chat_id}:", e)