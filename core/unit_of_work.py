"""Unit of Work abstraction for atomic transactions.

Ensures that all repository operations within a transfer
either commit together or roll back together, maintaining
data consistency.
"""

from abc import ABC, abstractmethod
from typing import Optional

from core.repositories import (
    ClienteRepository,
    CuentaRepository,
    TransaccionRepository,
)


class UnitOfWork(ABC):
    """Abstract Unit of Work for atomic banking operations.

    Provides a context manager that commits on success
    or rolls back on any exception.

    Attributes:
        clientes: Repository for Cliente operations.
        cuentas: Repository for Cuenta operations.
        transacciones: Repository for Transaccion operations.
    """

    clientes: ClienteRepository
    cuentas: CuentaRepository
    transacciones: TransaccionRepository

    @abstractmethod
    def commit(self) -> None:
        """Persist all changes made during this unit of work."""
        ...

    @abstractmethod
    def rollback(self) -> None:
        """Discard all changes made during this unit of work."""
        ...

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> None:
        """Auto-commit on success, auto-rollback on exception."""
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
