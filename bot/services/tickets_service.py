from backend.db import SessionLocal, Ticket
from datetime import datetime

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

#!Crear Ticket
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

def cerrar_ticket_con_observacion(ticket_id, observacion):
    db = SessionLocal()

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        db.close()
        raise ValueError("Ticket no encontrado")

    ticket.estado = "Cerrado"
    ticket.observacion = observacion

    ahora = datetime.now()
    ticket.fecha_actualizacion = ahora.strftime("%d-%m-%Y")
    ticket.hora_actualizacion = ahora.strftime("%H:%M:%S")

    db.commit()
    db.refresh(ticket)
    db.close()

    return ticket
