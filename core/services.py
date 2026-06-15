"""Domain service for money transfers.

Contains the core business logic (transferir) that orchestrates
validation, balance updates, transaction logging, and persistence
via the Unit of Work pattern.
"""

from decimal import Decimal

from core.exceptions import CuentaNoEncontrada, SaldoInsuficiente
from core.models import Transaccion
from core.unit_of_work import UnitOfWork


class TransferenciaService:
    """Orchestrates money transfers between accounts.

    Uses Unit of Work for atomic persistence — on success it commits,
    on any error it rolls back the entire operation.

    Args:
        uow: A UnitOfWork instance providing account and transaction repositories.
    """

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def transferir(self, num_origen: str, num_destino: str, monto: Decimal) -> dict:
        """Execute a transfer between two accounts.

        Validation steps:
            1. Amount must be positive.
            2. Source account must exist.
            3. Destination account must exist.
            4. Source must have sufficient balance.

        On success, debits source, credits destination, logs a Transaccion,
        and commits. On any error, rolls back the Unit of Work.

        Args:
            num_origen: Account number of the source.
            num_destino: Account number of the destination.
            monto: Positive amount to transfer.

        Returns:
            dict with status, account numbers, amount, and new balances.

        Raises:
            ValueError: If monto <= 0.
            CuentaNoEncontrada: If either account does not exist.
            SaldoInsuficiente: If source has insufficient funds.
        """
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
