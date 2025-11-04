from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router

app = FastAPI(
    title="DigiPath API",
    description="API para el Sistema Predictivo de Madurez Digital para MYPEs Industriales.",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs"
)

# ==============================================================================
# CONFIGURACIÓN DE CORS
# ==============================================================================

# 2. DEFINIMOS DE DÓNDE PERMITIREMOS LAS CONEXIONES
origins = [
    "http://localhost:8080",  # El origen del frontend de React en desarrollo
    "http://localhost:5173",  # Un puerto común para Vite que a veces usa
    # Cuando despliegues tu frontend, añadirás su URL aquí:
    # "https://tu-frontend-en-azure.com", 
]

# 3. AÑADIMOS EL MIDDLEWARE A LA APLICACIÓN
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Lista de orígenes permitidos
    allow_credentials=True, # Permitir cookies (importante para autenticación)
    allow_methods=["*"],    # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"],    # Permitir todas las cabeceras
)


# Incluye todas las rutas de la API bajo el prefijo /api/v1
app.include_router(api_router, prefix="/api/v1")

# Puedes añadir rutas simples aquí si quieres
@app.get("/")
def read_root():
    return {"message": "Welcome to DigiPath API"}