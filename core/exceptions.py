class ErrorBanco(Exception):
    """Base exception for all banking domain errors."""


class SaldoInsuficiente(ErrorBanco):
    def __init__(self, cuenta_numero: str, saldo_actual: str, monto_solicitado: str):
        self.cuenta_numero = cuenta_numero
        self.saldo_actual = saldo_actual
        self.monto_solicitado = monto_solicitado
        super().__init__(
            f"Saldo insuficiente en cuenta {cuenta_numero}: "
            f"saldo={saldo_actual}, requerido={monto_solicitado}"
        )


class CuentaNoEncontrada(ErrorBanco):
    def __init__(self, numero: str):
        self.numero = numero
        super().__init__(f"Cuenta no encontrada: {numero}")


class ClienteNoEncontrado(ErrorBanco):
    def __init__(self, cliente_id: int):
        self.cliente_id = cliente_id
        super().__init__(f"Cliente no encontrado: {cliente_id}")
