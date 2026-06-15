# Banking MCP - Sistema Bancario Multi-Capa

Sistema bancario con arquitectura hexagonal, DDD táctico, API REST dinámica y servidor MCP.

## Arquitectura

```mermaid
graph TD
    ClienteChatGPT[Cliente ChatGPT] --> ServidorMCP[Servidor MCP<br/>mcp_server/]
    ServidorMCP --> APIREST[API REST FastAPI<br/>api/]
    APIREST --> ServicioLogica[Servicio de Lógica<br/>core/]
    ServicioLogica --> BaseDatos[(PostgreSQL<br/>db/)]
```

```mermaid
erDiagram
    Cliente {
        int id PK
        string nombre
        string email UK
    }
    Cuenta {
        int id PK
        string numero UK
        decimal saldo
        int cliente_id FK
    }
    Transaccion {
        int id PK
        decimal monto
        datetime fecha
        int cuenta_origen_id FK
        int cuenta_destino_id FK
    }
    Cliente ||--o{ Cuenta : tiene
    Cuenta ||--o{ Transaccion : origen
    Cuenta ||--o{ Transaccion : destino
```

## Estructura del Proyecto

```
├── core/                  # Lógica de dominio (Hexagonal + DDD)
│   ├── models.py          # Modelos SQLAlchemy (Cliente, Cuenta, Transaccion)
│   ├── exceptions.py      # Excepciones de dominio
│   ├── repositories.py    # Interfaces abstractas (ABC)
│   ├── repos_impl.py      # Implementaciones SQLAlchemy
│   ├── unit_of_work.py    # Unit of Work (ABC)
│   └── services.py        # Servicio de transferencias
├── api/                   # API REST FastAPI
│   ├── main.py            # Punto de entrada FastAPI
│   ├── crud_factory.py    # Generador dinámico de CRUD
│   ├── schemas.py         # Esquemas Pydantic v2
│   ├── security.py        # JWT + autenticación
│   └── dependencies.py    # Inyección de dependencias
├── mcp_server/            # Servidor MCP
│   ├── server.py          # Servidor MCP (stdio)
│   ├── generator.py       # Generación dinámica de Tools desde OpenAPI
│   └── api_client.py      # Cliente HTTP asíncrono
├── tests/
│   ├── unit/              # Pruebas unitarias (TDD)
│   │   ├── conftest.py
│   │   └── test_transferencia_service.py
│   └── integration/       # Pruebas de integración
│       ├── conftest.py
│       └── test_repos.py
├── alembic/               # Migraciones de base de datos
├── Dockerfile.api         # Docker para API
├── Dockerfile.mcp         # Docker para MCP
├── docker-compose.yml     # Orquestación de servicios
├── alembic.ini            # Configuración de Alembic
└── requirements.txt       # Dependencias Python
```

## Requisitos

- Python 3.11+
- Docker y Docker Compose
- pip

## Instalación y Desarrollo

### 1. Local (sin Docker)

```bash
# Clonar y entrar al proyecto
git clone https://github.com/yosbel-penate2/mcp-tranfer-microservide.git
cd mcp-tranfer-microservide

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos (usa SQLite por defecto si no hay DATABASE_URL)
set DATABASE_URL=sqlite:///./banking.db  # Windows
export DATABASE_URL=sqlite:///./banking.db  # Linux/macOS

# Iniciar API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Docker (producción)

```bash
# Construir e iniciar todos los servicios
docker-compose up --build -d

# Verificar que los 3 contenedores estén saludables
docker-compose ps

# Ver logs
docker-compose logs -f api
```

### Comandos Docker Útiles

| Comando | Descripción |
|---------|-------------|
| `docker-compose up -d` | Iniciar servicios en segundo plano |
| `docker-compose down` | Detener y limpiar servicios |
| `docker-compose logs -f api` | Ver logs de la API en tiempo real |
| `docker-compose logs -f mcp` | Ver logs del MCP server |
| `docker-compose build --no-cache api` | Reconstruir imagen de la API sin caché |

## Uso de la API

### Autenticación

```bash
# Obtener token JWT
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Respuesta:
# {"access_token":"eyJ...","token_type":"bearer"}
```

### CRUD de Clientes

```bash
# Listar todos los clientes
curl http://localhost:8000/clientes/ \
  -H "Authorization: Bearer <token>"

# Crear un cliente
curl -X POST http://localhost:8000/clientes/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Juan Pérez","email":"juan@example.com"}'

# Obtener cliente por ID
curl http://localhost:8000/clientes/1 \
  -H "Authorization: Bearer <token>"
```

### Transferencia entre Cuentas

```bash
# Crear cuentas primero
curl -X POST http://localhost:8000/cuentas/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"numero":"C001","cliente_id":1,"saldo":1000.00}'

