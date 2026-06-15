"""Integration tests for SQLAlchemy repository implementations.

Tests each repository method against a real SQLite in-memory database,
including constraint validation (unique email, unique account number).
"""

from decimal import Decimal

import pytest
from sqlalchemy import exc as sa_exc

from core.models import Cliente, Cuenta, Transaccion


class TestClienteRepository:
    """Integration tests for SQLAlchemyClienteRepository."""

    def test_agregar_y_obtener_por_id(self, cliente_repo):
        cliente = Cliente(nombre="Alice", email="alice@test.com")
        saved = cliente_repo.agregar(cliente)
        assert saved.id is not None
        fetched = cliente_repo.obtener_por_id(saved.id)
        assert fetched is not None
        assert fetched.nombre == "Alice"
        assert fetched.email == "alice@test.com"

    def test_listar_clientes(self, cliente_repo):
        cliente_repo.agregar(Cliente(nombre="A", email="a@test.com"))
        cliente_repo.agregar(Cliente(nombre="B", email="b@test.com"))
        lista = cliente_repo.listar()
        assert len(lista) == 2

    def test_eliminar_cliente(self, sample_cliente, cliente_repo):
        cliente_repo.eliminar(sample_cliente.id)
        assert cliente_repo.obtener_por_id(sample_cliente.id) is None

    def test_email_unique_constraint(self, session, cliente_repo):
        cliente_repo.agregar(Cliente(nombre="A", email="dup@test.com"))
        session.flush()
        with pytest.raises(sa_exc.IntegrityError):
            cliente_repo.agregar(Cliente(nombre="B", email="dup@test.com"))
            session.flush()


class TestCuentaRepository:
    """Integration tests for SQLAlchemyCuentaRepository."""

    def test_agregar_y_obtener_por_numero(self, cuenta_repo, sample_cliente):
        cuenta = Cuenta(
            numero="X001", saldo=Decimal("100.00"), cliente_id=sample_cliente.id
        )
        cuenta_repo.agregar(cuenta)
        fetched = cuenta_repo.obtener_por_numero("X001")
        assert fetched is not None
        assert fetched.saldo == Decimal("100.00")

    def test_listar_por_cliente(self, sample_cliente, cuenta_repo):
        c1 = Cuenta(numero="L01", saldo=Decimal("0"), cliente_id=sample_cliente.id)
        c2 = Cuenta(numero="L02", saldo=Decimal("0"), cliente_id=sample_cliente.id)
        cuenta_repo.agregar(c1)
        cuenta_repo.agregar(c2)
        cuentas = cuenta_repo.listar_por_cliente(sample_cliente.id)
        assert len(cuentas) == 2

    def test_numero_unique(self, session, cuenta_repo, sample_cliente):
        cuenta_repo.agregar(
            Cuenta(numero="UNIQ", saldo=Decimal("0"), cliente_id=sample_cliente.id)
        )
        session.flush()
        with pytest.raises(sa_exc.IntegrityError):
            cuenta_repo.agregar(
                Cuenta(numero="UNIQ", saldo=Decimal("0"), cliente_id=sample_cliente.id)
            )
            session.flush()


class TestTransaccionRepository:
    """Integration tests for SQLAlchemyTransaccionRepository."""

    def test_registrar_y_historial(self, transaccion_repo, sample_cuentas):
        origen, destino = sample_cuentas
        txn = Transaccion(
            monto=Decimal("200.00"),
            cuenta_origen_id=origen.id,
            cuenta_destino_id=destino.id,
        )
        transaccion_repo.registrar(txn)
        historial = transaccion_repo.historial_cuenta(origen.id)
        assert len(historial) == 1
        assert historial[0].monto == Decimal("200.00")
