# Coding Standards

## Python Version

- Python 3.11+ required.
- Use `str | None` notation (PEP 604), not `Optional[str]`.

## Architecture (Hexagonal + DDD)

```
core/       → Domain layer (pure Python + SQLAlchemy ORM only)
api/        → REST API layer (FastAPI, Pydantic)
mcp_server/ → MCP protocol layer
tests/      → Unit + integration tests
```

- `core/` must NOT import from `api/` or `mcp_server/`.
- `api/` may import from `core/`.
- `mcp_server/` may import from `core/` and call `api/` via HTTP only.

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Modules | `snake_case` | `crud_factory.py` |
| Classes | `PascalCase` | `TransferenciaService` |
| Functions | `snake_case` | `create_crud_router()` |
| Variables | `snake_case` | `num_origen` |
| Constants | `UPPER_SNAKE` | `ACCESS_TOKEN_EXPIRE_MINUTES` |
| Private | `_prefix` | `self._uow` |

## Docstrings

Use Google-style docstrings for all public modules, classes, and methods:

```python
def transferir(self, num_origen: str, num_destino: str, monto: Decimal) -> dict:
    """Brief description of the function.

    Args:
        num_origen: Source account number.
        num_destino: Destination account number.
        monto: Positive amount to transfer.

    Returns:
        dict with status, account numbers, and new balances.

    Raises:
        ValueError: If monto <= 0.
        SaldoInsuficiente: If source has insufficient funds.
    """
```

## Type Annotations

- All function parameters and return values MUST have type hints.
- Use `list[...]` / `dict[...]` / `tuple[...]` (PEP 585), not `List[...]` / `Dict[...]`.
- Exception: abstract base classes in Python 3.11 still use `from typing import List, Optional` for readability.

## Imports Order

1. Standard library (`decimal`, `datetime`, `os`)
2. Third-party (`fastapi`, `sqlalchemy`)
3. Application (`core.`, `api.`, `mcp_server.`)
4. Each group separated by a blank line.

## Testing

- Unit tests: mock all external dependencies (database, HTTP).
- Integration tests: use SQLite `:memory:` database.
- Test file placement: `tests/unit/` or `tests/integration/`.
- Test class names: `Test<Scenario>`.
- Test method names: `test_<what>_<condition>`.
- Use pytest fixtures for setup.

## SOLID Principles

- **Single Responsibility**: Each class has exactly one reason to change.
- **Open/Closed**: Core domain entities are open for extension via new services, closed for modification.
- **Liskov Substitution**: Repository interfaces (ABCs) ensure any implementation is swappable.
- **Interface Segregation**: Repository interfaces are minimal (only needed methods).
- **Dependency Inversion**: Core depends on abstractions (ABCs), not on SQLAlchemy directly.

## Code Style

- Line length: 100 characters max.
- Indentation: 4 spaces (no tabs).
- Blank line at end of file.
- No trailing whitespace.
- Use single quotes for strings, double quotes for docstrings.