curl -X POST http://localhost:8000/cuentas/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"numero":"C002","cliente_id":1,"saldo":500.00}'

# Transferir dinero
curl -X POST http://localhost:8000/transferir \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"from":"C001","to":"C002","amount":300.00}'

# Respuesta:
# {"status":"ok","from":"C001","to":"C002","amount":"300.00",
#  "new_balance_origen":"700.00","new_balance_destino":"800.00"}
```

## Uso del MCP Server

### Con Claude Desktop (stdio)

Configurar `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "banking": {
      "command": "python",
      "args": ["-m", "mcp_server.server"]
    }
  }
}
```

Se requiere la variable de entorno `AUTH_TOKEN` con un token JWT válido.

### Conectividad Remota (SSE)

El MCP Server expone SSE en el puerto 3000 cuando se ejecuta con Docker:

```
GET  http://localhost:3000/sse       → Conexión SSE
POST http://localhost:3000/messages/ → Mensajes del cliente
```

## Datos de Demo (Seed)

El script `scripts/seed.py` popula la base de datos con datos ficticios para desarrollo y demos.

### Uso Local

```bash
# Con SQLite (desarrollo rápido)
export DATABASE_URL=sqlite:///./banking.db  # Linux/macOS
set DATABASE_URL=sqlite:///./banking.db     # Windows
python scripts/seed.py

# Con PostgreSQL local
export DATABASE_URL=postgresql://user:password@localhost:5432/banking
python scripts/seed.py
```

### Uso con Docker Compose

```bash
# Iniciar servicios
docker-compose up -d

# Ejecutar seed (desde el host, apuntando al puerto expuesto)
DATABASE_URL=postgresql://user:password@localhost:5432/banking python scripts/seed.py

# O desde dentro del contenedor de la API
docker-compose exec api python scripts/seed.py
```

### Datos Creados

| Cliente | Email | Cuentas (número - saldo) |
|---------|-------|---------------------------|
| Juan Pérez | juan.perez@example.com | 0010000001 - $5,000.00 / 0010000002 - $2,500.50 |
| María García | maria.garcia@example.com | 0020000001 - $10,000.00 |
| Carlos López | carlos.lopez@example.com | 0030000001 - $1,500.75 |

- **Idempotente**: si ya existen datos, no duplica
- **Compatible** con SQLite (dev) y PostgreSQL (Docker/producción)
- **Variable** `DATABASE_URL` configurable (default apunta a Docker Compose)

## Ejecutar Pruebas

```bash
# Todas las pruebas
pytest -v

# Solo unitarias
pytest tests/unit/ -v

# Solo integración
pytest tests/integration/ -v

# Con cobertura
pip install pytest-cov
pytest --cov=core --cov=api --cov=mcp_server -v
```

## Estructura del Proyecto

```
├── core/                  # Lógica de dominio (Hexagonal + DDD)
│   ├── models.py          # Modelos SQLAlchemy
│   ├── exceptions.py      # Excepciones de dominio
│   ├── repositories.py    # Interfaces abstractas (puertos)
│   ├── repos_impl.py      # Implementaciones SQLAlchemy (adaptadores)
│   ├── unit_of_work.py    # Unit of Work abstracto
│   └── services.py        # Servicio de transferencias
├── api/                   # API REST FastAPI
│   ├── main.py            # Punto de entrada y rutas
│   ├── crud_factory.py    # Generador dinámico de CRUD
│   ├── schemas.py         # Esquemas Pydantic v2
│   ├── security.py        # JWT + autenticación
│   └── dependencies.py    # Inyección de dependencias
├── mcp_server/            # Servidor MCP
│   ├── server.py          # Servidor (SSE + stdio)
│   ├── generator.py       # Generación dinámica de Tools
│   └── api_client.py      # Cliente HTTP asíncrono
├── tests/
│   ├── unit/              # Pruebas unitarias (9 tests)
│   └── integration/       # Pruebas de integración (8 tests)
├── alembic/               # Migraciones de base de datos
├── .github/workflows/     # GitHub Actions CI/CD
├── Dockerfile.api         # Imagen Docker para la API
├── Dockerfile.mcp         # Imagen Docker para el MCP
├── docker-compose.yml     # Orquestación de servicios
├── CODING_STANDARDS.md    # Guía de estilo y convenciones
└── CHANGELOG.md           # Historial de cambios
```

## Variables de Entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://user:password@db:5432/banking` | URL de conexión a PostgreSQL |
| `API_BASE_URL` | `http://api:8000` | URL base de la API (MCP → API) |
| `AUTH_TOKEN` | `""` | Token JWT para autenticación MCP |
| `MCP_TRANSPORT` | `sse` | Transporte del MCP (`sse` o `stdio`) |
| `MCP_PORT` | `3000` | Puerto del MCP server en modo SSE |

## Licencia

MIT
