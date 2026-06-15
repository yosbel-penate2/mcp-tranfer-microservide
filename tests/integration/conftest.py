"""Test fixtures for integration tests with SQLite in-memory database.

Provides real SQLAlchemy repository instances backed by
an in-memory SQLite database for verifying persistence behavior.
"""

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.models import Base, Cliente, Cuenta
from core.repos_impl import (
    SQLAlchemyClienteRepository,
    SQLAlchemyCuentaRepository,
    SQLAlchemyTransaccionRepository,
)


@pytest.fixture
def engine():
    """Fixture: creates an in-memory SQLite database with all tables."""
    e = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(e)
    yield e
    Base.metadata.drop_all(e)


@pytest.fixture
def session(engine):
    """Fixture: yields a SQLAlchemy session, rolled back after each test."""
    SessionLocal = sessionmaker(bind=engine)
    s = SessionLocal()
    yield s
    s.rollback()
    s.close()


@pytest.fixture
def cliente_repo(session):
    """Fixture: SQLAlchemyClienteRepository wired to the test session."""
    return SQLAlchemyClienteRepository(session)


@pytest.fixture
def cuenta_repo(session):
    """Fixture: SQLAlchemyCuentaRepository wired to the test session."""
    return SQLAlchemyCuentaRepository(session)


@pytest.fixture
def transaccion_repo(session):
    """Fixture: SQLAlchemyTransaccionRepository wired to the test session."""
    return SQLAlchemyTransaccionRepository(session)


@pytest.fixture
def sample_cliente(cliente_repo):
    """Fixture: persists and returns a sample Cliente."""
    c = Cliente(nombre="Test User", email="test@example.com")
    cliente_repo.agregar(c)
    return c


@pytest.fixture
def sample_cuentas(sample_cliente, cuenta_repo):
    """Fixture: persists and returns two sample Cuentas for a client."""
    origen = Cuenta(numero="C001", saldo=Decimal("1000.00"), cliente_id=sample_cliente.id)
    destino = Cuenta(numero="C002", saldo=Decimal("500.00"), cliente_id=sample_cliente.id)
    cuenta_repo.agregar(origen)
    cuenta_repo.agregar(destino)
    return origen, destino
