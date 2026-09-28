from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    nombre: str
    username: str
    maquinas_asignadas: str


class UsuarioCreate(BaseModel):
    nombre: str
    cedula: str
    username: str
    password: str
    rol: str = "operario"
    maquinas_asignadas: str = ""


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    cedula: str
    username: str
    rol: str
    maquinas_asignadas: str
    activo: str

    class Config:
        from_attributes = True


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    cedula: Optional[str] = None
    maquinas_asignadas: Optional[str] = None
    activo: Optional[str] = None
    password: Optional[str] = None
