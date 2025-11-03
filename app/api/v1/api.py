from fastapi import APIRouter
from .endpoints import auth, diagnosis

api_router = APIRouter()

# Incluimos los routers de cada funcionalidad
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(diagnosis.router, prefix="/diagnosis", tags=["Diagnósticos"])

# app/main.py

from fastapi import FastAPI
from app.api.v1.api import api_router
from app.db.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware

# --- Creación de la aplicación FastAPI ---
app = FastAPI(
    title="API del Sistema Predictivo de Madurez Digital",
    description="API para la tesis de JP y LF.",
    version="1.0.0"
)

# --- Configuración de CORS ---
# Permite que tu frontend (que se ejecutará en un dominio diferente)
# pueda comunicarse con este backend.
origins = [
    "http://localhost",
    "http://localhost:3000", # Asumiendo que React corre en el puerto 3000
    # Añadir aquí la URL de tu frontend cuando lo despliegues
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Creación de las tablas en la base de datos ---
# Esta línea le dice a SQLAlchemy que cree todas las tablas
# definidas en nuestros modelos si no existen.
Base.metadata.create_all(bind=engine)


# --- Inclusión de las rutas de la API ---
app.include_router(api_router, prefix="/api/v1")


# --- Endpoint de prueba en la raíz ---
@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de DigiPath"}