# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-06-16

### Fixed
- `_extract_input_schema` now returns `required: []` instead of `required: null` when no parameters are required, fixing JSON Schema validation error that caused "None is not of type 'array'" in MCP tool calls.

### Added
- Voice assistant script (`scripts/voice_mcp.py`) with speech recognition and text-to-speech for hands-free banking operations.
- LiveKit voice agent (`banking-voice-agent/`) for production-grade voice AI with SSE MCP transport.

## [1.0.0] - 2026-06-15

### Added
- Core domain models: `Cliente`, `Cuenta`, `Transaccion` (SQLAlchemy 2.0)
- Domain exceptions: `ErrorBanco`, `SaldoInsuficiente`, `CuentaNoEncontrada`, `ClienteNoEncontrado`
- Repository interfaces (ABCs): `ClienteRepository`, `CuentaRepository`, `TransaccionRepository`
- SQLAlchemy repository implementations: `SQLAlchemyClienteRepository`, `SQLAlchemyCuentaRepository`, `SQLAlchemyTransaccionRepository`
- Unit of Work pattern: abstract `UnitOfWork` and `SQLAlchemyUnitOfWork`
- Domain service: `TransferenciaService.transferir()` with validation, atomic updates, transaction logging
- FastAPI REST API with dynamic CRUD factory (`create_crud_router()`)
- JWT authentication (`/login` endpoint, Bearer token)
- Pydantic v2 request/response schemas
- Transfer endpoint (`POST /transferir`)
- Health check endpoint (`GET /health`)
- MCP server with SSE transport (port 3000) and stdio support
- Dynamic MCP Tool generation from OpenAPI spec
- Async HTTP client for MCP → API communication
- Docker Compose orchestration (PostgreSQL + API + MCP)
- Alembic migration setup
- 9 unit tests (mocked repositories) + 8 integration tests (SQLite)
- GitHub Actions CI workflow (lint, format check, type check, unit tests, integration tests, build check)
- Coding standards guide (`CODING_STANDARDS.md`)
