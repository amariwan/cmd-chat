# Multi-stage build for CMD Chat
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY cmdchat/ ./cmdchat/

# Build wheel
RUN pip install --no-cache-dir build && \
    python -m build --wheel

# Runtime stage
FROM python:3.11-slim

LABEL org.opencontainers.image.title="CMD Chat"
LABEL org.opencontainers.image.description="Secure in-memory console chat"
LABEL org.opencontainers.image.source="https://github.com/amariwan/cmd-chat"

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash cmdchat

WORKDIR /app

# Copy wheel from builder
COPY --from=builder /build/dist/*.whl /tmp/

# Install the package
RUN pip install --no-cache-dir /tmp/*.whl && \
    rm -rf /tmp/*.whl

# Switch to non-root user
USER cmdchat

# Expose default port
EXPOSE 5050

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import socket; s = socket.socket(); s.settimeout(2); s.connect(('localhost', 5050)); s.close()" || exit 1

# Default command runs the server
ENTRYPOINT ["cmdchat-server"]
CMD ["--host", "0.0.0.0", "--port", "5050", "--metrics-interval", "60"]
