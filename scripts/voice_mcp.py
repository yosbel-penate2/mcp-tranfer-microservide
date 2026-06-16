#!/usr/bin/env python
"""Voice + MCP Banking Assistant with barge-in support.

Uses: Google STT (free), pyttsx3 TTS (local), MCP stdio.
Supports barge-in: the user can interrupt the assistant at any time.
"""

import asyncio
import json
import threading
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import speech_recognition as sr
import pyttsx3
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters


def humanize_clients(raw: str) -> str:
    """Convert raw JSON list of clients into a conversational sentence."""
    try:
        data = json.loads(raw)
        if isinstance(data, list) and len(data) > 0:
            names = [c.get("nombre", "unknown") for c in data]
            if len(names) == 1:
                return f"We have one client: {names[0]}."
            return (
                f"We have {len(names)} clients: "
                f"{', '.join(names[:-1])} and {names[-1]}."
            )
        return "No clients found in the system."
    except (json.JSONDecodeError, TypeError):
        return raw[:300]


def humanize_accounts(raw: str) -> str:
    """Convert raw JSON list of accounts into a conversational sentence."""
    try:
        data = json.loads(raw)
        if isinstance(data, list) and len(data) > 0:
            parts = []
            total = 0
            for a in data:
                numero = a.get("numero", "unknown")
                saldo = float(a.get("saldo", 0))
                total += saldo
                parts.append(f"account {numero} has ${saldo:,.2f}")
            summary = "; ".join(parts)
            return (
                f"There are {len(data)} accounts. {summary}. "
                f"Your total balance across all accounts is ${total:,.2f}."
            )
        return "No accounts found."
    except (json.JSONDecodeError, TypeError):
        return raw[:300]


def humanize_health(raw: str) -> str:
    """Convert health check JSON into a friendly message."""
    try:
        data = json.loads(raw)
        status = data.get("status", "unknown")
        if status == "ok":
            return "The system is running perfectly. All services are operational."
        return f"The system status is: {status}."
    except (json.JSONDecodeError, TypeError):
        return raw[:200]


def humanize_error(tool: str, error_msg: str) -> str:
    """Convert a technical error into a friendly message."""
    error_lower = str(error_msg).lower()
    if "connection" in error_lower or "unreachable" in error_lower:
        return (
            "I'm having trouble connecting to the banking system. "
            "Please check that the server is running."
        )
    if "not found" in error_lower:
        return f"I couldn't find what you were looking for in the {tool} section."
    if "timeout" in error_lower:
        return "The request timed out. The system might be busy, please try again."
    return f"Sorry, I ran into an issue while checking {tool}. Please try again."


def speak_text(text: str):
    """Non-blocking TTS: starts speaking in a background thread."""
    engine = pyttsx3.init()
    engine.setProperty("rate", 150)
    engine.setProperty("volume", 0.9)
    engine.say(text)
    engine.runAndWait()
    engine.stop()


def speak(text: str):
    """Print and speak text in one shot (blocking)."""
    print(f"[BOT] {text}")
    thread = threading.Thread(target=speak_text, args=(text,), daemon=True)
    thread.start()
    thread.join()


def speak_with_bargein(
    text: str,
    recognizer: sr.Recognizer,
    source: sr.AudioSource,
) -> tuple[bool, sr.AudioData | None]:
    """
    Speak text while listening for user interruption.

    If the user starts speaking while TTS is playing, the TTS is
    stopped immediately and the audio is returned.

    Returns:
        (interrupted, audio_data):
            interrupted — True if the user interrupted.
            audio_data — captured audio if interrupted, else None.
    """
    print(f"[BOT] {text}")

    engine = pyttsx3.init()
    engine.setProperty("rate", 150)
    engine.setProperty("volume", 0.9)
    engine.say(text)

    interrupted = False
    audio = None

    # Start TTS in a background thread
    tts_thread = threading.Thread(target=engine.runAndWait, daemon=True)
    tts_thread.start()

    # Monitor microphone while TTS plays
    while tts_thread.is_alive():
        try:
            # Short listen — if user speaks, catch it immediately
            audio = recognizer.listen(source, timeout=0.15, phrase_time_limit=0.5)
            # Audio received → user interrupted
            engine.stop()
            interrupted = True
            break
        except sr.WaitTimeoutError:
            continue
        except Exception:
            break

    # Ensure TTS thread finishes
    try:
        engine.stop()
    except Exception:
        pass

    return interrupted, audio


