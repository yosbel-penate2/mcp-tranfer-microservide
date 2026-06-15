from decimal import Decimal

import pytest

from core.exceptions import CuentaNoEncontrada, SaldoInsuficiente
from core.models import Cuenta, Cliente


class TestTransferenciaExitosa:
    def test_transfiere_saldo_correctamente(self, service, mock_uow):
        cliente = Cliente(nombre="Alice", email="alice@test.com")
        mock_uow.clientes.agregar(cliente)
        origen = Cuenta(numero="001", saldo=Decimal("1000.00"), cliente_id=cliente.id)
        destino = Cuenta(numero="002", saldo=Decimal("500.00"), cliente_id=cliente.id)
        mock_uow.cuentas.agregar(origen)
        mock_uow.cuentas.agregar(destino)

        service.transferir(origen.numero, destino.numero, Decimal("300.00"))

        assert origen.saldo == Decimal("700.00")
        assert destino.saldo == Decimal("800.00")

    def test_llama_commit_despues_de_transferir(self, service, mock_uow):
        cliente = Cliente(nombre="Bob", email="bob@test.com")
        mock_uow.clientes.agregar(cliente)
        origen = Cuenta(numero="003", saldo=Decimal("500.00"), cliente_id=cliente.id)
        destino = Cuenta(numero="004", saldo=Decimal("0.00"), cliente_id=cliente.id)
        mock_uow.cuentas.agregar(origen)
        mock_uow.cuentas.agregar(destino)

        service.transferir(origen.numero, destino.numero, Decimal("100.00"))

        assert mock_uow.committed is True

    def test_registra_transaccion(self, service, mock_uow):
        cliente = Cliente(nombre="Carol", email="carol@test.com")
        mock_uow.clientes.agregar(cliente)
        origen = Cuenta(numero="005", saldo=Decimal("1000.00"), cliente_id=cliente.id)
        destino = Cuenta(numero="006", saldo=Decimal("0.00"), cliente_id=cliente.id)
        mock_uow.cuentas.agregar(origen)
        mock_uow.cuentas.agregar(destino)

        service.transferir(origen.numero, destino.numero, Decimal("250.00"))

        assert len(mock_uow.transacciones.transacciones) == 1
        txn = mock_uow.transacciones.transacciones[0]
        assert txn.monto == Decimal("250.00")
        assert txn.cuenta_origen_id == origen.id
        assert txn.cuenta_destino_id == destino.id


class TestSaldoInsuficiente:
    def test_lanza_error_si_saldo_insuficiente(self, service, mock_uow):
        cliente = Cliente(nombre="Dave", email="dave@test.com")
        mock_uow.clientes.agregar(cliente)
        origen = Cuenta(numero="007", saldo=Decimal("100.00"), cliente_id=cliente.id)
        destino = Cuenta(numero="008", saldo=Decimal("0.00"), cliente_id=cliente.id)
        mock_uow.cuentas.agregar(origen)
        mock_uow.cuentas.agregar(destino)

        with pytest.raises(SaldoInsuficiente):
            service.transferir(origen.numero, destino.numero, Decimal("200.00"))

        assert origen.saldo == Decimal("100.00")
        assert destino.saldo == Decimal("0.00")
        assert mock_uow.rollbacked is True


class TestCuentaNoEncontrada:
    def test_lanza_error_si_origen_no_existe(self, service, mock_uow):
        with pytest.raises(CuentaNoEncontrada) as exc:
            service.transferir("999", "001", Decimal("100.00"))
        assert "999" in str(exc.value)
        assert mock_uow.rollbacked is True

    def test_lanza_error_si_destino_no_existe(self, service, mock_uow):
        cliente = Cliente(nombre="Eve", email="eve@test.com")
        mock_uow.clientes.agregar(cliente)
        origen = Cuenta(numero="009", saldo=Decimal("500.00"), cliente_id=cliente.id)
        mock_uow.cuentas.agregar(origen)

        with pytest.raises(CuentaNoEncontrada) as exc:
            service.transferir(origen.numero, "999", Decimal("50.00"))
        assert "999" in str(exc.value)
        assert mock_uow.rollbacked is True


class TestPuedeRetirar:
    def test_puede_retirar_cuando_saldo_suficiente(self):
        cuenta = Cuenta(numero="010", saldo=Decimal("500.00"), cliente_id=1)
        assert cuenta.puede_retirar(Decimal("300.00")) is True

    def test_no_puede_retirar_cuando_saldo_insuficiente(self):
        cuenta = Cuenta(numero="011", saldo=Decimal("100.00"), cliente_id=1)
        assert cuenta.puede_retirar(Decimal("200.00")) is False

    def test_puede_retirar_con_saldo_exacto(self):
        cuenta = Cuenta(numero="012", saldo=Decimal("100.00"), cliente_id=1)
        assert cuenta.puede_retirar(Decimal("100.00")) is True
