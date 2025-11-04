from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel, EmailStr

from app.db.database import get_db
from app.schemas.user_schema import Usuario, UsuarioCreate, Token, UsuarioUpdate
from app.services import auth_service

router = APIRouter()
oauth2_scheme = HTTPBearer()

# ==============================================================================
# FUNCIÓN DE DEPENDENCIA DE SEGURIDAD (MOVIDA A LA PARTE SUPERIOR)
# ==============================================================================
def get_current_user(token_creds: HTTPAuthorizationCredentials = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Decodifica el token Bearer, valida al usuario y devuelve el objeto de usuario de la BD.
    Actúa como el "guardia de seguridad" para los endpoints protegidos.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token_creds:
        raise credentials_exception

    token = token_creds.credentials
    email = auth_service.decode_access_token(token)
    if email is None:
        raise credentials_exception

    user = auth_service.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception

    return user

# ==============================================================================
# ESQUEMAS LOCALES PARA RECUPERACIÓN DE CONTRASEÑA
# ==============================================================================
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

# ==============================================================================
# ENDPOINTS DE AUTENTICACIÓN Y REGISTRO
# ==============================================================================
@router.post("/register", response_model=Usuario, status_code=status.HTTP_201_CREATED)
def register_new_user(user: UsuarioCreate, db: Session = Depends(get_db)):
    if not user.acepta_terminos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe aceptar los términos y condiciones para registrarse."
        )
    existing = auth_service.get_user_by_email(db, user.correo_electronico)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario ya existe")
    return auth_service.create_user(db=db, user=user)

@router.post("/token", response_model=Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = auth_service.get_user_by_email(db, form_data.username)
    if not user or not auth_service.verify_password(form_data.password, user.contrasena_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo o contraseña inválidos")
    access_token_expires = timedelta(minutes=30)
    access_token = auth_service.create_access_token(data={"sub": user.correo_electronico}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

# ==============================================================================
# ENDPOINTS DE GESTIÓN DE PERFIL (/me)
# ==============================================================================
@router.get("/me", response_model=Usuario)
def read_current_user(current_user: Usuario = Depends(get_current_user)):
    """
    Endpoint para que un usuario autenticado obtenga su propia información.
    """
    return current_user

@router.put("/me", response_model=Usuario)
def update_current_user_profile(
    user_update: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Endpoint para que un usuario autenticado actualice su propio perfil (nombre y RUC).
    """
    return auth_service.update_user(db=db, db_user=current_user, user_update=user_update)

# ==============================================================================
# ENDPOINTS DE RECUPERACIÓN DE CONTRASEÑA
# ==============================================================================
@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = auth_service.get_user_by_email(db, email=request.email)
    if user:
        expires_delta = timedelta(minutes=15)
        reset_token = auth_service.create_access_token(
            data={"sub": user.correo_electronico, "scope": "password_reset"}, 
            expires_delta=expires_delta
        )
        await auth_service.send_password_reset_email(email=user.correo_electronico, token=reset_token)
    
    return {"message": "Si el correo electrónico está registrado, recibirás un enlace para restablecer tu contraseña."}

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    email = auth_service.decode_access_token(token=request.token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido o expirado")
    
    user = auth_service.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    user.contrasena_hash = auth_service.get_password_hash(request.new_password)
    db.commit()

    return {"message": "Contraseña actualizada correctamente."}