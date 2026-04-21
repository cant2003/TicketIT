from backend.db import Ticket, get_db
from datetime import datetime, timedelta

#! FILTRAR TODO
def tickets_todos():
   with get_db() as db:
        return (
            db.query(Ticket)
            .order_by(Ticket.id.desc())
            .limit(10000)
            .all()
        )
#!--------------------------------------------------------
#! FILTRAR POR Asignado
def tickets_asignado(asignado):
    with get_db() as db:
        return(
            db.query(Ticket)
            .filter(
                Ticket.asignado_a.ilike(f"%{asignado}%"), 
                Ticket.estado == "Cerrado"
            )
            .order_by(Ticket.id.desc())
            .limit(10000)
            .all()
        )
#!--------------------------------------------------------
def tickets_usuario(usuario):
    with get_db() as db:
        return(
            db.query(Ticket)
            .filter(
                Ticket.usuario.ilike(f"%{usuario}%"), 
                Ticket.estado == "Cerrado"
            )
            .order_by(Ticket.id.desc())
            .limit(10000)
            .all()
        )
#!-------------------------------------------------------


def tickets_ultimo_anyo():
    db = SessionLocal()

    ahora = datetime.utcnow()
    hace_12_meses = ahora - timedelta(days=365)

    tickets = (
        db.query(Ticket)
        .filter(
            Ticket.fecha_creacion >= hace_12_meses,
            Ticket.fecha_creacion <= ahora,
            Ticket.estado == "Cerrado",
        )
        .order_by(Ticket.id.desc())
        .limit(10000)
        .all()
    )

    db.close()
    return tickets


#!-------------------------------------------------------


def tickets_ultimo_mes():
    db = SessionLocal()

    ahora = datetime.utcnow()
    hace_30_dias = ahora - timedelta(days=30)

    tickets = (
        db.query(Ticket)
        .filter(
            Ticket.fecha_creacion >= hace_30_dias,
            Ticket.fecha_creacion <= ahora,
            Ticket.estado == "Cerrado",
        )
        .order_by(Ticket.id.desc())
        .limit(10000)
        .all()
    )

    db.close()
    return tickets


#!---------------------------------------------------------
def tickets_hoy():
    db = SessionLocal()

    ahora = datetime.utcnow()

    inicio_dia = datetime(ahora.year, ahora.month, ahora.day)
    fin_dia = inicio_dia + timedelta(days=1)

    tickets = (
        db.query(Ticket)
        .filter(
            Ticket.fecha_creacion >= inicio_dia,
            Ticket.fecha_creacion < fin_dia,
            Ticket.estado == "Cerrado",
        )
        .order_by(Ticket.id.desc())
        .limit(10000)
        .all()
    )

    db.close()
    return tickets


#!---------------------------------------------------------
def tickets_semana_actual():
    db = SessionLocal()

    ahora = datetime.utcnow()

    # lunes de esta semana
    inicio_semana = ahora - timedelta(days=ahora.weekday())
    inicio_semana = datetime(inicio_semana.year, inicio_semana.month, inicio_semana.day)

    fin_semana = inicio_semana + timedelta(days=7)

    tickets = (
        db.query(Ticket)
        .filter(
            Ticket.fecha_creacion >= inicio_semana,
            Ticket.fecha_creacion < fin_semana,
            Ticket.estado == "Cerrado",
        )
        .order_by(Ticket.id.desc())
        .limit(10000)
        .all()
    )

    db.close()
    return tickets


#!------------------------------------------------
def tickets_por_rango(fecha_inicio_str, fecha_fin_str):
    db = SessionLocal()

    try:
        # convertir strings a datetime
        inicio = datetime.strptime(fecha_inicio_str, "%d-%m-%Y")
        fin = datetime.strptime(fecha_fin_str, "%d-%m-%Y")

        # incluir todo el día final
        fin = fin + timedelta(days=1)

    except ValueError:
        db.close()
        raise ValueError("Formato de fecha inválido. Usa dd-mm-yyyy")

    tickets = (
        db.query(Ticket)
        .filter(
            Ticket.fecha_creacion >= inicio,
            Ticket.fecha_creacion < fin,
            Ticket.estado == "Cerrado",
        )
        .order_by(Ticket.id.desc())
        .limit(10000)
        .all()
    )

    db.close()
    return tickets