def listen(recognizer: sr.Recognizer, source: sr.AudioSource) -> str | None:
    """
    Listen and transcribe one utterance from the microphone.

    Returns transcribed text (lowercase) or None on failure.
    """
    print("[MIC] Listening...")
    try:
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
    except sr.WaitTimeoutError:
        return None

    try:
        text = recognizer.recognize_google(audio, language="en-US")
        print(f"[YOU] {text}")
        return text.lower().strip()
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"[STT ERROR] {e}")
        return None


def parse_intent(text: str):
    """Parse English voice commands into actions."""
    if not text:
        return None, {}

    if any(w in text for w in ["quit", "exit", "bye", "goodbye", "stop"]):
        return "exit", {}

    if any(w in text for w in ["balance", "account", "money", "how much"]):
        return "list_accounts", {}

    if any(w in text for w in ["transfer", "send", "pay"]):
        return "transfer", {"text": text}

    if any(w in text for w in ["client", "customer", "who"]):
        return "list_clients", {}

    if any(w in text for w in ["health", "status", "running"]):
        return "health", {}

    return "unknown", {"text": text}


async def main():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    # Obtain JWT token from the Banking API
    login_resp = requests.post(
        "http://localhost:8000/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = login_resp.json().get("access_token", "")

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
        },
    )

    print("[BANK] Voice Banking Assistant started")
    print("Say 'quit' to exit\n")

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")
            print("Listening...\n")

            # Open microphone once and reuse it
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)

                speak(
                    "Hello, I'm your banking assistant. "
                    "I can check balances, list clients, or tell you the system status. "
                    "Feel free to interrupt me at any time. "
                    "How can I help you?"
                )

                while True:
                    text = listen(recognizer, source)
                    if not text:
                        speak("Sorry, I didn't catch that. Could you repeat?")
                        continue

                    print(f"[DEBUG] Intent: {text}")
                    intent, params = parse_intent(text)

                    if intent == "exit":
                        speak("Goodbye! Have a great day.")
                        break

                    elif intent == "list_accounts":
                        try:
                            result = await session.call_tool(
                                "list_all_cuentas__get", {}
                            )
                            raw = result.content[0].text
                            print(f"[DEBUG] Result: {raw[:200]}")
                            response = humanize_accounts(raw)
                            interrupted, _ = speak_with_bargein(
                                response, recognizer, source
                            )
                            if interrupted:
                                # User already started speaking — process next
                                continue
                        except Exception as e:
                            print(f"[ERROR] list_accounts: {e}")
                            speak(humanize_error("accounts", e))

                    elif intent == "list_clients":
                        try:
                            result = await session.call_tool(
                                "list_all_clientes__get", {}
                            )
                            raw = result.content[0].text
                            print(f"[DEBUG] Result: {raw[:200]}")
                            response = humanize_clients(raw)
                            interrupted, _ = speak_with_bargein(
                                response, recognizer, source
                            )
                            if interrupted:
                                continue
                        except Exception as e:
                            print(f"[ERROR] list_clients: {e}")
                            speak(humanize_error("clients", e))

                    elif intent == "health":
                        try:
                            result = await session.call_tool(
                                "health_health_get", {}
                            )
                            raw = result.content[0].text
                            print(f"[DEBUG] Result: {raw[:200]}")
                            response = humanize_health(raw)
                            interrupted, _ = speak_with_bargein(
                                response, recognizer, source
                            )
                            if interrupted:
                                continue
                        except Exception as e:
                            print(f"[ERROR] health: {e}")
                            speak(humanize_error("system status", e))

                    elif intent == "transfer":
                        speak(
                            "For security reasons, I cannot process transfers by voice. "
                            "Please use the web application instead."
                        )

                    else:
                        speak(
                            "Sorry, I didn't understand. You can ask me about: "
                            "account balances, client list, or system status."
                        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
