#!/usr/bin/env python
"""Voice + MCP Banking Assistant - Minimal script.

Uses: Google STT (free), pyttsx3 TTS (local), MCP stdio.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import speech_recognition as sr
import pyttsx3
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters


def speak(text):
    print(f"[BOT] {text}")
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 0.9)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"[TTS ERROR] {e}")


async def main():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    # MCP Server via stdio - use valid JWT token from API login
    import requests
    login_resp = requests.post("http://localhost:8000/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.json().get("access_token", "supersecrettoken")
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_server.server"],
        cwd=project_root,
        env={
            **os.environ,
            "MCP_TRANSPORT": "stdio",
            "API_BASE_URL": "http://localhost:8000",
            "AUTH_TOKEN": token,
        }
    )

    print("[BANK] Asistente bancario por voz iniciado")
    print("Di 'salir' para terminar\n")

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print(f"Tools disponibles: {[t.name for t in tools.tools]}")
            print("Escuchando...")

            def listen():
                with sr.Microphone() as source:
                    print("[MIC] Escuchando...")
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    try:
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    except sr.WaitTimeoutError:
                        return None
                try:
                    text = recognizer.recognize_google(audio, language="es-ES")
                    print(f"[YOU] {text}")
                    return text.lower()
                except sr.UnknownValueError:
                    return None
                except sr.RequestError as e:
                    print(f"Error STT: {e}")
                    return None

            def parse_intent(text):
                """Simple intent parsing for banking operations."""
                if not text:
                    return None, {}

                if any(w in text for w in ["salir", "adios", "terminar", "chau"]):
                    return "exit", {}

                if "saldo" in text or "cuanto tengo" in text:
                    return "list_cuentas", {}

                if "transferir" in text or "enviar" in text:
                    return "transferir", {"text": text}

                if "cliente" in text and ("lista" in text or "todos" in text):
                    return "list_clientes", {}

                return "unknown", {"text": text}

            speak("Hola, soy tu asistente bancario. En que puedo ayudarte?")

            while True:
                text = listen()
                if not text:
                    speak("No te entendi. Puedes repetir?")
                    continue

                print(f"[DEBUG] Intent: {text}")

                intent, params = parse_intent(text)

                if intent == "exit":
                    speak("Hasta luego!")
                    break

                elif intent == "list_cuentas":
                    try:
                        print("[DEBUG] Calling list_cuentas...")
                        result = await session.call_tool("list_all_cuentas__get", {})
                        print(f"[DEBUG] Result: {result.content[0].text[:200]}")
                        speak(result.content[0].text[:500])
                    except Exception as e:
                        print(f"[ERROR] list_cuentas: {e}")
                        speak(f"Error consultando cuentas: {e}")

                elif intent == "list_clientes":
                    try:
                        print("[DEBUG] Calling list_clientes...")
                        result = await session.call_tool("list_all_clientes__get", {})
                        print(f"[DEBUG] Result: {result.content[0].text[:200]}")
                        speak(result.content[0].text[:500])
                    except Exception as e:
                        print(f"[ERROR] list_clientes: {e}")
                        speak(f"Error consultando clientes: {e}")

                elif intent == "transferir":
                    speak("Para transferencias, por favor usa la app web. Por seguridad no proceso transferencias por voz.")

                else:
                    speak("Puedo ayudarte con: consultar saldos, listar clientes, o transferencias. Que necesitas?")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSaliendo...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()