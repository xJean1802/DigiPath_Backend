from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Crear el motor de la base de datos usando la URL de configuración
# El argumento connect_args es específico para SQLite, lo quitamos para SQL Server.
# El argumento pool_pre_ping=True verifica las conexiones antes de usarlas, lo cual es bueno para la producción.
engine = create_engine(
    settings.DATABASE_URL, 
    pool_pre_ping=True
)

# Crear una fábrica de sesiones (SessionLocal)
# autocommit=False y autoflush=False son las configuraciones estándar
# para asegurar que las transacciones se manejen explícitamente.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear una clase base para nuestros modelos ORM (los que irán en la carpeta models/)
Base = declarative_base()


# --- Función de Dependencia para FastAPI ---
def get_db():
    """
    Esta función es una dependencia de FastAPI que crea una nueva sesión
    de base de datos para cada solicitud entrante y la cierra cuando termina.
    Esto asegura que las sesiones no se queden abiertas y se manejen correctamente.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()