"""SQLAlchemy ORM models for the banking domain.

Defines the database schema and relationships for
Cliente (client), Cuenta (account), and Transaccion (transaction).
"""

from decimal import Decimal
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, ForeignKey,
    UniqueConstraint, func, create_engine
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


class Cliente(Base):
    """Bank client (aggregate root).

    Attributes:
        id: Auto-generated primary key.
        nombre: Full name of the client.
        email: Unique email address (used as login identifier).
        cuentas: One-to-many relationship to Cuenta.
    """
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    cuentas = relationship("Cuenta", back_populates="cliente", cascade="all, delete-orphan")


class Cuenta(Base):
    """Bank account belonging to a client.

    Attributes:
        id: Auto-generated primary key.
        numero: Unique account number (business identifier).
        saldo: Current balance (Numeric(10,2) for precision).
        cliente_id: Foreign key to the owning Cliente.
    """
    __tablename__ = "cuentas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    numero: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    saldo: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)

    cliente = relationship("Cliente", back_populates="cuentas")
    transacciones_origen = relationship(
        "Transaccion", foreign_keys="Transaccion.cuenta_origen_id",
        back_populates="cuenta_origen", cascade="all, delete-orphan"
    )
    transacciones_destino = relationship(
        "Transaccion", foreign_keys="Transaccion.cuenta_destino_id",
        back_populates="cuenta_destino", cascade="all, delete-orphan"
    )

    def puede_retirar(self, monto: Decimal) -> bool:
        """Check if account has sufficient funds.

        Args:
            monto: Amount to withdraw.

        Returns:
            True if current balance >= monto, False otherwise.
        """
        return self.saldo >= monto

    def __repr__(self) -> str:
        return f"<Cuenta(numero={self.numero}, saldo={self.saldo})>"


class Transaccion(Base):
    """Record of a money transfer between two accounts.

    Attributes:
        id: Auto-generated primary key.
        monto: Transfer amount (Numeric(10,2)).
        fecha: Timestamp of the transaction (server default now()).
        cuenta_origen_id: FK to the source Cuenta.
        cuenta_destino_id: FK to the destination Cuenta.
    """
    __tablename__ = "transacciones"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    cuenta_origen_id: Mapped[int] = mapped_column(
        ForeignKey("cuentas.id"), nullable=False
    )
    cuenta_destino_id: Mapped[int] = mapped_column(
        ForeignKey("cuentas.id"), nullable=False
    )

    cuenta_origen = relationship(
        "Cuenta", foreign_keys=[cuenta_origen_id],
        back_populates="transacciones_origen"
    )
    cuenta_destino = relationship(
        "Cuenta", foreign_keys=[cuenta_destino_id],
        back_populates="transacciones_destino"
    )
