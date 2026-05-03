from sqlalchemy.orm import Session
from datetime import datetime, timezone
import copy

from app.models.action_plan import PlanAccion, TareaPlan
from app.models.diagnosis import Diagnostico, DiagnosticoSHAP
from app.models.question import Recomendacion
from app.services.diagnosis_service import process_diagnosis
from app.schemas.action_plan_schema import TareaUpdate
from app.services.diagnosis_service import _normalize_row, process_diagnosis
import pandas as pd

def _obtener_respuesta_ideal(id_pregunta: int) -> any:
    """Devuelve la respuesta perfecta para simular que el usuario mejoró en esta área."""
    if id_pregunta in[1, 3, 7, 10, 13, 15, 17]:
        return "Si"
    elif id_pregunta == 6:
        return 4 # Nivel Alto en el mapeo
    elif id_pregunta == 18:
        return 3 # En más de la mitad
    elif id_pregunta == 8:
        return 7 # Todas
    else:
        return 7 # Escalas del 1 al 7, el ideal es 7

def crear_o_obtener_plan(db: Session, id_diagnostico: int):
    """Genera un plan de acción basado en las debilidades del diagnóstico."""
    plan_existente = db.query(PlanAccion).filter(PlanAccion.id_diagnostico == id_diagnostico).first()
    if plan_existente:
        return plan_existente

    # Si no existe, lo creamos
    nuevo_plan = PlanAccion(id_diagnostico=id_diagnostico)
    db.add(nuevo_plan)
    db.flush()

    # Buscamos los drivers clave (las debilidades) para hacerlas tareas
    drivers = db.query(DiagnosticoSHAP).filter(
        DiagnosticoSHAP.id_diagnostico == id_diagnostico,
        DiagnosticoSHAP.es_driver_clave == True
    ).all()

    for driver in drivers:
        tarea = TareaPlan(id_plan=nuevo_plan.id_plan, id_pregunta=driver.id_pregunta)
        db.add(tarea)
    
    db.commit()
    db.refresh(nuevo_plan)
    return nuevo_plan

def obtener_datos_dashboard(db: Session, id_plan: int):
    """EL MOTOR DE SIMULACIÓN: Obtiene el plan, las tareas y proyecta el futuro."""
    plan = db.query(PlanAccion).filter(PlanAccion.id_plan == id_plan).first()
    diagnostico = db.query(Diagnostico).filter(Diagnostico.id_diagnostico == plan.id_diagnostico).first()

    # 1. Formateamos las tareas para el frontend (To-Do List)
    tareas_formateadas = []
    tareas_completadas_ids =[]
    
    for t in plan.tareas:
        # Obtenemos la recomendación de la BD
        rec = db.query(Recomendacion).filter(
            Recomendacion.id_pregunta == t.id_pregunta, 
            Recomendacion.tipo_feedback == 'DEBILIDAD'
        ).first()
        
        tareas_formateadas.append({
            "id_tarea": t.id_tarea,
            "id_pregunta": t.id_pregunta,
            "titulo": rec.pregunta.subdominio if rec else f"Mejora en Q{t.id_pregunta}",
            "recomendacion": rec.texto_recomendacion if rec else "Acción requerida.",
            "estado": t.estado,
            "fecha_limite": t.fecha_limite,
            "fecha_completada": t.fecha_completada,
            "progreso": t.progreso
        })
        if t.estado == 'Completada':
            tareas_completadas_ids.append(t.id_pregunta)

    porcentaje = int((len(tareas_completadas_ids) / len(plan.tareas)) * 100) if plan.tareas else 0

    # =========================================================================
    # 2. EL MOTOR DE SIMULACIÓN (Interpolación Dinámica)
    # =========================================================================
    
    respuestas_originales = {f"Q{r.id_pregunta}": r.valor_respuesta_cruda for r in diagnostico.respuestas}
    
    # Análisis actual 
    analisis_actual = process_diagnosis(respuestas_crudas_dict=respuestas_originales)
    
    # Extraemos las respuestas normalizadas originales (en escala 1 a 7)
    fila_norm_proyectada = _normalize_row(respuestas_originales)
    
    # Por cada tarea, calculamos la mejora proporcional según su progreso (%)
    for t in plan.tareas:
        if t.progreso > 0:
            q_col = f"Q{t.id_pregunta}"
            val_actual = fila_norm_proyectada.at[0, q_col]
            val_ideal = 7.0 # El valor máximo/ideal siempre es 7 en nuestra escala normalizada
            
            # Si actual es 3, y progreso es 50%. Sube la mitad del camino hacia el 7.
            nuevo_val = val_actual + ((val_ideal - val_actual) * (t.progreso / 100.0))
            fila_norm_proyectada.at[0, q_col] = nuevo_val

    # Corremos el modelo con los valores matemáticamente proyectados
    analisis_proyectado = process_diagnosis(fila_normalizada_df=fila_norm_proyectada)

    # 4. Ensamblamos la Super-Respuesta JSON
    return {
        "id_plan": plan.id_plan,
        "id_diagnostico": plan.id_diagnostico,
        "estado_plan": plan.estado,
        "tareas": tareas_formateadas,
        "progreso_porcentaje": porcentaje,
        
        # Datos Comparativos para Gráficos
        "nivel_actual": analisis_actual["nivel_madurez_predicho"],
        "nivel_proyectado": analisis_proyectado["nivel_madurez_predicho"],
        
        "puntaje_digital_actual": analisis_actual["puntaje_cap_digital"],
        "puntaje_digital_proyectado": analisis_proyectado["puntaje_cap_digital"],
        
        "puntaje_liderazgo_actual": analisis_actual["puntaje_cap_liderazgo"],
        "puntaje_liderazgo_proyectado": analisis_proyectado["puntaje_cap_liderazgo"],
        
        "dominios_actuales": analisis_actual["desglose_dominios"],
        "dominios_proyectados": analisis_proyectado["desglose_dominios"]
    }

def actualizar_tarea(db: Session, id_tarea: int, update_data: TareaUpdate):
    """Marca una tarea como completada y guarda la fecha."""
    tarea = db.query(TareaPlan).filter(TareaPlan.id_tarea == id_tarea).first()
    if not tarea:
        return None
    
    tarea.estado = update_data.estado
    tarea.progreso = update_data.progreso
    if update_data.fecha_limite:
        tarea.fecha_limite = update_data.fecha_limite
        
    if tarea.estado == 'Completada' and not tarea.fecha_completada:
        tarea.fecha_completada = datetime.now(timezone.utc)
    elif tarea.estado == 'Pendiente':
        tarea.fecha_completada = None # Si la desmarca

    db.commit()
    db.refresh(tarea)
    return tarea