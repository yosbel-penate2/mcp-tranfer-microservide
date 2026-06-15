from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional, List

from core.models import Cliente, Cuenta, Transaccion


class ClienteRepository(ABC):

    @abstractmethod
    def agregar(self, cliente: Cliente) -> Cliente:
        ...

    @abstractmethod
    def obtener_por_id(self, cliente_id: int) -> Optional[Cliente]:
        ...

    @abstractmethod
    def listar(self, skip: int = 0, limit: int = 100) -> List[Cliente]:
        ...

    @abstractmethod
    def eliminar(self, cliente_id: int) -> None:
        ...


class CuentaRepository(ABC):

    @abstractmethod
    def agregar(self, cuenta: Cuenta) -> Cuenta:
        ...

    @abstractmethod
    def obtener_por_numero(self, numero: str) -> Optional[Cuenta]:
        ...

    @abstractmethod
    def listar_por_cliente(self, cliente_id: int) -> List[Cuenta]:
        ...


class TransaccionRepository(ABC):

    @abstractmethod
    def registrar(self, transaccion: Transaccion) -> Transaccion:
        ...

    @abstractmethod
    def historial_cuenta(self, cuenta_id: int, skip: int = 0, limit: int = 100) -> List[Transaccion]:
        ...
