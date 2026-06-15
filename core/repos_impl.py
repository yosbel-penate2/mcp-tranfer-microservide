"""SQLAlchemy implementations of repository interfaces (adapters).

Concrete persistence adapters that fulfill the contracts
defined in core/repositories.py using the SQLAlchemy ORM.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from core.models import Cliente, Cuenta, Transaccion
from core.repositories import (
    ClienteRepository,
    CuentaRepository,
    TransaccionRepository,
)


class SQLAlchemyClienteRepository(ClienteRepository):
    """SQLAlchemy adapter for Cliente persistence."""

    def __init__(self, session: Session):
        self.session = session

    def agregar(self, cliente: Cliente) -> Cliente:
        self.session.add(cliente)
        self.session.flush()
        return cliente

    def obtener_por_id(self, cliente_id: int) -> Optional[Cliente]:
        return self.session.get(Cliente, cliente_id)

    def listar(self, skip: int = 0, limit: int = 100) -> List[Cliente]:
        return self.session.query(Cliente).offset(skip).limit(limit).all()

    def eliminar(self, cliente_id: int) -> None:
        cliente = self.session.get(Cliente, cliente_id)
        if cliente:
            self.session.delete(cliente)
            self.session.flush()


class SQLAlchemyCuentaRepository(CuentaRepository):
    """SQLAlchemy adapter for Cuenta persistence."""

    def __init__(self, session: Session):
        self.session = session

    def agregar(self, cuenta: Cuenta) -> Cuenta:
        self.session.add(cuenta)
        self.session.flush()
        return cuenta

    def obtener_por_numero(self, numero: str) -> Optional[Cuenta]:
        return (
            self.session.query(Cuenta)
            .filter(Cuenta.numero == numero)
            .first()
        )

    def listar_por_cliente(self, cliente_id: int) -> List[Cuenta]:
        return (
            self.session.query(Cuenta)
            .filter(Cuenta.cliente_id == cliente_id)
            .all()
        )


class SQLAlchemyTransaccionRepository(TransaccionRepository):
    """SQLAlchemy adapter for Transaccion persistence."""

    def __init__(self, session: Session):
        self.session = session

    def registrar(self, transaccion: Transaccion) -> Transaccion:
        self.session.add(transaccion)
        self.session.flush()
        return transaccion

    def historial_cuenta(
        self, cuenta_id: int, skip: int = 0, limit: int = 100
    ) -> List[Transaccion]:
        return (
            self.session.query(Transaccion)
            .filter(
                (Transaccion.cuenta_origen_id == cuenta_id)
                | (Transaccion.cuenta_destino_id == cuenta_id)
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
