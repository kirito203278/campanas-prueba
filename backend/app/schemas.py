import datetime as dt

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    nombre: str
    username: str
    rol: str
    solo_lectura: bool
    activo: bool
    primer_ingreso: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class CreateCMRequest(BaseModel):
    nombre: str = Field(min_length=1)
    apellido: str | None = None


class CreateAdminRequest(BaseModel):
    nombre: str = Field(min_length=1)
    apellido: str | None = None
    solo_lectura: bool = False


class CreatedCredentialsResponse(BaseModel):
    """Contraseña en texto plano, entregada UNA sola vez (especificación,
    sección 2). El frontend la muestra con botón de copiar y no vuelve a
    pedirse al backend."""
    id: int
    nombre: str
    username: str
    password: str
    rol: str
    solo_lectura: bool = False


class ResetPasswordResponse(BaseModel):
    id: int
    username: str
    password: str


class UsuarioListItem(BaseModel):
    id: int
    nombre: str
    username: str
    rol: str
    solo_lectura: bool
    activo: bool
    creado_en: dt.datetime

    class Config:
        from_attributes = True
