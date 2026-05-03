from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db.database import get_db
from app.schemas.action_plan_schema import TareaUpdate, DashboardTransformacionResponse
from app.services import action_plan_service
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.user_schema import Usuario

router = APIRouter()

@router.post("/diagnostico/{id_diagnostico}", status_code=status.HTTP_201_CREATED)
def generar_o_obtener_plan(
    id_diagnostico: int, 
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    """
    Toma el ID de un diagnóstico, extrae sus debilidades y genera un Plan de Acción.
    Si el plan ya existe, simplemente lo devuelve.
    """
    # Llama a nuestro servicio
    plan = action_plan_service.crear_o_obtener_plan(db, id_diagnostico=id_diagnostico)
    
    return {
        "id_plan": plan.id_plan, 
        "mensaje": "Plan de acción listo para este diagnóstico."
    }

@router.get("/{id_plan}/dashboard", response_model=DashboardTransformacionResponse)
def obtener_dashboard_simulacion(
    id_plan: int, 
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    """
    El motor de simulación. Devuelve las tareas y los datos actuales vs. proyectados.
    """
    datos_dashboard = action_plan_service.obtener_datos_dashboard(db, id_plan=id_plan)
    if not datos_dashboard:
        raise HTTPException(status_code=404, detail="Plan de Acción no encontrado")
    
    return datos_dashboard

@router.put("/tareas/{id_tarea}")
def actualizar_tarea(
    id_tarea: int, 
    tarea_update: TareaUpdate, 
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    """
    Permite marcar una tarea como 'Completada' o 'Pendiente', y establecer fecha límite.
    """
    tarea = action_plan_service.actualizar_tarea(db, id_tarea=id_tarea, update_data=tarea_update)
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
        
    return {"mensaje": f"Tarea {id_tarea} actualizada a estado: {tarea.estado}"}