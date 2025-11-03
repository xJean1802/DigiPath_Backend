from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    class Config:
        env_file = ".env"

# Creamos una instancia única de la configuración que será importada
# por el resto de la aplicación.
settings = Settings()