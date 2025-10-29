"""Tests for lib.renderers module."""

import pytest
from io import StringIO

from cmdchat.lib.renderers import (
    PlainRenderer,
    RichRenderer,
    MarkdownRenderer,
    get_renderer,
)


class TestPlainRenderer:
    """Test PlainRenderer."""

    def test_render_chat_message(self):
        """Test rendering a chat message."""
        renderer = PlainRenderer()

        output = StringIO()
        msg = {
            "type": "chat",
            "sender": "Alice",
            "message": "Hello!",
            "timestamp": "2024-01-01T12:00:00Z",
        }

        renderer.render(msg, output)
        result = output.getvalue()

        assert "Alice" in result
        assert "Hello!" in result
        # Timestamp is formatted as time only (HH:MM:SS)
        assert ":" in result  # Should contain time format

    def test_render_system_message(self):
        """Test rendering a system message."""
        renderer = PlainRenderer()

        output = StringIO()
        msg = {
            "type": "system",
            "message": "User joined",
        }

        renderer.render(msg, output)
        result = output.getvalue()

        assert "User joined" in result

    def test_render_file_init_message(self):
        """Test rendering a file init message."""
        renderer = PlainRenderer()

        output = StringIO()
        msg = {
            "type": "file_init",
            "sender": "Bob",
            "filename": "test.txt",
            "filesize": 1024,
        }

        renderer.render(msg, output)
        result = output.getvalue()

        assert "Bob" in result
        assert "test.txt" in result
        assert "1024" in result or "1.0" in result  # May be formatted

    def test_render_unknown_message_type(self):
        """Test rendering unknown message type."""
        renderer = PlainRenderer()

        output = StringIO()
        msg = {
            "type": "unknown",
            "data": "something",
        }

        # Should not raise an error
        renderer.render(msg, output)


class TestRichRenderer:
    """Test RichRenderer."""

    def test_render_chat_message(self):
        """Test rendering a chat message with rich formatting."""
        renderer = RichRenderer()

        output = StringIO()
        msg = {
            "type": "chat",
            "sender": "Alice",
            "message": "Hello!",
            "timestamp": "2024-01-01T12:00:00Z",
        }

        renderer.render(msg, output)
        result = output.getvalue()

        # Rich renderer adds formatting, so check for content
        assert "Alice" in result or len(result) > 0

    def test_render_system_message(self):
        """Test rendering a system message with rich formatting."""
        renderer = RichRenderer()

        output = StringIO()
        msg = {
            "type": "system",
            "message": "User joined",
        }

        renderer.render(msg, output)
        result = output.getvalue()

        assert len(result) > 0

    def test_render_file_init_message(self):
        """Test rendering a file init message with rich formatting."""
        renderer = RichRenderer()

        output = StringIO()
        msg = {
            "type": "file_init",
            "sender": "Bob",
            "filename": "test.txt",
            "filesize": 2048,
        }

        renderer.render(msg, output)
        result = output.getvalue()

        assert len(result) > 0


class TestMarkdownRenderer:
    """Test MarkdownRenderer."""

    def test_render_chat_message(self):
        """Test rendering a chat message in markdown."""
        renderer = MarkdownRenderer()

        output = StringIO()
        msg = {
            "type": "chat",
            "sender": "Alice",
            "message": "Hello!",
            "timestamp": "2024-01-01T12:00:00Z",
        }

        renderer.render(msg, output)
        result = output.getvalue()

        # Markdown uses **bold** for sender
        assert "**" in result or "Alice" in result
        assert "Hello!" in result

    def test_render_system_message(self):
        """Test rendering a system message in markdown."""
        renderer = MarkdownRenderer()

        output = StringIO()
        msg = {
            "type": "system",
            "message": "User joined",
        }

        renderer.render(msg, output)
        result = output.getvalue()

        # System messages may use italics
        assert "User joined" in result

    def test_render_file_init_message(self):
        """Test rendering a file init message in markdown."""
        renderer = MarkdownRenderer()

        output = StringIO()
        msg = {
            "type": "file_init",
            "sender": "Bob",
            "filename": "test.txt",
            "filesize": 4096,
        }

        renderer.render(msg, output)
        result = output.getvalue()

        assert "Bob" in result
        assert "test.txt" in result


class TestRendererFactory:
    """Test renderer factory function."""

    def test_get_plain_renderer(self):
        """Test getting plain renderer."""
        renderer = get_renderer("plain")
        assert isinstance(renderer, PlainRenderer)

    def test_get_rich_renderer(self):
        """Test getting rich renderer."""
        renderer = get_renderer("rich")
        assert isinstance(renderer, RichRenderer)

    def test_get_markdown_renderer(self):
        """Test getting markdown renderer."""
        renderer = get_renderer("markdown")
        assert isinstance(renderer, MarkdownRenderer)

    def test_get_renderer_case_insensitive(self):
        """Test that renderer name is case-insensitive."""
        renderer1 = get_renderer("PLAIN")
        renderer2 = get_renderer("Rich")
        renderer3 = get_renderer("MarkDown")

        assert isinstance(renderer1, PlainRenderer)
        assert isinstance(renderer2, RichRenderer)
        assert isinstance(renderer3, MarkdownRenderer)

    def test_get_renderer_default(self):
        """Test that unknown renderer defaults to plain."""
        renderer = get_renderer("unknown")
        assert isinstance(renderer, PlainRenderer)


class TestRendererOutput:
    """Test renderer output formatting."""

    def test_plain_no_ansi_codes(self):
        """Test that plain renderer produces no ANSI codes."""
        renderer = PlainRenderer()

        output = StringIO()
        msg = {
            "type": "chat",
            "sender": "Alice",
            "message": "Test",
            "timestamp": "2024-01-01T12:00:00Z",
        }

        renderer.render(msg, output)
        result = output.getvalue()

        # Plain renderer should not have ANSI escape codes
        assert "\x1b[" not in result

    def test_renderers_produce_output(self):
        """Test that all renderers produce some output."""
        msg = {
            "type": "chat",
            "sender": "Alice",
            "message": "Test",
            "timestamp": "2024-01-01T12:00:00Z",
        }

        for renderer_name in ["plain", "rich", "markdown"]:
            renderer = get_renderer(renderer_name)
            output = StringIO()

            renderer.render(msg, output)
            result = output.getvalue()

            assert len(result) > 0, f"{renderer_name} produced no output"


class TestRendererEdgeCases:
    """Test edge cases for renderers."""

    def test_render_empty_message(self):
        """Test rendering a message with empty text."""
        renderer = PlainRenderer()

        output = StringIO()
        msg = {
            "type": "chat",
            "sender": "Alice",
            "message": "",
            "timestamp": "2024-01-01T12:00:00Z",
        }

        # Should not raise an error
        renderer.render(msg, output)

    def test_render_missing_fields(self):
        """Test rendering with missing fields."""
        renderer = PlainRenderer()

        output = StringIO()
        msg = {
            "type": "chat",
            # Missing sender and message
        }

        # Should not raise an error
        renderer.render(msg, output)

    def test_render_special_characters(self):
        """Test rendering with special characters."""
        renderer = PlainRenderer()

        output = StringIO()
        msg = {
            "type": "chat",
            "sender": "Alice<>",
            "message": "Test & special chars: <script>alert('xss')</script>",
            "timestamp": "2024-01-01T12:00:00Z",
        }

        # Should not raise an error
        renderer.render(msg, output)
        result = output.getvalue()

        # Content should be present
        assert "Alice" in result
        assert "special chars" in result
