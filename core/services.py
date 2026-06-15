from decimal import Decimal

from core.exceptions import CuentaNoEncontrada, SaldoInsuficiente
from core.models import Transaccion
from core.unit_of_work import UnitOfWork


class TransferenciaService:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def transferir(self, num_origen: str, num_destino: str, monto: Decimal) -> dict:
        if monto <= Decimal("0"):
            raise ValueError("El monto debe ser positivo")

        with self._uow:
            origen = self._uow.cuentas.obtener_por_numero(num_origen)
            if origen is None:
                raise CuentaNoEncontrada(num_origen)

            destino = self._uow.cuentas.obtener_por_numero(num_destino)
            if destino is None:
                raise CuentaNoEncontrada(num_destino)

            if not origen.puede_retirar(monto):
                raise SaldoInsuficiente(
                    origen.numero, str(origen.saldo), str(monto)
                )

            origen.saldo -= monto
            destino.saldo += monto

            transaccion = Transaccion(
                monto=monto,
                cuenta_origen_id=origen.id,
                cuenta_destino_id=destino.id,
            )
            self._uow.transacciones.registrar(transaccion)

        return {
            "status": "ok",
            "origen": num_origen,
            "to": num_destino,
            "amount": str(monto),
            "new_balance_origen": str(origen.saldo),
            "new_balance_destino": str(destino.saldo),
        }
