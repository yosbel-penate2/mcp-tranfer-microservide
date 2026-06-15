"""LiveKit Voice Agent with MCP Banking Tools Integration.

This agent connects to the Banking MCP server and exposes its tools
as LiveKit function tools for voice interactions.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

from livekit import agents, rtc
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.agents.llm import FunctionTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger("banking-voice-agent")


class BankingMCPAgent(Agent):
    """Voice agent with access to banking MCP tools."""

    def __init__(
        self,
        mcp_command: list[str],
        mcp_env: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(
            instructions=(
                "Eres un asistente bancario por voz. Puedes ayudar a los usuarios con:\n"
                "- Consultar saldos y movimientos de cuentas\n"
                "- Realizar transferencias entre cuentas\n"
                "- Listar clientes y cuentas\n"
                "- Crear nuevos clientes y cuentas\n\n"
                "Habla de forma natural y conversacional. Confirma siempre "
                "las operaciones importantes antes de ejecutarlas."
            ),
        )
        self._mcp_command = mcp_command
        self._mcp_env = mcp_env or {}
        self._mcp_session: Optional[ClientSession] = None
        self._available_tools: List[Dict[str, Any]] = []

    async def _connect_mcp(self) -> None:
        """Connect to the MCP server and fetch available tools."""
        server_params = StdioServerParameters(
            command=self._mcp_command[0],
            args=self._mcp_command[1:],
            env={**os.environ, **self._mcp_env},
        )

        stdio_transport = await stdio_client(server_params).__aenter__()
        read_stream, write_stream = stdio_transport

        self._mcp_session = ClientSession(read_stream, write_stream)
        await self._mcp_session.initialize()

        tools_result = await self._mcp_session.list_tools()
        self._available_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
            }
            for tool in tools_result.tools
        ]
        logger.info(f"Loaded {len(self._available_tools)} MCP tools")

    async def _call_mcp_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool on the MCP server."""
        if not self._mcp_session:
            return "Error: MCP session not initialized"

        try:
            result = await self._mcp_session.call_tool(name, arguments)
            if result.content:
                return result.content[0].text
            return "Operación completada sin respuesta"
        except Exception as e:
            logger.error(f"MCP tool call failed: {e}")
            return f"Error al ejecutar {name}: {e}"

    def _create_function_tools(self) -> List[FunctionTool]:
        """Create LiveKit function tools from MCP tools."""
        tools = []

        for tool_def in self._available_tools:
            name = tool_def["name"]
            description = tool_def["description"]
            schema = tool_def["inputSchema"]

            async def make_tool_call(
                tool_name: str,
                tool_schema: Dict[str, Any],
            ):
                @function_tool(description=description)
                async def tool_func(**kwargs) -> str:
                    return await self._call_mcp_tool(tool_name, kwargs)

                tool_func.__name__ = tool_name
                return tool_func

            tool_func = await make_tool_call(name, schema)
            tools.append(tool_func)

        return tools

    async def on_enter(self) -> None:
        """Called when the agent joins the room."""
        await self._connect_mcp()

        # Register MCP tools as LiveKit function tools
        for tool in self._create_function_tools():
            self.tools.append(tool)

        await self.session.say(
            "¡Hola! Soy tu asistente bancario. "
            "¿En qué puedo ayudarte hoy?"
        )


async def entrypoint(ctx: JobContext) -> None:
    """Main entrypoint for the LiveKit agent worker."""
    await ctx.connect()

    # MCP server command - adjust based on your setup
    mcp_command = [
        "python", "-m", "mcp_server.server"
    ]

    # Environment for MCP (AUTH_TOKEN needed for API access)
    mcp_env = {
        "MCP_TRANSPORT": "stdio",
        "API_BASE_URL": os.environ.get("API_BASE_URL", "http://localhost:8000"),
        "AUTH_TOKEN": os.environ.get("AUTH_TOKEN", ""),
    }

    agent = BankingMCPAgent(mcp_command=mcp_command, mcp_env=mcp_env)

    session = AgentSession()
    await session.start(agent=agent, room=ctx.room)

    # Keep running
    await asyncio.Event().wait()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))