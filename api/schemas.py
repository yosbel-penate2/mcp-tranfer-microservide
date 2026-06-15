from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field


class ClienteCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)
    email: EmailStr


class ClienteOut(BaseModel):
    id: int
    nombre: str
    email: str

    model_config = {"from_attributes": True}


class CuentaCreate(BaseModel):
    numero: str = Field(..., min_length=1, max_length=50)
    cliente_id: int
    saldo: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=2)


class CuentaOut(BaseModel):
    id: int
    numero: str
    saldo: Decimal
    cliente_id: int

    model_config = {"from_attributes": True}


class TransaccionCreate(BaseModel):
    monto: Decimal = Field(..., max_digits=10, decimal_places=2, gt=0)
    cuenta_origen_id: int
    cuenta_destino_id: int


class TransaccionOut(BaseModel):
    id: int
    monto: Decimal
    fecha: datetime
    cuenta_origen_id: int
    cuenta_destino_id: int

    model_config = {"from_attributes": True}


class TransferenciaRequest(BaseModel):
    num_origen: str
    num_destino: str
    monto: Decimal = Field(..., gt=0)


class TransferenciaResponse(BaseModel):
    status: str
    origen: str = Field(..., serialization_alias="from")
    to: str
    amount: str
    new_balance_origen: str
    new_balance_destino: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str
