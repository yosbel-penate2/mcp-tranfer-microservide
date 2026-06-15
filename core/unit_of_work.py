from abc import ABC, abstractmethod
from typing import Optional

from core.repositories import (
    ClienteRepository,
    CuentaRepository,
    TransaccionRepository,
)


class UnitOfWork(ABC):

    clientes: ClienteRepository
    cuentas: CuentaRepository
    transacciones: TransaccionRepository

    @abstractmethod
    def commit(self) -> None:
        ...

    @abstractmethod
    def rollback(self) -> None:
        ...

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
