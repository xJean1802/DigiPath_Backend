from pydantic import BaseModel
from typing import List, Dict

class FactorImpacto(BaseModel):
    pregunta_id: str
    titulo: str
    peso_impacto: float
    porque: str
    accion: str | None = None # Será None para las fortalezas

class ReporteDiagnostico(BaseModel):
    # --- Módulo 1: Resumen Ejecutivo ---
    id_diagnostico: int
    fecha_diagnostico: str
    nivel_madurez_predicho: str
    potencial_avance: float

    # --- Módulo 2: Análisis de Factores (SHAP) ---
    areas_mejora_prioritarias: List[FactorImpacto]
    fortalezas_a_mantener: List[FactorImpacto]
    
    # --- Módulo 3: Desglose Gráfico ---
    desglose_dominios: Dict[str, float]