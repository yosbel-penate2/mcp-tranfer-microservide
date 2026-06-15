from decimal import Decimal
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, ForeignKey,
    UniqueConstraint, func, create_engine
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    cuentas = relationship("Cuenta", back_populates="cliente", cascade="all, delete-orphan")


class Cuenta(Base):
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
        return self.saldo >= monto

    def __repr__(self) -> str:
        return f"<Cuenta(numero={self.numero}, saldo={self.saldo})>"


class Transaccion(Base):
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
