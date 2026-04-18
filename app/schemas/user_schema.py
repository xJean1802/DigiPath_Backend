from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re

# --- Esquema Base para Usuario ---
# Contiene los campos comunes que se comparten entre creación y lectura.
class UsuarioBase(BaseModel):
    correo_electronico: EmailStr
    nombre_empresa: str
    ruc: str = Field(..., pattern=r'^\d{11}$')

# --- Esquema para la Creación de un Usuario (Entrada de la API) ---
# Hereda de UsuarioBase y añade el campo de la contraseña.
class UsuarioCreate(UsuarioBase):
    contrasena: str = Field(..., min_length=8, max_length=72)
    acepta_terminos: bool

    # AÑADIMOS EL VALIDADOR PERSONALIZADO PARA LA CONTRASEÑA
    @field_validator('contrasena')
    @classmethod
    def validar_fortaleza_contrasena(cls, v: str) -> str:
        patron = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&.])[A-Za-z\d@$!%*?&.]+$'
        # Usamos re.match de Python puro
        if not re.match(patron, v):
            raise ValueError('La contraseña debe tener al menos 8 caracteres, incluir una mayúscula, una minúscula, un número y un símbolo especial.')
        return v
     
    
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
    ruc: Optional[str] = Field(None, pattern=r'^\d{11}$')