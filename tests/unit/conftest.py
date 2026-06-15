from decimal import Decimal
from unittest.mock import MagicMock
from typing import Optional, List

import pytest

from core.exceptions import CuentaNoEncontrada, SaldoInsuficiente
from core.models import Cliente, Cuenta, Transaccion
from core.repositories import ClienteRepository, CuentaRepository, TransaccionRepository
from core.services import TransferenciaService
from core.unit_of_work import UnitOfWork


class MockClienteRepository(ClienteRepository):
    def __init__(self):
        self.clientes: dict[int, Cliente] = {}
        self._next_id = 1

    def agregar(self, cliente: Cliente) -> Cliente:
        cliente.id = self._next_id
        self._next_id += 1
        self.clientes[cliente.id] = cliente
        return cliente

    def obtener_por_id(self, cliente_id: int) -> Optional[Cliente]:
        return self.clientes.get(cliente_id)

    def listar(self, skip: int = 0, limit: int = 100) -> List[Cliente]:
        return list(self.clientes.values())[skip:skip + limit]

    def eliminar(self, cliente_id: int) -> None:
        self.clientes.pop(cliente_id, None)


class MockCuentaRepository(CuentaRepository):
    def __init__(self):
        self.cuentas: dict[str, Cuenta] = {}
        self._next_id = 1

    def agregar(self, cuenta: Cuenta) -> Cuenta:
        cuenta.id = self._next_id
        self._next_id += 1
        self.cuentas[cuenta.numero] = cuenta
        return cuenta

    def obtener_por_numero(self, numero: str) -> Optional[Cuenta]:
        return self.cuentas.get(numero)

    def listar_por_cliente(self, cliente_id: int) -> List[Cuenta]:
        return [c for c in self.cuentas.values() if c.cliente_id == cliente_id]


class MockTransaccionRepository(TransaccionRepository):
    def __init__(self):
        self.transacciones: list[Transaccion] = []
        self._next_id = 1

    def registrar(self, transaccion: Transaccion) -> Transaccion:
        transaccion.id = self._next_id
        self._next_id += 1
        self.transacciones.append(transaccion)
        return transaccion

    def historial_cuenta(self, cuenta_id: int, skip: int = 0, limit: int = 100) -> List[Transaccion]:
        relevant = [
            t for t in self.transacciones
            if t.cuenta_origen_id == cuenta_id or t.cuenta_destino_id == cuenta_id
        ]
        return relevant[skip:skip + limit]


class MockUnitOfWork(UnitOfWork):
    def __init__(self):
        self.clientes = MockClienteRepository()
        self.cuentas = MockCuentaRepository()
        self.transacciones = MockTransaccionRepository()
        self.committed = False
        self.rollbacked = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rollbacked = True


@pytest.fixture
def mock_uow():
    return MockUnitOfWork()


@pytest.fixture
def service(mock_uow):
    return TransferenciaService(uow=mock_uow)


@pytest.fixture
def sample_cliente():
    return Cliente(nombre="Juan Pérez", email="juan@example.com")
