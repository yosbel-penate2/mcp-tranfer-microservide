class ErrorBanco(Exception):
    """Base exception for all banking domain errors.

    All custom exceptions in the domain layer inherit from this,
    allowing the API layer to catch and map them to HTTP responses.
    """


class SaldoInsuficiente(ErrorBanco):
    """Raised when a source account lacks sufficient funds for a transfer.

    Attributes:
        cuenta_numero: The account that lacks funds.
        saldo_actual: Current balance (as string for display).
        monto_solicitado: Amount that was requested.
    """

    def __init__(self, cuenta_numero: str, saldo_actual: str, monto_solicitado: str):
        self.cuenta_numero = cuenta_numero
        self.saldo_actual = saldo_actual
        self.monto_solicitado = monto_solicitado
        super().__init__(
            f"Saldo insuficiente en cuenta {cuenta_numero}: "
            f"saldo={saldo_actual}, requerido={monto_solicitado}"
        )


class CuentaNoEncontrada(ErrorBanco):
    """Raised when a requested account does not exist.

    Attributes:
        numero: The account number that was not found.
    """

    def __init__(self, numero: str):
        self.numero = numero
        super().__init__(f"Cuenta no encontrada: {numero}")


class ClienteNoEncontrado(ErrorBanco):
    """Raised when a requested client does not exist.

    Attributes:
        cliente_id: The ID of the client that was not found.
    """

    def __init__(self, cliente_id: int):
        self.cliente_id = cliente_id
        super().__init__(f"Cliente no encontrado: {cliente_id}")
