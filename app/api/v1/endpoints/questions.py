from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.question import Pregunta
from app.schemas.question_schema import Pregunta as PreguntaSchema

router = APIRouter()

@router.get("/", response_model=List[PreguntaSchema])
def read_questions(db: Session = Depends(get_db)):
    """
    Endpoint para obtener la lista completa de las 20 preguntas del cuestionario.
    """
    # Se asegura de que las preguntas se envíen siempre en el orden correcto.
    questions = db.query(Pregunta).order_by(Pregunta.id_pregunta.asc()).all()
    return questions