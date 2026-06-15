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
    e = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(e)
    yield e
    Base.metadata.drop_all(e)


@pytest.fixture
def session(engine):
    SessionLocal = sessionmaker(bind=engine)
    s = SessionLocal()
    yield s
    s.rollback()
    s.close()


@pytest.fixture
def cliente_repo(session):
    return SQLAlchemyClienteRepository(session)


@pytest.fixture
def cuenta_repo(session):
    return SQLAlchemyCuentaRepository(session)


@pytest.fixture
def transaccion_repo(session):
    return SQLAlchemyTransaccionRepository(session)


@pytest.fixture
def sample_cliente(cliente_repo):
    c = Cliente(nombre="Test User", email="test@example.com")
    cliente_repo.agregar(c)
    return c


@pytest.fixture
def sample_cuentas(sample_cliente, cuenta_repo):
    origen = Cuenta(numero="C001", saldo=Decimal("1000.00"), cliente_id=sample_cliente.id)
    destino = Cuenta(numero="C002", saldo=Decimal("500.00"), cliente_id=sample_cliente.id)
    cuenta_repo.agregar(origen)
    cuenta_repo.agregar(destino)
    return origen, destino
