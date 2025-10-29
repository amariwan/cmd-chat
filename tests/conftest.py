"""Test configuration and fixtures for cmdchat tests."""

import asyncio
from pathlib import Path
from typing import AsyncIterator

import pytest


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
