from decimal import Decimal
from datetime import timedelta

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from api.crud_factory import create_crud_router
from api.dependencies import get_session, get_transferencia_service
from api.schemas import (
    ClienteCreate, ClienteOut,
    CuentaCreate, CuentaOut,
    TransaccionCreate, TransaccionOut,
    TransferenciaRequest, TransferenciaResponse,
    Token, LoginRequest,
)
from api.security import (
    create_access_token,
    hash_password,
    verify_password,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from core.models import Cliente, Cuenta, Transaccion
from core.services import TransferenciaService

app = FastAPI(title="Banking API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FAKE_USER_DB = {
    "admin": hash_password("admin123"),
}


@app.post("/login", response_model=Token)
def login(data: LoginRequest):
    hashed = FAKE_USER_DB.get(data.username)
    if not hashed or not verify_password(data.password, hashed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    token = create_access_token(
        data={"sub": data.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=token)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(
    create_crud_router(
        model=Cliente,
        schema_in=ClienteCreate,
        schema_out=ClienteOut,
        prefix="/clientes",
        tags=["Clientes"],
    )
)

app.include_router(
    create_crud_router(
        model=Cuenta,
        schema_in=CuentaCreate,
        schema_out=CuentaOut,
        prefix="/cuentas",
        tags=["Cuentas"],
    )
)

app.include_router(
    create_crud_router(
        model=Transaccion,
        schema_in=TransaccionCreate,
        schema_out=TransaccionOut,
        prefix="/transacciones",
        tags=["Transacciones"],
    )
)


@app.post("/transferir", response_model=TransferenciaResponse)
def transferir(
    data: TransferenciaRequest,
    service: TransferenciaService = Depends(get_transferencia_service),
    _: str = Depends(get_current_user),
):
    result = service.transferir(
        num_origen=data.num_origen,
        num_destino=data.num_destino,
        monto=data.monto,
    )
    return TransferenciaResponse(**result)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
