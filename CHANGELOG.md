# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-06-16

### Added
- **Barge-in**: voice assistant stops speaking immediately when the user interrupts, capturing the interruption speech and using it as the next command.
- `dynamic_energy_threshold = False` to prevent TTS speaker feedback from raising the microphone threshold above the user's voice level.
- Barge-in ignore logic: when the interruption contains only exit keywords ("stop"/"quit"/"exit"), it is treated as an interruption intent — the assistant stops speaking and waits for the real command instead of exiting.

### Changed
- `speak_with_bargein()` refactored to single-thread using `startLoop(False)` + `iterate()` — eliminates COM cross-apartment deadlocks when calling `Speak()` on an STA `SpVoice` object from a background thread.
- `transcribe()` extracted as a reusable helper; `listen()` delegates to it.
- Microphone source opened once at startup and reused across the session.
- Voice assistant commands updated to English (see README).
- Barge-in listen timeout increased to 0.3s for better speech detection.

### Fixed
- `pyttsx3` "run loop already started" crash: bypass module-level `_activeEngines` cache by constructing `Engine()` directly instead of calling `pyttsx3.init()`, giving each TTS call a completely fresh SAPI voice with no shared state.
- Barge-in captured audio was discarded (`_`) and the main loop called `listen()` again, but the user had already spoken — causing a "didn't catch that" loop. Fixed by storing the captured audio in `bargein_audio` and transcribing it directly on the next iteration.

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
