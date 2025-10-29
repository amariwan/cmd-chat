"""Message renderers.

This module implements different message rendering strategies following
the Strategy pattern and SOLID principles.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ..utils import format_timestamp

if TYPE_CHECKING:
    from ..types import MessageRenderer


class RichRenderer:
    """Rich renderer with timestamps and metadata."""

    def render(self, payload: dict, output=None) -> str:
        """Render a message payload."""
        timestamp = format_timestamp(payload.get("timestamp"))
        msg_type = payload.get("type")

        if msg_type == "chat":
            sender = payload.get("sender", "?")
            message = payload.get("message", "")
            sequence = payload.get("sequence")
            seq_label = f" #{sequence}" if sequence is not None else ""
            line = f"[{timestamp}{seq_label}] {sender}: {message}"
            if output is not None:
                output.write(line)
                return None
            return line

        message = payload.get("message", "")
        line = f"[{timestamp}] [system] {message}"
        if output is not None:
            output.write(line)
            return None
        return line


class AsciiRenderer:
    """ASCII art renderer with beautiful formatting."""

    def __init__(self):
        """Initialize renderer with UI components."""
        try:
            from ..ui import (
                Colors,
                Icons,
                create_file_transfer_box,
                create_message_box,
                create_system_message,
            )
            self.create_message_box = create_message_box
            self.create_system_message = create_system_message
            self.create_file_transfer_box = create_file_transfer_box
            self.Colors = Colors
            self.Icons = Icons
            self._ui_available = True
        except ImportError:
            self._ui_available = False

    def render(self, payload: dict, output=None) -> str:
        """Render a message payload with ASCII art."""
        if not self._ui_available:
            # Fallback to simple rendering
            return self._render_fallback(payload, output)

        timestamp = format_timestamp(payload.get("timestamp"))
        msg_type = payload.get("type")

        if msg_type == "chat":
            sender = payload.get("sender", "?")
            message = payload.get("message", "")
            # For now, we can't detect if it's own message, so default to False
            line = self.create_message_box(sender, message, timestamp, is_own=False)
            if output is not None:
                output.write(line)
                return None
            return line

        if msg_type == "system":
            message = payload.get("message", "")
            line = self.create_system_message(message, "info")
            if output is not None:
                output.write(line)
                return None
            return line

        if msg_type == "file_init":
            sender = payload.get("sender", "?")
            filename = payload.get("filename", "")
            filesize = payload.get("filesize", 0)
            line = self.create_file_transfer_box(filename, filesize, sender, progress=0.0)
            if output is not None:
                output.write(line)
                return None
            return line

        # Default fallback
        return self._render_fallback(payload, output)

    def _render_fallback(self, payload: dict, output=None) -> str:
        """Fallback rendering without UI components."""
        timestamp = format_timestamp(payload.get("timestamp"))
        msg_type = payload.get("type")

        if msg_type == "chat":
            sender = payload.get("sender", "?")
            message = payload.get("message", "")
            line = f"[{timestamp}] {sender}: {message}"
        elif msg_type == "system":
            message = payload.get("message", "")
            line = f"[{timestamp}] [system] {message}"
        else:
            line = f"[{timestamp}] {payload}"

        if output is not None:
            output.write(line)
            return None
        return line


class MinimalRenderer:
    """Minimal renderer without timestamps."""

    def render(self, payload: dict, output=None) -> str:
        """Render a message payload."""
        msg_type = payload.get("type")

        if msg_type == "chat":
            sender = payload.get("sender", "?")
            message = payload.get("message", "")
            line = f"{sender}: {message}"
            if output is not None:
                output.write(line)
                return None
            return line

        message = payload.get("message", "")
        line = f"[system] {message}"
        if output is not None:
            output.write(line)
            return None
        return line


class JsonRenderer:
    """JSON renderer for machine-readable output."""

    def render(self, payload: dict, output=None) -> str:
        """Render a message payload as JSON."""
        line = json.dumps(payload, separators=(",", ":"))
        if output is not None:
            output.write(line)
            return None
        return line


class PlainRenderer:
    """Plain text renderer."""

    def render(self, payload: dict, output=None):
        msg_type = payload.get("type")
        timestamp = format_timestamp(payload.get("timestamp"))

        if msg_type == "chat":
            sender = payload.get("sender", "?")
            message = payload.get("message", "")
            line = f"{timestamp} {sender}: {message}" if timestamp else f"{sender}: {message}"
            if output is not None:
                output.write(line)
                return None
            return line

        if msg_type == "file_init":
            sender = payload.get("sender", "?")
            filename = payload.get("filename", "")
            filesize = payload.get("filesize")
            size_str = str(filesize) if filesize is not None else ""
            line = f"{sender} sent file {filename} ({size_str})"
            if output is not None:
                output.write(line)
                return None
            return line

        message = payload.get("message", payload.get("data", ""))
        line = f"{timestamp} [system] {message}" if timestamp else f"[system] {message}"
        if output is not None:
            output.write(line)
            return None
        return line


class MarkdownRenderer:
    """Renderer that outputs Markdown-friendly strings."""

    def render(self, payload: dict, output=None):
        msg_type = payload.get("type")
        timestamp = format_timestamp(payload.get("timestamp"))

        if msg_type == "chat":
            sender = payload.get("sender", "?")
            message = payload.get("message", "")
            line = f"**{sender}**: {message}"
            if timestamp:
                line = f"{timestamp} {line}"
            if output is not None:
                output.write(line)
                return None
            return line

        if msg_type == "file_init":
            sender = payload.get("sender", "?")
            filename = payload.get("filename", "")
            filesize = payload.get("filesize")
            line = f"**{sender}** sent `{filename}` ({filesize})"
            if output is not None:
                output.write(line)
                return None
            return line

        message = payload.get("message", payload.get("data", ""))
        line = f"*{message}*"
        if timestamp:
            line = f"{timestamp} {line}"
        if output is not None:
            output.write(line)
            return None
        return line


def create_renderer(renderer_type: str) -> MessageRenderer:
    """Factory function for creating renderers."""
    renderers = {
        "rich": RichRenderer,
        "ascii": AsciiRenderer,
        "minimal": MinimalRenderer,
        "json": JsonRenderer,
        "plain": PlainRenderer,
        "markdown": MarkdownRenderer,
    }

    renderer_class = renderers.get(renderer_type.lower())
    if not renderer_class:
        raise ValueError(
            f"Unknown renderer type: {renderer_type}. "
            f"Valid types: {', '.join(renderers.keys())}"
        )

    return renderer_class()


def get_renderer(name: str):
    """Backward-compatible factory used by tests."""
    try:
        return create_renderer(name)
    except ValueError:
        return PlainRenderer()
