# LiveKit Voice Agent - Banking MCP Integration

Agente de voz LiveKit que expone las herramientas bancarias del MCP server para interacciones por voz en tiempo real.

## Arquitectura

```
Usuario (voz) → LiveKit Room → LiveKit Agent → MCP Server (stdio) → REST API → PostgreSQL
```

## Requisitos

- LiveKit Cloud account o servidor LiveKit self-hosted
- Python 3.11+
- Banking API corriendo (ver proyecto principal)

## Configuración

### 1. Variables de entorno

```bash
cp .env.example .env
# Editar .env con tus credenciales de LiveKit
```

### 2. Credenciales LiveKit

Obtén tus credenciales en [LiveKit Cloud](https://cloud.livekit.io) o en tu servidor self-hosted:
- `LIVEKIT_URL`: WebSocket URL (ej: `wss://your-project.livekit.cloud`)
- `LIVEKIT_API_KEY`: API Key del proyecto
- `LIVEKIT_API_SECRET`: API Secret del proyecto

## Ejecución

### Desarrollo Local

```bash
# 1. Iniciar API y base de datos
cd ..
docker-compose up -d db api

# 2. Poblar datos de demo
DATABASE_URL=postgresql://user:password@localhost:5432/banking python scripts/seed.py

# 3. Obtener token JWT para AUTH_TOKEN
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 4. Configurar .env con AUTH_TOKEN y credenciales LiveKit

# 5. Ejecutar agente
pip install -r requirements.txt
python agent.py
```

### Con Docker Compose (Producción)

```bash
# Desde la raíz del proyecto
docker-compose up -d livekit-agent
```

El agente se conectará automáticamente a LiveKit y esperará usuarios en rooms.

## Tools Disponibles (desde MCP)

El agente expone dinámicamente todas las tools del MCP server:

| Tool | Descripción |
|------|-------------|
| `list_clientes` | Listar todos los clientes |
| `get_cliente` | Obtener cliente por ID |
| `create_cliente` | Crear nuevo cliente |
| `update_cliente` | Actualizar cliente |
| `delete_cliente` | Eliminar cliente |
| `list_cuentas` | Listar todas las cuentas |
| `get_cuenta` | Obtener cuenta por ID |
| `create_cuenta` | Crear nueva cuenta |
| `update_cuenta` | Actualizar cuenta |
| `delete_cuenta` | Eliminar cuenta |
| `list_transacciones` | Listar transacciones |
| `get_transaccion` | Obtener transacción por ID |
| `create_transaccion` | Registrar transacción |
| `transferir` | Transferir dinero entre cuentas |

## Uso con LiveKit

### 1. Token Server (para frontend)

```bash
# Ejemplo token server simple (Node.js)
# Ver: https://github.com/livekit-examples/token-server-node
```

### 2. Conectar desde frontend

```javascript
import { Room } from "livekit-client";

const room = new Room();
await room.connect(
  "wss://your-project.livekit.cloud",
  "token-generado-desde-tu-backend"
);

// El agente bancario se unirá automáticamente
```

### 3. Probar con LiveKit Meet

1. Ve a https://meet.livekit.io
2. Ingresa tu token
3. Únete a una room
4. El agente bancario responderá por voz

## Desarrollo

### Agregar nuevas tools

Las tools se descubren automáticamente desde el MCP server. Para agregar funcionalidad:

1. Agrega endpoint en la REST API (`api/`)
2. El MCP server lo detecta automáticamente via OpenAPI
3. El agente LiveKit lo expone como function tool

### Logs

```bash
docker-compose logs -f livekit-agent
```

## Estructura

```
livekit_agent/
├── agent.py          # Agente principal con integración MCP
├── Dockerfile        # Imagen Docker
├── requirements.txt  # Dependencias Python
├── .env.example      # Template de variables de entorno
└── README.md         # Esta documentación
```