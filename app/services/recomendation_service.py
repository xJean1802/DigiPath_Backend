# ==============================================================================
# Servicio de Recomendaciones
# Genera recomendaciones personalizadas basadas en los drivers identificados
# en el diagnóstico de madurez digital
# ==============================================================================

from sqlalchemy.orm import Session
from app.models.question import Recomendacion

def get_recommendations_for_drivers(db: Session, drivers: list) -> list:
    """
    Busca en la base de datos las explicaciones y recomendaciones
    para una lista de preguntas identificadas como debilidades.
    """
    recomendaciones_finales = []
    
    for driver in drivers:
        pregunta_id = int(driver['pregunta_id'][1:])
        
        # Busca el texto en la tabla de Recomendaciones
        db_rec = db.query(Recomendacion).filter(
            Recomendacion.id_pregunta == pregunta_id,
            Recomendacion.tipo_feedback == 'DEBILIDAD'
        ).first()
        
        if db_rec:
            recomendaciones_finales.append({
                "pregunta_id": f"Q{pregunta_id}",
                "titulo": db_rec.pregunta.subdominio, # Usamos el subdominio como título
                "porque": db_rec.texto_explicacion,
                "accion": db_rec.texto_recomendacion,
                "peso_impacto": driver['peso_impacto']
            })
            
    return recomendaciones_finales

# Se debe hacer lo mismo para las fortalezas