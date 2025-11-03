from pydantic import BaseModel
from typing import Optional

# --- Esquema para la Lectura de una Recomendación ---
class Recomendacion(BaseModel):
    tipo_feedback: str
    texto_explicacion: str
    texto_recomendacion: Optional[str] = None
    
    class Config:
        from_attributes = True

# --- Esquema para la Lectura de una Pregunta ---
# Este es el formato que el frontend espera para construir el cuestionario.
class Pregunta(BaseModel):
    id_pregunta: int
    texto_pregunta: str
    seccion: str
    dominio: str
    subdominio: str
    tipo_pregunta: str
    
    class Config:
        from_attributes = True