import os
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.models import Base
from core.repos_impl import (
    SQLAlchemyClienteRepository,
    SQLAlchemyCuentaRepository,
    SQLAlchemyTransaccionRepository,
)
from core.services import TransferenciaService
from core.unit_of_work import UnitOfWork

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@db:5432/banking")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session() -> AsyncGenerator[Session, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session: Session):
        self.session = session
        self.clientes = SQLAlchemyClienteRepository(session)
        self.cuentas = SQLAlchemyCuentaRepository(session)
        self.transacciones = SQLAlchemyTransaccionRepository(session)

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()


def get_uow(session: Session = Depends(get_session)) -> SQLAlchemyUnitOfWork:
    return SQLAlchemyUnitOfWork(session)


def get_transferencia_service(
    uow: SQLAlchemyUnitOfWork = Depends(get_uow),
) -> TransferenciaService:
    return TransferenciaService(uow=uow)
