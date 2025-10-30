# Makefile that mirrors the justfile commands for CmdChat

SHELL := /bin/bash

# ---- Tools from venv (override if nötig) ----
VENV ?= .venv
PYTHON      ?= $(VENV)/bin/python
PIP         ?= $(VENV)/bin/pip
PYTEST      ?= $(VENV)/bin/pytest
BLACK       ?= $(VENV)/bin/black
RUFF        ?= $(VENV)/bin/ruff
MYPY        ?= $(VENV)/bin/mypy
BANDIT      ?= $(VENV)/bin/bandit
SAFETY      ?= $(VENV)/bin/safety
PRE_COMMIT  ?= $(VENV)/bin/pre-commit
PTW         ?= $(VENV)/bin/ptw
TWINE       ?= $(VENV)/bin/twine
CMDCHAT_SERVER ?= $(VENV)/bin/cmdchat-server
CMDCHAT_CLIENT ?= $(VENV)/bin/cmdchat-client

# ---- Runtime vars (overridable like just env()) ----
HOST ?= 0.0.0.0
PORT ?= 8888
NAME ?= anon
CERTFILE ?=
KEYFILE  ?=
FILE ?=
PATTERN ?=

.PHONY: help default install setup-hooks setup fmt lint typecheck security \
        pre-commit check test test-cov test-parallel test-file test-match test-watch \
        test-e2e test-e2e-full \
        server server-tls server-debug client client-named client-rich client-json \
        gen-certs clean stats update-deps ci-local dev build publish-test publish \
        docs-cat refactoring set-tokens

# Default: list available targets
default: help
help:
	@echo "Available targets:"
	@echo "  install            - pip install -e '.[dev]'"
	@echo "  setup              - install + pre-commit install"
	@echo "  fmt | lint | typecheck | security | pre-commit | check"
	@echo "  test | test-cov | test-parallel | test-file FILE=... | test-match PATTERN=... | test-watch"
	@echo "  test-e2e           - Run E2E integration tests"
	@echo "  test-e2e-full      - Run complete E2E test script"
	@echo "  server [HOST,PORT] | server-debug | server-tls CERTFILE=... KEYFILE=..."
	@echo "  client | client-named NAME=... | client-rich | client-json"
	@echo "  gen-certs | clean | stats | update-deps | ci-local | dev"
	@echo "  build | publish-test | publish"
	@echo "  docs-cat (cat ARCHITECTURE.md) | refactoring (cat REFACTORING_COMPLETE.md)"
	@echo "  set-tokens TOKENS='...'  (nur im Subshell sichtbar)"

# --- Development Setup ---
install:
	$(PIP) install -e '.[dev]'


setup-hooks:
	$(PRE_COMMIT) install
	@echo "✅ Pre-commit hooks installed"

setup: install setup-hooks
	@echo "✅ Development environment ready!"

# --- Code Quality ---
fmt:
	$(BLACK) cmdchat tests
	$(RUFF) check --fix cmdchat tests
	@echo "✅ Code formatted"

lint:
	$(RUFF) check cmdchat tests
	$(BLACK) --check cmdchat tests
	@echo "✅ Linting passed"

lint-fix:
	$(RUFF) check --fix cmdchat tests
	@echo "✅ Linting issues fixed"

typecheck:
	$(MYPY) cmdchat --strict --ignore-missing-imports
	@echo "✅ Type checking passed"

fix-all:
	$(RUFF) check --fix cmdchat tests
	$(BLACK) cmdchat tests
	@echo "✅ All fixable issues resolved"

security:
	$(BANDIT) -r cmdchat -ll
	-$(SAFETY) check
	@echo "✅ Security scan complete"

pre-commit:
	$(PRE_COMMIT) run --all-files

check: lint typecheck security
	@echo "✅ All quality checks passed!"

# --- Testing ---
test:
	$(PYTEST) -v

test-cov:
	$(PYTEST) --cov=cmdchat --cov-report=html --cov-report=term-missing --cov-fail-under=95

test-parallel:
	$(PYTEST) -n auto -v

test-file:
	@if [ -z "$(FILE)" ]; then echo "ERROR: provide FILE=..."; exit 1; fi
	$(PYTEST) -v $(FILE)

test-match:
	@if [ -z "$(PATTERN)" ]; then echo "ERROR: provide PATTERN=..."; exit 1; fi
	$(PYTEST) -k '$(PATTERN)' -v

test-watch:
	$(PTW) -v

test-e2e:
	@echo "Running E2E integration tests..."
	$(PYTEST) tests/test_e2e_integration.py -v

