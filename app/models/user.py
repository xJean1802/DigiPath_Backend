# ==============================================================================
# Modelo de Base de Datos para Usuarios
# Define la estructura de datos para almacenar la información de usuarios
# y sus relaciones con diagnósticos
# ==============================================================================

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.db.database import Base
import datetime

class Usuario(Base):
    """
    Modelo para almacenar información de usuarios empresariales.
    Incluye datos de la empresa, credenciales y relación con diagnósticos.
    """
    __tablename__ = "Usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre_empresa = Column(String(255), nullable=False)
    ruc = Column(String(11), unique=True, index=True, nullable=False)
    correo_electronico = Column(String(255), unique=True, index=True, nullable=False)
    contrasena_hash = Column(String(255), nullable=False)
    fecha_registro = Column(DateTime, default=datetime.datetime.utcnow)

    diagnosticos = relationship("Diagnostico", back_populates="usuario")