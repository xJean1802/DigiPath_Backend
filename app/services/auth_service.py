# ==============================================================================
# Servicio de Autenticación y Gestión de Usuarios
# Proporciona funciones para autenticación, gestión de contraseñas y usuarios
# ==============================================================================

from sqlalchemy.orm import Session
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from app.models.user import Usuario
from app.schemas.user_schema import UsuarioCreate
from app.core.config import settings
from app.schemas.user_schema import UsuarioUpdate

# NOTA: usamos la librería `bcrypt` directamente para evitar la inicialización interna de passlib
# que en algunas versiones provoca el error mostrado.

def _truncate_to_72_utf8_bytes(password: str) -> bytes:
    """
    Retorna la contraseña en bytes UTF-8 truncada por caracteres de modo que
    la representación en bytes tenga como máximo 72 bytes (límite de bcrypt).
    Devolvemos bytes listos para pasar a bcrypt.hashpw / bcrypt.checkpw.
    """
    if not password:
        return b""
    b = password.encode("utf-8")
    if len(b) <= 72:
        return b
    # búsqueda binaria por número de caracteres para no cortar en medio de un código UTF-8
    lo, hi = 0, len(password)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if len(password[:mid].encode("utf-8")) <= 72:
            lo = mid
        else:
            hi = mid - 1
    return password[:lo].encode("utf-8")

# --- Funciones de Servicio para Usuarios y Autenticación ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña en texto plano coincide con su hash (truncando a 72 bytes)."""
    truncated = _truncate_to_72_utf8_bytes(plain_password)
    # hashed_password se almacena como str, lo convertimos a bytes
    if isinstance(hashed_password, str):
        hashed_bytes = hashed_password.encode("utf-8")
    else:
        hashed_bytes = hashed_password
    try:
        return bcrypt.checkpw(truncated, hashed_bytes)
    except ValueError:
        # si el hash almacenado tiene formato inesperado, fallamos la verificación
        return False

def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña (truncando a 72 bytes en UTF-8)."""
    truncated = _truncate_to_72_utf8_bytes(password)
    hashed = bcrypt.hashpw(truncated, bcrypt.gensalt())
    return hashed.decode("utf-8")

def get_user_by_email(db: Session, email: str) -> Optional[Usuario]:
    """Busca y devuelve un usuario por su correo electrónico."""
    return db.query(Usuario).filter(Usuario.correo_electronico == email).first()

def create_user(db: Session, user: UsuarioCreate) -> Usuario:
    """Crea un nuevo usuario en la base de datos."""
    hashed_password = get_password_hash(user.contrasena)
    # Creamos el objeto del modelo SQLAlchemy
    db_user = Usuario(
        correo_electronico=user.correo_electronico,
        nombre_empresa=user.nombre_empresa,
        ruc=user.ruc,
        contrasena_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, db_user: Usuario, user_update: UsuarioUpdate) -> Usuario:
    """Actualiza los datos de un usuario en la base de datos."""
    
    # Usamos model_dump(exclude_unset=True) que es el método correcto en Pydantic v2
    update_data = user_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        # Usamos setattr para actualizar dinámicamente los campos del objeto de la BD
        setattr(db_user, key, value)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un nuevo token de acceso JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Por defecto, el token expira en 15 minutos si no se especifica.
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    # decodificar el token
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None
    
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True
)

async def send_password_reset_email(email: EmailStr, token: str):
    frontend_reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    html_content = f"""
    <html>
        <body>
            <h2>Recuperación de Contraseña</h2>
            <p>Hola,</p>
            <p>Has solicitado restablecer tu contraseña. Haz clic en el siguiente enlace para continuar:</p>
            <p><a href="{frontend_reset_url}">Restablecer Contraseña</a></p>
            <p>Este enlace expirará en 15 minutos.</p>
            <p>Si no solicitaste esto, por favor ignora este correo.</p>
        </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Recuperación de Contraseña - DigiPath",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)