"""LiveKit Voice Agent with MCP Banking Tools Integration.

This agent connects to the Banking MCP server and exposes its tools
as LiveKit function tools for voice interactions.
"""

import asyncio
import logging
import os
import textwrap
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    function_tool,
    inference,
    RunContext,
)
from livekit.plugins import silero
from livekit.agents import inference
from mcp import ClientSession
from mcp.client.sse import sse_client

logger = logging.getLogger("banking-voice-agent")

load_dotenv(".env.local")


class BankingMCPAgent(Agent):
    """Voice agent with access to banking MCP tools."""

    def __init__(
        self,
        mcp_env: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(
            llm=inference.LLM(model="openai/gpt-5.2-chat-latest"),
            instructions=textwrap.dedent(
                """\
                Eres un asistente bancario por voz. Puedes ayudar a los usuarios con:
                - Consultar saldos y movimientos de cuentas
                - Realizar transferencias entre cuentas
                - Listar clientes y cuentas
                - Crear nuevos clientes y cuentas

                Habla de forma natural y conversacional. Confirma siempre
                las operaciones importantes antes de ejecutarlas.

                # Reglas de salida para voz
                - Responde en texto plano. Nunca uses JSON, markdown, listas, tablas, código o emojis.
                - Mantén las respuestas breves: una a tres frases. Haz una pregunta a la vez.
                - No reveles nombres de herramientas, parámetros o salidas técnicas.
                - Deleta números, números de teléfono o emails.
                - Evita acrónimos y palabras con pronunciación poco clara.

                # Flujo conversacional
                - Ayuda al usuario eficientemente. Prefiere el paso más simple y seguro primero.
                - Confirma operaciones importantes antes de ejecutarlas.
                - Resume resultados clave al cerrar un tema.
                """
            ),
        )
        self._mcp_env = mcp_env or {}
        self._mcp_session: Optional[ClientSession] = None
        self._available_tools: List[Dict[str, Any]] = []

    async def _connect_mcp(self) -> None:
        """Connect to the MCP server via SSE and fetch available tools."""
        # MCP server runs in SSE mode on port 3000 (Docker) or 3000 (local)
        mcp_url = os.environ.get("MCP_SSE_URL", "http://localhost:3000/sse")
        logger.info(f"Connecting to MCP server at {mcp_url}")
        
        try:
            sse_transport = await sse_client(mcp_url).__aenter__()
            read_stream, write_stream = sse_transport
            logger.info("SSE transport established")

            self._mcp_session = ClientSession(read_stream, write_stream)
            await self._mcp_session.initialize()
            logger.info("MCP session initialized")

            tools_result = await self._mcp_session.list_tools()
            self._available_tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                }
                for tool in tools_result.tools
            ]
            logger.info(f"Loaded {len(self._available_tools)} MCP tools from {mcp_url}")
        except Exception as e:
            logger.error(f"Failed to connect to MCP server at {mcp_url}: {type(e).__name__}: {e}")
            raise

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

    async def on_enter(self) -> None:
        """Called when the agent joins the room."""
        # Register MCP tools as LiveKit function tools dynamically
        for tool_def in self._available_tools:
            name = tool_def["name"]
            description = tool_def["description"]

            async def make_tool_call(tool_name: str):
                @function_tool(description=description)
                async def tool_func(context: RunContext, **kwargs) -> str:
                    return await self._call_mcp_tool(tool_name, kwargs)

                tool_func.__name__ = tool_name
                return tool_func

            tool_func = await make_tool_call(name)
            self.tools.append(tool_func)

        await self.session.say(
            "¡Hola! Soy tu asistente bancario. "
            "¿En qué puedo ayudarte hoy?"
        )


async def entrypoint(ctx: JobContext) -> None:
    """Main entrypoint for the LiveKit agent worker."""
    # MCP server runs in SSE mode (Docker: http://mcp:3000/sse, Local: http://localhost:3000/sse)
    mcp_env = {
        "MCP_SSE_URL": os.environ.get("MCP_SSE_URL", "http://localhost:3000/sse"),
    }

    agent = BankingMCPAgent(mcp_env=mcp_env)

    # Temporarily disabled MCP SSE connection to test 1006 disconnect
    # await agent._connect_mcp()

    # VAD for turn detection
    vad = silero.VAD.load()

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="es"),
        tts=inference.TTS(
            model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
        vad=vad,
    )

    await session.start(
        agent=agent,
        room=ctx.room,
    )

    await ctx.connect()


# AgentServer setup for `lk agent dev`
server = AgentServer()


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="banking-voice-agent")
async def banking_agent(ctx: JobContext) -> None:
    await entrypoint(ctx)


if __name__ == "__main__":
    cli.run_app(server)