"""Abstract repository interfaces (ports) for the domain layer.

Defines the contracts that infrastructure implementations must fulfill,
following the hexagonal architecture pattern (ports & adapters).
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from core.models import Cliente, Cuenta, Transaccion


class ClienteRepository(ABC):
    """Repository interface for Cliente persistence."""

    @abstractmethod
    def agregar(self, cliente: Cliente) -> Cliente:
        """Persist a new client.

        Args:
            cliente: Transient Cliente instance (without id).

        Returns:
            The persisted Cliente with generated id.
        """
        ...

    @abstractmethod
    def obtener_por_id(self, cliente_id: int) -> Optional[Cliente]:
        """Retrieve a client by primary key.

        Args:
            cliente_id: The client's database ID.

        Returns:
            Cliente if found, None otherwise.
        """
        ...

    @abstractmethod
    def listar(self, skip: int = 0, limit: int = 100) -> List[Cliente]:
        """List clients with pagination.

        Args:
            skip: Number of records to skip.
            limit: Maximum records to return.

        Returns:
            List of Cliente instances.
        """
        ...

    @abstractmethod
    def eliminar(self, cliente_id: int) -> None:
        """Delete a client by ID.

        Args:
            cliente_id: The client's database ID.
        """
        ...


class CuentaRepository(ABC):
    """Repository interface for Cuenta persistence."""

    @abstractmethod
    def agregar(self, cuenta: Cuenta) -> Cuenta:
        """Persist a new account.

        Args:
            cuenta: Transient Cuenta instance (without id).

        Returns:
            The persisted Cuenta with generated id.
        """
        ...

    @abstractmethod
    def obtener_por_numero(self, numero: str) -> Optional[Cuenta]:
        """Find an account by its unique number.

        Args:
            numero: Account number (business key).

        Returns:
            Cuenta if found, None otherwise.
        """
        ...

    @abstractmethod
    def listar_por_cliente(self, cliente_id: int) -> List[Cuenta]:
        """List all accounts belonging to a client.

        Args:
            cliente_id: The client's database ID.

        Returns:
            List of Cuenta instances.
        """
        ...


class TransaccionRepository(ABC):
    """Repository interface for Transaccion persistence."""

    @abstractmethod
    def registrar(self, transaccion: Transaccion) -> Transaccion:
        """Persist a new transaction record.

        Args:
            transaccion: Transient Transaccion instance.

        Returns:
            The persisted Transaccion with generated id.
        """
        ...

    @abstractmethod
    def historial_cuenta(
        self, cuenta_id: int, skip: int = 0, limit: int = 100
    ) -> List[Transaccion]:
        """Get all transactions involving a specific account.

        Returns both outgoing and incoming transactions
        ordered by creation date (newest first).

        Args:
            cuenta_id: Account database ID.
            skip: Number of records to skip.
            limit: Maximum records to return.

        Returns:
            List of Transaccion instances.
        """
        ...
