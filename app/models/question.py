# ==============================================================================
# Modelos de Base de Datos para Preguntas y Recomendaciones
# Define las estructuras para el cuestionario de diagnóstico y
# el sistema de recomendaciones asociado
# ==============================================================================

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Pregunta(Base):
    """
    Modelo para las preguntas del cuestionario de diagnóstico.
    Organiza las preguntas por secciones, dominios y subdominios.
    """
    __tablename__ = "Preguntas"

    id_pregunta = Column(Integer, primary_key=True, index=True)
    texto_pregunta = Column(Text, nullable=False)
    seccion = Column(String(100), nullable=False)
    dominio = Column(String(100), nullable=False)
    subdominio = Column(String(100), nullable=False)
    tipo_pregunta = Column(String(50), nullable=False)

    recomendaciones = relationship("Recomendacion", back_populates="pregunta")

class Recomendacion(Base):
    """
    Modelo para almacenar recomendaciones asociadas a cada pregunta.
    Incluye explicaciones y acciones recomendadas según el tipo de feedback.
    """
    __tablename__ = "Recomendaciones"

    id_recomendacion = Column(Integer, primary_key=True, index=True)
    id_pregunta = Column(Integer, ForeignKey("Preguntas.id_pregunta"), nullable=False)
    tipo_feedback = Column(String(20), nullable=False) # 'DEBILIDAD' o 'FORTALEZA'
    texto_explicacion = Column(Text, nullable=False)
    texto_recomendacion = Column(Text, nullable=True)

    pregunta = relationship("Pregunta", back_populates="recomendaciones")