#!/usr/bin/env python3
"""Run tests with coverage and show summary."""
import subprocess
import sys

# Run tests with coverage
result = subprocess.run(
    [
        ".venv/bin/pytest",
        "tests/",
        "--cov=cmdchat",
        "--cov-report=term",
        "--cov-report=html",
        "-v",
        "--tb=short"
    ],
    capture_output=False,
    text=True,
    cwd="/home/snow/dev/cmd-chat"
)

sys.exit(result.returncode)
