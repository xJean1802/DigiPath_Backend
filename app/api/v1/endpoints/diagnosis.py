# ==============================================================================
# Módulo de Endpoints para Diagnósticos
# Maneja la creación, consulta y generación de reportes de diagnósticos
# ==============================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.schemas.diagnosis_schema import Diagnostico, DiagnosticoCreate
from app.services import diagnosis_service
from app.schemas.user_schema import Usuario
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.report_schema import ReporteDiagnostico
from app.services import report_service
from app.models.diagnosis import Diagnostico as DiagnosticoModel

router = APIRouter()

@router.get("/", response_model=List[Diagnostico])
def get_user_diagnosis_history(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Endpoint para obtener el historial de diagnósticos del usuario autenticado.
    """

    user_id = current_user.id_usuario
    return diagnosis_service.get_user_diagnoses(db=db, user_id=user_id)

@router.post("/", response_model=Diagnostico, status_code=status.HTTP_201_CREATED)
def submit_diagnosis(
    diagnostico_data: DiagnosticoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Endpoint para procesar un nuevo diagnóstico.
    
    Parámetros:
    - diagnostico_data: Contiene las 20 respuestas del cuestionario
    - db: Conexión a la base de datos
    - current_user: Usuario autenticado que realiza la solicitud
    
    El sistema procesa las respuestas utilizando el modelo de Machine Learning
    y genera un diagnóstico completo con recomendaciones.
    """
    if len(diagnostico_data.respuestas) != 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Se esperaban 20 respuestas, pero se recibieron {len(diagnostico_data.respuestas)}"
        )

    user_id = current_user.id_usuario

    return diagnosis_service.create_and_process_diagnosis(
        db=db, 
        user_id=user_id, 
        respuestas_schema=diagnostico_data.respuestas
    )

@router.get("/{diagnosis_id}/report", response_model=ReporteDiagnostico)
def get_diagnosis_full_report(
    diagnosis_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Endpoint que devuelve el reporte completo y formateado para el dashboard
    de un diagnóstico específico.
    """
    user_id = current_user.id_usuario
    
    # Verificamos que el diagnóstico exista y pertenezca al usuario
    db_diagnostico = db.query(DiagnosticoModel).filter(
        DiagnosticoModel.id_diagnostico == diagnosis_id,
        DiagnosticoModel.id_usuario == user_id
    ).first()

    if not db_diagnostico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnóstico no encontrado o no pertenece al usuario."
        )

    # Llamamos a un futuro servicio que generará el reporte
    return report_service.generate_full_report(db=db, db_diagnostico=db_diagnostico)