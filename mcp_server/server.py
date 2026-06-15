"""MCP (Model Context Protocol) server for banking operations.

Supports two transport modes:
  - SSE (default): Uses HTTP Server-Sent Events on port 3000.
    Suitable for remote connections (e.g., ChatGPT Actions).
  - stdio: Standard input/output for local Claude Desktop integration.

Transport mode is selected via the MCP_TRANSPORT environment variable.
"""

import logging
import os
from typing import Any, Dict, List, Sequence

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    Tool,
    TextContent,
    ServerCapabilities,
)

from mcp_server.generator import generate_tools, handle_tool_call

logger = logging.getLogger(__name__)

app = Server("banking-mcp")

TRANSPORT = os.environ.get("MCP_TRANSPORT", "sse").lower()


@app.list_tools()
async def list_tools() -> List[Tool]:
    """MCP handler: returns available tools dynamically from the OpenAPI spec."""
    return await generate_tools()


@app.call_tool()
async def call_tool(
    name: str,
    arguments: Dict[str, Any],
) -> Sequence[TextContent]:
    """MCP handler: executes a tool call against the REST API."""
    result = await handle_tool_call(name, arguments)
    return [TextContent(type="text", text=r["text"]) for r in result]


async def run_sse():
    """Run the MCP server with SSE (Server-Sent Events) transport.

    Listens on port 3000 (configurable via MCP_PORT env var).
    Exposes two HTTP routes:
      - GET  /sse        — SSE endpoint for client connection
      - POST /messages/  — Message endpoint for client responses
    """
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    import uvicorn

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as (
            read_stream,
            write_stream,
        ):
            await app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="banking-mcp",
                    server_version="1.0.0",
                    capabilities=ServerCapabilities(),
                ),
            )

    async def handle_messages(request):
        await sse.handle_post_message(request.scope, request.receive, request._send)

    starlette_app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages/", endpoint=handle_messages, methods=["POST"]),
        ],
    )

    port = int(os.environ.get("MCP_PORT", "3000"))
    logger.info(f"MCP SSE server starting on port {port}")
    config = uvicorn.Config(starlette_app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def run_stdio():
    """Run the MCP server with stdio transport.

    Used for local Claude Desktop integration via
    claude_desktop_config.json.
    """
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="banking-mcp",
                server_version="1.0.0",
                capabilities=ServerCapabilities(),
            ),
        )


async def main():
    """Entry point — dispatches to SSE or stdio based on MCP_TRANSPORT."""
    if TRANSPORT == "sse":
        await run_sse()
    else:
        await run_stdio()


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
