"""Core client class for CMD Chat.

This module provides the main CmdChatClient class that coordinates
all client functionality following SOLID principles.
"""

from __future__ import annotations

import asyncio
from collections import deque
import contextlib
from typing import TYPE_CHECKING

from cmdchat.lib import FileTransferManager, create_renderer
from cmdchat.types import ClientConfig
from cmdchat.utils import sanitize_name, sanitize_room
from cmdchat.client.files import handle_file_chunk, handle_file_init, send_file
from cmdchat.client.history import EncryptedHistory
from cmdchat.client.io import perform_handshake, send_encrypted
from cmdchat.client.loops import receive_loop, send_loop
from cmdchat.client.tls import create_ssl_context

if TYPE_CHECKING:

    from cmdchat import crypto
    from cmdchat.types import MessageRenderer


class CmdChatClient:
    """Manage the encrypted client lifecycle.

    This class coordinates:
    - Connection management with auto-reconnect
    - Message rendering via Strategy pattern
    - File transfer operations
    - Encrypted history (optional)

    Follows SOLID principles with dependency injection.
    """

    def __init__(self, config: ClientConfig):
        """Initialize client with configuration.

        Args:
            config: Client configuration
        """
        self.config = config
        self._stop_event = asyncio.Event()
        self._messages: deque[dict] = deque(maxlen=config.buffer_size)
        self._history = (
            EncryptedHistory(config.history_file, config.history_passphrase)
            if config.history_file and config.history_passphrase
            else None
        )
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._cipher: crypto.SymmetricCipher | None = None
        self._send_lock = asyncio.Lock()
        self._current_name = sanitize_name(config.name)
        self._current_room = sanitize_room(config.room)
        self._heartbeat_interval: float | None = None

        # Dependency injection: renderer and file transfer manager
        self._renderer: MessageRenderer = create_renderer(config.renderer)
        self._file_manager = FileTransferManager()

    async def run(self) -> None:
        """Attempt to connect and maintain a live session with automatic retries."""
        backoff = 1
        while not self._stop_event.is_set():
            try:
                await self._connect_and_run()
                break
            except asyncio.CancelledError:
                raise
            except StopAsyncIteration:
                break
            except Exception as exc:
                if self._stop_event.is_set():
                    break
                self._handle_reconnect_notice(exc, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
        print("Client session terminated.")

    async def _connect_and_run(self) -> None:
        """Connect to server and run send/receive loops."""
        ssl_context = create_ssl_context(
            self.config.tls, self.config.ca_file, self.config.tls_insecure
        )
        reader, writer = await asyncio.open_connection(
            self.config.host,
            self.config.port,
            ssl=ssl_context,
        )

        cipher, response = await perform_handshake(
            reader,
            writer,
            self.config,
            self._current_name,
            self._current_room,
        )

        negotiated_renderer = response.get("renderer", self.config.renderer)
        negotiated_buffer = int(response.get("buffer_size", self.config.buffer_size))
        negotiated_room = response.get("room", self._current_room)
        self._heartbeat_interval = response.get("heartbeat_interval")

        self._messages = deque(
            list(self._messages)[-negotiated_buffer:], maxlen=negotiated_buffer
        )
        self.config.renderer = negotiated_renderer
        self._current_room = negotiated_room

        # Update renderer if negotiated different
        with contextlib.suppress(ValueError):
            self._renderer = create_renderer(negotiated_renderer)

        self._reader = reader
        self._writer = writer
        self._cipher = cipher

        # Display beautiful welcome banner
        self._show_welcome_banner()

        await self._send_system_message(f"{self._current_name} connected.")

        send_task = asyncio.create_task(
            send_loop(
                self._stop_event,
                self._handle_command,
                self._send_chat,
            )
        )
        receive_task = asyncio.create_task(
            receive_loop(
                self._reader,
                self._cipher,
                self._stop_event,
                self._record_message,
                self._handle_file_init,
                self._handle_file_chunk,
                self._send_pong,
            )
        )

        done, pending = await asyncio.wait(
            {send_task, receive_task}, return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

        if any(task is send_task for task in done):
            self._stop_event.set()

        if self._writer:
            self._writer.close()
            with contextlib.suppress(Exception):
                await self._writer.wait_closed()
        self._reader = None
        self._writer = None
        self._cipher = None

    async def _record_message(self, payload: dict) -> None:
        """Remember and render incoming payloads."""
        self._messages.append(payload)
        if self._history:
            with contextlib.suppress(Exception):
                await asyncio.to_thread(self._history.append, payload)
        self._render_message(payload)

    async def _handle_command(self, command_line: str) -> bool:
        """Process slash commands. Returns True if the client should exit."""
        parts = command_line.strip().split(maxsplit=1)
        command = parts[0].lower()
        argument = parts[1] if len(parts) > 1 else ""

        if command == "/quit":
            await self._send_system_message(f"{self._current_name} disconnected.")
            return True
        if command == "/help":
            try:
                from cmdchat.ui import create_help_menu

                print(create_help_menu())
            except ImportError:
                print("Commands: /nick <name>, /join <room>, /send <filepath>,")
                print("/clear, /help, /quit")
            return False
        if command == "/clear":
            try:
                from cmdchat.ui import clear_screen

                clear_screen()
                # Re-show welcome banner after clear
                self._show_welcome_banner()
            except ImportError:
                self._messages.clear()
                print("[local] chat buffer cleared.")
            return False
        if command == "/send":
            if not argument:
                print("Usage: /send <filepath>")
                return False
            await self._send_file(argument)
            return False
        if command == "/nick":
            if not argument:
                print("Usage: /nick <new name>")
                return False
            new_name = sanitize_name(argument)
            await self._send_encrypted({"type": "rename", "name": new_name})
            self._current_name = new_name
            return False
        if command == "/join":
            if not argument:
                print("Usage: /join <room>")
                return False
            new_room = sanitize_room(argument)
            await self._send_encrypted({"type": "switch_room", "room": new_room})
            self._current_room = new_room
            return False
        print(f"Unknown command: {command}")
        return False

    async def _send_chat(self, message: str) -> None:
        """Encrypt and send a chat payload."""
        await self._send_encrypted({"type": "chat", "message": message})

    async def _send_system_message(self, message: str) -> None:
        """Send a system notification."""
        await self._send_encrypted({"type": "system", "message": message})

    async def _send_pong(self) -> None:
        """Respond to server heartbeat pings."""
        await self._send_encrypted({"type": "pong"})

    async def _send_encrypted(self, payload: dict) -> None:
        """Encrypt payload and push to the server."""
        await send_encrypted(self._writer, self._cipher, payload, self._send_lock)

    def _render_message(self, payload: dict) -> None:
        """Render payloads using the configured renderer.

        Uses Strategy pattern for flexible rendering.

        Args:
            payload: Message payload to render
        """
        try:
            output = self._renderer.render(payload)
            print(output)
        except Exception as exc:
            # Fallback to simple representation
            print(f"[render error] {payload.get('type', 'unknown')}: {exc}")

    def _show_welcome_banner(self) -> None:
        """Display welcome banner with connection info."""
        try:
            from cmdchat.ui import (
                Colors,
                create_banner,
                create_help_menu,
                create_separator,
                create_welcome_box,
            )

            # Show banner
            print(create_banner())

            # Show connection info
            server_addr = f"{self.config.host}:{self.config.port}"
            print(create_welcome_box(self._current_name, self._current_room, server_addr))
            print()

            # Show quick help
            print(f"{Colors.BRIGHT_YELLOW}💡 Quick Tips:{Colors.RESET}")
            print("  • Type a message and press Enter to chat")
            print("  • Use /help to see all available commands")
            print("  • Use /quit to disconnect and exit")
            print()
            print(create_separator(width=70))
            print()
        except ImportError:
            # Fallback if UI module not available
            print(
                f"Connected to CMD Chat as {self._current_name} in room {self._current_room}."
            )
            print("Type messages to chat. Commands: /nick, /join, /send, /clear, /help, /quit")

    def _handle_reconnect_notice(self, exc: Exception, backoff: int) -> None:
        """Emit a reconnection status indicator."""
        if self.config.quiet_reconnect:
            print("[status] reconnecting...", flush=True)
        else:
            print(
                f"[status] connection lost ({exc}). Retrying in {backoff}s.", flush=True
            )

    async def _send_file(self, filepath: str) -> None:
        """Send a file to the current room via encrypted chunks."""
        await send_file(filepath, self._current_name, self._send_encrypted)

    async def _handle_file_init(self, payload: dict) -> None:
        """Handle incoming file transfer initialization."""
        await handle_file_init(payload, self._file_manager)

    async def _handle_file_chunk(self, payload: dict) -> None:
        """Handle incoming file chunk."""
        await handle_file_chunk(payload, self._file_manager)
