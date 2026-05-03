from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class PlanAccion(Base):
    __tablename__ = "Planes_Accion"

    id_plan = Column(Integer, primary_key=True, index=True)
    id_diagnostico = Column(Integer, ForeignKey("Diagnosticos.id_diagnostico", ondelete="CASCADE"), unique=True)
    fecha_creacion = Column(DateTime, server_default=func.now())
    estado = Column(String(50), default="En Progreso")

    # Relaciones
    diagnostico = relationship("Diagnostico")
    tareas = relationship("TareaPlan", back_populates="plan", cascade="all, delete-orphan")


class TareaPlan(Base):
    __tablename__ = "Tareas_Plan"

    id_tarea = Column(Integer, primary_key=True, index=True)
    id_plan = Column(Integer, ForeignKey("Planes_Accion.id_plan", ondelete="CASCADE"))
    id_pregunta = Column(Integer, ForeignKey("Preguntas.id_pregunta"))
    estado = Column(String(20), default="Pendiente")
    fecha_limite = Column(Date, nullable=True)
    fecha_completada = Column(DateTime, nullable=True)
    progreso = Column(Integer, default=0, nullable=False)

    # Relaciones
    plan = relationship("PlanAccion", back_populates="tareas")
    pregunta = relationship("Pregunta")