from pydantic import BaseModel
from typing import List
from datetime import datetime

# --- Esquema para una Respuesta Individual (Entrada de la API) ---
# Representa una de las 20 respuestas que envía el frontend.
class RespuestaCreate(BaseModel):
    id_pregunta: int
    valor_respuesta_cruda: str

# --- Esquema para la Creación de un Diagnóstico Completo (Entrada de la API) ---
# Contiene la lista de las 20 respuestas.
class DiagnosticoCreate(BaseModel):
    respuestas: List[RespuestaCreate]


# --- Esquemas para la Visualización de Resultados (Salida de la API) ---

# --- Esquema para un valor SHAP individual ---
class DiagnosticoSHAP(BaseModel):
    id_pregunta: int
    valor_shap: float
    es_driver_clave: bool
    
    class Config:
        from_attributes = True
        
# --- Esquema para el Reporte de Diagnóstico Completo ---
# Este es el objeto principal que el backend enviará al frontend tras el análisis.
class Diagnostico(BaseModel):
    id_diagnostico: int
    fecha_diagnostico: datetime
    puntaje_cap_digital: float
    puntaje_cap_liderazgo: float
    nivel_madurez_predicho: str
    
    # Podríamos añadir aquí los valores SHAP y recomendaciones si queremos una única respuesta anidada.
    # Por ahora, se mantiene simple.
    
    class Config:
        from_attributes = True