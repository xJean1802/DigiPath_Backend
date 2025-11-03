from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, Boolean
from sqlalchemy.orm import relationship
from .question import Pregunta
from app.db.database import Base
import datetime

class Diagnostico(Base):
    __tablename__ = "Diagnosticos"

    id_diagnostico = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("Usuarios.id_usuario"), nullable=False)
    fecha_diagnostico = Column(DateTime, default=datetime.datetime.utcnow)
    puntaje_cap_digital = Column(DECIMAL(5, 2), nullable=False)
    puntaje_cap_liderazgo = Column(DECIMAL(5, 2), nullable=False)
    nivel_madurez_predicho = Column(String(50), nullable=False)

    usuario = relationship("Usuario", back_populates="diagnosticos")
    respuestas = relationship("Respuesta", back_populates="diagnostico", cascade="all, delete-orphan")
    valores_shap = relationship("DiagnosticoSHAP", back_populates="diagnostico", cascade="all, delete-orphan")

class Respuesta(Base):
    __tablename__ = "Respuestas"

    id_respuesta = Column(Integer, primary_key=True, index=True)
    id_diagnostico = Column(Integer, ForeignKey("Diagnosticos.id_diagnostico"), nullable=False)
    id_pregunta = Column(Integer, ForeignKey("Preguntas.id_pregunta"), nullable=False)
    valor_respuesta_cruda = Column(String(50), nullable=False)
    valor_normalizado = Column(Integer, nullable=False)

    diagnostico = relationship("Diagnostico", back_populates="respuestas")
    pregunta = relationship("Pregunta")


class DiagnosticoSHAP(Base):
    __tablename__ = "Diagnostico_SHAP"

    id_shap = Column(Integer, primary_key=True, index=True)
    id_diagnostico = Column(Integer, ForeignKey("Diagnosticos.id_diagnostico"), nullable=False)
    id_pregunta = Column(Integer, ForeignKey("Preguntas.id_pregunta"), nullable=False)
    valor_shap = Column(DECIMAL(18, 9), nullable=False)
    es_driver_clave = Column(Boolean, default=False, nullable=False)

    diagnostico = relationship("Diagnostico", back_populates="valores_shap")
    pregunta = relationship("Pregunta")