from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.db.database import Base, engine

# --- Creación de las tablas en la base de datos ---
# Esta línea le dice a SQLAlchemy que cree todas las tablas definidas
# en nuestros modelos si aún no existen en la base de datos.
# Es seguro ejecutarlo cada vez; solo crea las tablas que faltan.
def create_tables():
    Base.metadata.create_all(bind=engine)

# Llamamos a la función al iniciar la aplicación.
create_tables()


# --- Creación de la aplicación FastAPI ---
# Aquí se define el objeto 'app' que Uvicorn busca.
app = FastAPI(
    title="DigiPath API",
    description="API para el Sistema Predictivo de Madurez Digital para MYPEs Industriales.",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",  # URL de la especificación OpenAPI
    docs_url="/api/v1/docs"              # URL de la documentación interactiva Swagger UI
)


# --- Configuración de CORS ---
# Esto es crucial para permitir que tu frontend de React (que se ejecutará
# en un dominio diferente, ej. localhost:3000) pueda comunicarse con este backend.
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173", # Puerto común para Vite/React
    # Cuando despliegues tu frontend, deberás añadir su URL aquí.
    # ej. "https://mi-frontend-digipath.azurewebsites.net"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Inclusión de las rutas de la API ---
# Le decimos a la aplicación principal que incluya todas las rutas
# definidas en nuestro api_router (de app/api/v1/api.py).
# Todas las rutas tendrán el prefijo /api/v1.
app.include_router(api_router, prefix="/api/v1")


# --- Endpoint de prueba en la raíz ---
# Útil para verificar rápidamente que el servidor está funcionando.
@app.get("/", tags=["Root"])
def read_root():
    """
    Endpoint raíz para verificar el estado de la API.
    """
    return {"message": "Bienvenido a la API de DigiPath v1"}