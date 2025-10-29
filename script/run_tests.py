#!/usr/bin/env python3
"""Run tests and show results."""
import subprocess
import sys

result = subprocess.run(
    [".venv/bin/pytest", "tests/", "-v", "--tb=short"],
    capture_output=True,
    text=True,
    cwd="/home/snow/dev/cmd-chat"
)

print(result.stdout)
print(result.stderr)
print(f"\nExit code: {result.returncode}")
