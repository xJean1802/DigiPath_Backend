from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Dict, Any

from app.models.diagnosis import Diagnostico as DiagnosticoModel, DiagnosticoSHAP
from app.models.question import Recomendacion # <-- Importamos el nuevo modelo
from app.schemas.report_schema import FactorImpacto

# Reutilizamos la lógica de ML del servicio de diagnóstico
from app.services.diagnosis_service import process_diagnosis 

def _get_factores_de_impacto(db: Session, db_shap_valores: List[DiagnosticoSHAP], tipo: str) -> List[FactorImpacto]:
    """Helper para buscar textos de recomendación y formatear los factores de impacto."""
    factores = []
    
    total_impacto_abs = sum(abs(s.valor_shap) for s in db_shap_valores)
    if total_impacto_abs == 0: total_impacto_abs = 1

    for shap_val in db_shap_valores:
        # Buscamos en nuestra "base de conocimiento" la recomendación asociada
        db_rec = db.query(Recomendacion).filter(
            Recomendacion.id_pregunta == shap_val.id_pregunta,
            Recomendacion.tipo_feedback == tipo
        ).first()

        if db_rec:
            factores.append(FactorImpacto(
                pregunta_id=f"Q{shap_val.id_pregunta}",
                # El título del factor es el subdominio de la pregunta (ej. 'Conocimiento del Cliente')
                titulo=db_rec.pregunta.subdominio, 
                peso_impacto=round((abs(shap_val.valor_shap) / total_impacto_abs) * 100, 2),
                porque=db_rec.texto_explicacion,
                accion=db_rec.texto_recomendacion if tipo == 'DEBILIDAD' else None
            ))
    return factores

def generate_full_report(db: Session, db_diagnostico: DiagnosticoModel) -> Dict[str, Any]:
    """
    Ensambla el reporte completo para el dashboard a partir de un diagnóstico
    y sus valores SHAP asociados.
    """
    
    # 1. Recuperar los valores SHAP de la BD
    shap_valores = db_diagnostico.valores_shap
    if not shap_valores:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron datos de análisis SHAP.")

    # 2. Identificar drivers (debilidades) y fortalezas desde los datos SHAP guardados
    debilidades_shap = [s for s in shap_valores if s.es_driver_clave]
    # Fortalezas son las 3 con el valor SHAP positivo más alto
    fortalezas_shap = sorted([s for s in shap_valores if s.valor_shap > 0], key=lambda x: x.valor_shap, reverse=True)[:3]
    
    # 3. Construir los objetos de factores de impacto con los textos de la BD
    areas_mejora = _get_factores_de_impacto(db, debilidades_shap, 'DEBILIDAD')
    fortalezas = _get_factores_de_impacto(db, fortalezas_shap, 'FORTALEZA')

    # 4. Reutilizar la lógica de ML para calcular métricas no guardadas
    respuestas_crudas_dict = {f"Q{r.id_pregunta}": r.valor_respuesta_cruda for r in db_diagnostico.respuestas}
    analisis_ml = process_diagnosis(respuestas_crudas_dict)

    # 5. Ensamblar el JSON final para el frontend
    reporte_final = {
        "id_diagnostico": db_diagnostico.id_diagnostico,
        "fecha_diagnostico": db_diagnostico.fecha_diagnostico.isoformat(),
        "nivel_madurez_predicho": db_diagnostico.nivel_madurez_predicho,
        "potencial_avance": analisis_ml["potencial_avance"],
        "areas_mejora_prioritarias": areas_mejora,
        "fortalezas_a_mantener": fortalezas,
        "desglose_dominios": analisis_ml["desglose_dominios"]
    }
    
    return reporte_final