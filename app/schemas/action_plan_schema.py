from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, date

class TareaUpdate(BaseModel):
    estado: str # 'Pendiente' o 'Completada'
    fecha_limite: Optional[date] = None
    progreso: int

class TareaResponse(BaseModel):
    id_tarea: int
    id_pregunta: int
    titulo: str
    recomendacion: str
    estado: str
    fecha_limite: Optional[date]
    fecha_completada: Optional[datetime]
    progreso: int
    
    class Config:
        from_attributes = True

# ESTE ES EL JSON QUE LLENARÁ EL FRONTEND
class DashboardTransformacionResponse(BaseModel):
    id_plan: int
    id_diagnostico: int
    estado_plan: str
    
    # 1. To-Do List
    tareas: List[TareaResponse]
    progreso_porcentaje: int # Ej: 33%
    
    # 2. Datos para el Medidor (Gauge Chart) / Comparativas
    nivel_actual: str
    nivel_proyectado: str
    puntaje_digital_actual: float
    puntaje_digital_proyectado: float
    puntaje_liderazgo_actual: float
    puntaje_liderazgo_proyectado: float
    
    # 3. Datos para el Radar Chart (Superposición de Dominios)
    dominios_actuales: Dict[str, float]
    dominios_proyectados: Dict[str, float]