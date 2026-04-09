from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# !Conexión SQLite
engine = create_engine("sqlite:///tickets.db", connect_args={"check_same_thread": False})

# !Base de modelos
Base = declarative_base()

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String, nullable=False)
    area = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    estado = Column(String, default="Abierto")
    fecha_creacion = Column(String, default=datetime.utcnow().strftime("%d-%m-%Y"))
    hora_creacion = Column(String, default=datetime.utcnow().strftime("%H:%M:%S"))
    fecha_actualizacion = Column(String, default=datetime.utcnow().strftime("%d-%m-%Y"))
    hora_actualizacion = Column(String, default=datetime.utcnow().strftime("%H:%M:%S"))
    chat_id = Column(String, nullable=False)
    asignado_a = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)