"""Pydantic v2 schemas for request/response validation.

Defines the API contract for all endpoints including
create/update payloads, response models, authentication DTOs,
and the transfer operation request/response.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class ClienteCreate(BaseModel):
    """Request body for creating a new client."""
    nombre: str = Field(..., min_length=1, max_length=255)
    email: EmailStr


class ClienteOut(BaseModel):
    """Response schema for client data."""
    id: int
    nombre: str
    email: str

    model_config = {"from_attributes": True}


class CuentaCreate(BaseModel):
    """Request body for creating a new account."""
    numero: str = Field(..., min_length=1, max_length=50)
    cliente_id: int
    saldo: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=2)


class CuentaOut(BaseModel):
    """Response schema for account data."""
    id: int
    numero: str
    saldo: Decimal
    cliente_id: int

    model_config = {"from_attributes": True}


class TransaccionCreate(BaseModel):
    """Request body for recording a transaction directly."""
    monto: Decimal = Field(..., max_digits=10, decimal_places=2, gt=0)
    cuenta_origen_id: int
    cuenta_destino_id: int


class TransaccionOut(BaseModel):
    """Response schema for transaction data."""
    id: int
    monto: Decimal
    fecha: datetime
    cuenta_origen_id: int
    cuenta_destino_id: int

    model_config = {"from_attributes": True}


class TransferenciaRequest(BaseModel):
    """Request body for the /transferir endpoint."""
    num_origen: str
    num_destino: str
    monto: Decimal = Field(..., gt=0)


class TransferenciaResponse(BaseModel):
    """Response returned after a successful transfer.

    Note: 'origen' is serialized as 'from' in JSON (Python reserved word).
    """
    status: str
    origen: str = Field(..., serialization_alias="from")
    to: str
    amount: str
    new_balance_origen: str
    new_balance_destino: str


class Token(BaseModel):
    """JWT access token response."""
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Login credentials."""
    username: str
    password: str
