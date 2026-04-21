from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# !Conexión SQLite
engine = create_engine(
    "sqlite:///tickets.db", connect_args={"check_same_thread": False}
)

# !Base de modelos
Base = declarative_base()


def now():
    return datetime.utcnow()


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String, nullable=False)
    area = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    estado = Column(String, default="Abierto")
    fecha_creacion = Column(DateTime, default=now)
    fecha_actualizacion = Column(DateTime, default=now, onupdate=now)
    chat_id = Column(String, nullable=False)
    asignado_a = Column(String, nullable=True)
    observacion = Column(String, nullable=True)
    
class SyncJob(Base):
    __tablename__ = "syncjobs"
    
    id= Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, nullable=False, index= True)
    accion = Column(String,nullable=False, default="insertar")
    estado = Column(String, nullable=False, default="pendiente", index=True)
    reintentos = Column(Integer, nullable=False, default=0)
    mensaje_error = Column(String, nullable=True)
    creado = Column(DateTime, default=now)
    actualizado = Column(DateTime, default=now, onupdate=now)

class SheetRowMap(Base):
    __tablename__ ="sheet_row_map"
    
    ticket_id = Column(Integer, primary_key=True, index=True)
    row_number = Column(Integer, nullable=False)
    creado = Column(DateTime, default=now)
    actualizado = Column(DateTime, default=now, onupdate=now)


Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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