#!/usr/bin/env python
"""Seed script to populate the database with demo data."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.models import Base, Cliente, Cuenta



def main():
    database_url = os.environ.get(
        "DATABASE_URL", "postgresql://user:password@localhost:5432/banking"
    )

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    Base.metadata.create_all(engine)

    session = SessionLocal()
    try:
        if session.query(Cliente).first():
            print("Database already seeded, skipping...")
            return

        clientes = [
            Cliente(nombre="Juan Pérez", email="juan.perez@example.com"),
            Cliente(nombre="María García", email="maria.garcia@example.com"),
            Cliente(nombre="Carlos López", email="carlos.lopez@example.com"),
        ]
        session.add_all(clientes)
        session.commit()

        for cliente in clientes:
            session.refresh(cliente)

        cuentas = [
            Cuenta(numero="0010000001", cliente_id=clientes[0].id, saldo=5000.00),
            Cuenta(numero="0010000002", cliente_id=clientes[0].id, saldo=2500.50),
            Cuenta(numero="0020000001", cliente_id=clientes[1].id, saldo=10000.00),
            Cuenta(numero="0030000001", cliente_id=clientes[2].id, saldo=1500.75),
        ]
        session.add_all(cuentas)
        session.commit()

        print("Database seeded successfully!")
        print(f"Created {len(clientes)} clientes and {len(cuentas)} cuentas")

    finally:
        session.close()


if __name__ == "__main__":
    main()