test-e2e-full:
	@echo "Running full E2E test script..."
	./test_e2e.sh

test-all:
	@echo "Running all tests..."
	$(PYTEST) -v
	@$(MAKE) test
	@$(MAKE) test-parallel
	@$(MAKE) test-cov
	@$(MAKE) test-e2e
	@$(MAKE) test-e2e-full


	@echo "✅ All tests passed!"

# --- Server ---
server:
	@test -f $(CMDCHAT_SERVER) || { echo "❌ cmdchat-server not found. Run 'make install' first."; exit 1; }
	$(CMDCHAT_SERVER) --host $(HOST) --port $(PORT)

server-tls:
	@test -f $(CMDCHAT_SERVER) || { echo "❌ cmdchat-server not found. Run 'make install' first."; exit 1; }
	@if [ -z "$(CERTFILE)" ] || [ -z "$(KEYFILE)" ]; then echo "ERROR: provide CERTFILE=... KEYFILE=..."; exit 1; fi
	$(CMDCHAT_SERVER) --host $(HOST) --port $(PORT) --certfile $(CERTFILE) --keyfile $(KEYFILE)

server-debug:
	@test -f $(CMDCHAT_SERVER) || { echo "❌ cmdchat-server not found. Run 'make install' first."; exit 1; }
	$(CMDCHAT_SERVER) --log-level DEBUG --host $(HOST) --port $(PORT)

# --- Client ---
client:
	@test -f $(CMDCHAT_CLIENT) || { echo "❌ cmdchat-client not found. Run 'make install' first."; exit 1; }
	$(CMDCHAT_CLIENT) --host $(HOST) --port $(PORT)

client-named:
	@test -f $(CMDCHAT_CLIENT) || { echo "❌ cmdchat-client not found. Run 'make install' first."; exit 1; }
	$(CMDCHAT_CLIENT) --host $(HOST) --port $(PORT) --name $(NAME)

client-rich:
	@test -f $(CMDCHAT_CLIENT) || { echo "❌ cmdchat-client not found. Run 'make install' first."; exit 1; }
	$(CMDCHAT_CLIENT) --host $(HOST) --port $(PORT) --renderer rich

client-json:
	@test -f $(CMDCHAT_CLIENT) || { echo "❌ cmdchat-client not found. Run 'make install' first."; exit 1; }
	$(PYTHON) -m cmdchat.client --renderer json --host $(HOST) --port $(PORT)

# --- Utility ---
gen-certs:
	openssl req -x509 -newkey rsa:4096 -nodes \
	  -keyout server-key.pem -out server-cert.pem \
	  -days 365 -subj "/CN=localhost"
	@echo "✅ Generated server-cert.pem and server-key.pem"

clean:
	rm -rf build/ dist/ *.egg-info htmlcov/ .coverage .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleaned build artifacts"

stats:
	@echo "=== Project Statistics ==="
	@echo "Python files: $$(find cmdchat -name '*.py' | wc -l)"
	@echo "Test files:   $$(find tests -name 'test_*.py' | wc -l)"
	@echo "Total lines:  $$(find cmdchat -name '*.py' -exec wc -l {} + | awk '{s+=$$1} END {print s+0}')"
	@echo "Coverage: Run 'make test-cov' to see coverage report"

update-deps:
	$(PIP) install --upgrade pip
	$(PIP) install --upgrade -e '.[dev]'
	$(PRE_COMMIT) autoupdate
	@echo "✅ Dependencies updated"

ci-local: fmt lint typecheck security test-cov
	@echo "✅ All CI checks passed locally!"

dev: fmt test
	@echo "✅ Quick dev check complete!"

# --- Build & Publish ---
build: clean
	$(PYTHON) -m build
	$(TWINE) check dist/*
	@echo "✅ Package built successfully"

publish-test: build
	$(TWINE) upload --repository testpypi dist/*

publish: build
	$(TWINE) upload dist/*

# --- Docs (as in justfile: cat files) ---
docs-cat:
	@cat ARCHITECTURE.md || echo "ARCHITECTURE.md not found"

refactoring:
	@cat REFACTORING_COMPLETE.md || echo "REFACTORING_COMPLETE.md not found"

# --- Security / Tokens ---
set-tokens:
	@if [ -z "$$TOKENS" ]; then echo "Usage: make set-tokens TOKENS='...'" ; exit 1; fi
	@echo "CMDCHAT_TOKENS=$$TOKENS (nur im Subshell gesetzt)"
	@export CMDCHAT_TOKENS="$$TOKENS"
	@echo "✅ CMDCHAT_TOKENS set in subshell"
