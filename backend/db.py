from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = "sqlite:///tickets.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

Base = declarative_base()


def now():
    return datetime.utcnow()


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    chat_id = Column(String, nullable=False, unique=True, index=True)
    creado = Column(DateTime, default=now)
    actualizado = Column(DateTime, default=now, onupdate=now)

    tickets = relationship("Ticket", back_populates="usuario_ref")


class UsuarioTI(Base):
    __tablename__ = "usuarios_ti"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    telegram_id = Column(String, nullable=False, unique=True, index=True)
    creado = Column(DateTime, default=now)
    actualizado = Column(DateTime, default=now, onupdate=now)

    tickets_asignados = relationship("Ticket", back_populates="asignado_ti_ref")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)

    # Compatibilidad temporal
    usuario = Column(String, nullable=False)
    chat_id = Column(String, nullable=False)
    asignado_a = Column(String, nullable=True)

    # Nuevo modelo relacional
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    asignado_ti_id = Column(
        Integer,
        ForeignKey("usuarios_ti.id"),
        nullable=True,
        index=True,
    )

    area = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    estado = Column(String, default="Abierto")
    fecha_creacion = Column(DateTime, default=now)
    fecha_actualizacion = Column(DateTime, default=now, onupdate=now)
    observacion = Column(String, nullable=True)

    usuario_ref = relationship("Usuario", back_populates="tickets")
    asignado_ti_ref = relationship("UsuarioTI", back_populates="tickets_asignados")


class SyncJob(Base):
    __tablename__ = "syncjobs"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, nullable=False, index=True)
    accion = Column(String, nullable=False, default="insertar")
    estado = Column(String, nullable=False, default="pendiente", index=True)
    reintentos = Column(Integer, nullable=False, default=0)
    mensaje_error = Column(String, nullable=True)
    creado = Column(DateTime, default=now)
    actualizado = Column(DateTime, default=now, onupdate=now)


class SheetRowMap(Base):
    __tablename__ = "sheet_row_map"

    ticket_id = Column(Integer, primary_key=True, index=True)
    row_number = Column(Integer, nullable=False)
    creado = Column(DateTime, default=now)
    actualizado = Column(DateTime, default=now, onupdate=now)


Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_tx():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()