from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# --- Esquema Base para Usuario ---
# Contiene los campos comunes que se comparten entre creación y lectura.
class UsuarioBase(BaseModel):
    correo_electronico: EmailStr
    nombre_empresa: str
    ruc: str

# --- Esquema para la Creación de un Usuario (Entrada de la API) ---
# Hereda de UsuarioBase y añade el campo de la contraseña.
class UsuarioCreate(UsuarioBase):
    contrasena: str = Field(
        ..., 
        min_length=8,
        max_length=72
    )
    # AÑADE ESTA LÍNEA
    acepta_terminos: bool
     
    
# --- Esquema para la Lectura de un Usuario (Salida de la API) ---
# Hereda de UsuarioBase y añade los campos que queremos mostrar al exterior.
# No incluye la contraseña por seguridad.
class Usuario(UsuarioBase):
    id_usuario: int
    
    class Config:
        # Pydantic v2
        from_attributes = True
        # Pydantic v1
        # orm_mode = True

# --- Esquema para el Token de Autenticación ---
# Define la estructura de la respuesta que se envía al iniciar sesión.
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    correo_electronico: str | None = None

# --- Esquema para Actualizar un Usuario (Entrada de la API) ---
class UsuarioUpdate(BaseModel):
    nombre_empresa: Optional[str] = None
    ruc: Optional[str] = None