# CMD Chat

[![CI/CD Pipeline](https://github.com/amariwan/cmd-chat/actions/workflows/ci.yml/badge.svg)](https://github.com/amariwan/cmd-chat/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/amariwan/cmd-chat/branch/master/graph/badge.svg)](https://codecov.io/gh/amariwan/cmd-chat)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A fully anonymous, encrypted console chat that exists only in memory.**

CMD Chat is a new milestone in console communication - a secure, memory-only chat system designed for ephemeral conversations between trusted peers. All data exists only in RAM and is wiped after the session ends. No logs, no traces, no compromise.

## 🔒 Key Features

### Security & Privacy
- **Full anonymity** – clients identify themselves with disposable screen names
- **End-to-End encryption** – RSA-2048 handshake + per-client AES-GCM session keys
- **Per-client symmetric keys** – unique encryption for every connected user
- **Data stored only in memory (RAM)** – nothing written to disk by default
- **No logging, no persistence** – server forgets everything on disconnect
- **Token-based authentication** – optional invite/bearer token gating
- **TLS support** – secure transport layer with WSS capability

### Chat Features
- **Multiple rooms** – isolated chat spaces with `/join` command
- **Real-time messaging** – instant encrypted message relay
- **File transfer** – encrypted file sharing via chunked transfer (up to 10MB)
- **Commands** – `/nick`, `/join`, `/send`, `/clear`, `/help`, `/quit`
- **Message timestamps** – UTC timestamps with sequence numbers
- **Heartbeat & reconnection** – automatic ping/pong with graceful reconnect
- **Rate limiting** – built-in anti-spam protection

### User Experience
- **Customizable renderers** – choose between `rich`, `minimal`, or `json` output modes
- **Local encrypted history** – optional client-side encrypted message storage
- **Configurable message buffer** – retain 10-1000 messages locally
- **Quiet reconnect mode** – minimal status messages during reconnection
- **Progress indicators** – file transfer progress tracking

### Operations & Deployment
- **Docker support** – production-ready containerization
- **Systemd integration** – native Linux service deployment
- **Metrics logging** – optional connection and throughput monitoring
- **Resource limits** – configurable memory and CPU constraints
- **Graceful shutdown** – clean session termination
- **Security hardening** – sanitized logging, no sensitive data leakage

## ⚙️ How It Works

1. **Client generates RSA keypair** – Fresh 2048-bit RSA keys per session
2. **Handshake** – Client sends public key, room preferences, and optional token
3. **Server creates symmetric key** – Unique AES-256 key for each client
4. **Key exchange** – Server encrypts symmetric key with client's public key
5. **Client decrypts** – Client retrieves the session key using private key
6. **Encrypted communication** – All messages use AES-GCM with fresh nonces
7. **Server relay** – Messages are decrypted, re-encrypted per recipient, and forwarded
8. **Memory-only operation** – No disk writes unless metrics/history enabled

Everything happens in memory only. Nothing is written to disk by the server.

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/amariwan/cmd-chat.git
cd cmd-chat

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install
pip install -e .
```

### Basic Usage

**Start the server** (defaults to `127.0.0.1:5050`):

```bash
cmdchat-server
```

**Connect a client**:

```bash
cmdchat-client --name alice
```

**Open another terminal for a second participant**:

```bash
cmdchat-client --name bob
```

Type messages and press Enter to send. Use `/help` to see available commands.

### Available Commands

- `/nick <name>` – Change your display name
- `/join <room>` – Switch to a different room
- `/send <filepath>` – Send a file to the room (encrypted, up to 10MB)
- `/clear` – Clear your local message buffer
- `/help` – Show command help
- `/quit` – Disconnect and exit

## 🔐 Authentication & TLS

### Token Authentication

Require invite/bearer tokens for access:

```bash
# Generate secure tokens
export CMDCHAT_TOKENS="$(openssl rand -hex 32),$(openssl rand -hex 32)"

# Start server with token auth
cmdchat-server
```

Connect with a token:

```bash
cmdchat-client --name alice --token <your-token>
```

### TLS Encryption

**Generate self-signed certificate** (for testing):

```bash
openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt \
    -days 365 -nodes -subj "/CN=localhost"
```

**Start server with TLS**:

```bash
cmdchat-server --certfile server.crt --keyfile server.key
```

**Connect client with TLS**:

```bash
cmdchat-client --name alice --tls --tls-insecure  # For self-signed certs
```

**Production with Let's Encrypt**:

```bash
cmdchat-server \
    --certfile /etc/letsencrypt/live/your-domain/fullchain.pem \
    --keyfile /etc/letsencrypt/live/your-domain/privkey.pem
```

## 📊 Server Options

```bash
cmdchat-server --help
```

Key options:
- `--host <addr>` – Bind address (default: 127.0.0.1)
- `--port <port>` – Listen port (default: 5050)
- `--certfile <path>` – TLS certificate file (PEM)
- `--keyfile <path>` – TLS private key file (PEM)
- `--metrics-interval <seconds>` – Log metrics every N seconds (0 disables)

### Environment Variables

- `CMDCHAT_TOKENS` – Comma-separated authentication tokens
- `CMDCHAT_LOG_LEVEL` – Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `CMDCHAT_METRICS` – Enable/disable metrics (1=enabled, 0=disabled)

## 💻 Client Options

```bash
cmdchat-client --help
```

Key options:
- `--host <addr>` – Server host (default: 127.0.0.1)
- `--port <port>` – Server port (default: 5050)
- `--name <name>` – Display name (default: anonymous)
- `--room <room>` – Initial room (default: lobby)
- `--token <token>` – Authentication token
- `--renderer <mode>` – Output style: rich, minimal, json (default: rich)
- `--buffer-size <n>` – Message buffer size 10-1000 (default: 200)
- `--tls` – Enable TLS connection
- `--tls-insecure` – Skip certificate verification (testing only)
- `--ca-file <path>` – Custom CA bundle
- `--history-file <path>` – Local encrypted history file
- `--history-passphrase <pass>` – Passphrase for history encryption
- `--quiet-reconnect` – Minimal reconnection messages

## 🐳 Docker Deployment

### Quick Start with Docker

```bash
# Build image
docker build -t cmdchat .

# Run server
docker run -d --name cmdchat-server \
    -p 5050:5050 \
    -e CMDCHAT_TOKENS="your-secret-token" \
    cmdchat
```

### Docker Compose

```bash
# Copy environment template
cp .env.example .env
# Edit .env with your tokens

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

For TLS with Docker, uncomment the TLS section in `docker-compose.yml` and mount your certificates.

## 🖥️ Systemd Service

For production Linux deployments, see [SYSTEMD_INSTALL.md](SYSTEMD_INSTALL.md) for complete installation instructions.

**Quick setup**:

```bash
# Install service
sudo cp cmdchat-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cmdchat-server
sudo systemctl start cmdchat-server

# View status
sudo systemctl status cmdchat-server

# View logs
sudo journalctl -u cmdchat-server -f
```

## 🛡️ Security Considerations

### What CMD Chat Provides
- ✅ End-to-end encryption between clients and server
- ✅ Per-client session keys (no shared global key)
- ✅ Memory-only operation (no disk persistence by default)
- ✅ No logging of message content
- ✅ Token-based authentication
- ✅ TLS transport encryption
- ✅ Rate limiting and message size limits
- ✅ Sanitized logging (no token/key exposure)

### Important Limitations
- ⚠️ The server can decrypt messages (not peer-to-peer E2EE)
- ⚠️ Server admin has full access to plaintext in RAM
- ⚠️ Memory can be dumped if server is compromised
- ⚠️ Use TLS in production to prevent MITM attacks
- ⚠️ Tokens should be generated with strong randomness
- ⚠️ File transfers are limited to 10MB
- ⚠️ No forward secrecy (session keys don't rotate)

### Best Practices
1. **Always use TLS in production** with valid certificates
2. **Generate strong tokens**: `openssl rand -hex 32`
3. **Run server as non-root user** (systemd service does this)
4. **Use firewall rules** to limit server access
5. **Enable metrics carefully** (logs connection counts, not content)
6. **Rotate tokens regularly** for long-running deployments
7. **Use encrypted history only on trusted devices**

## 📈 Performance & Limits

### Default Limits
- **Max message size**: 4 KB
- **Max file size**: 10 MB
- **Rate limit**: 12 messages per 5 seconds per client
- **Heartbeat interval**: 15 seconds
- **Heartbeat timeout**: 45 seconds
- **Message buffer**: 200 messages (client-side)
- **Max frame size**: 64 KB (protocol)

### Resource Usage
- **Memory**: ~512 MB recommended for server
- **CPU**: Minimal, single-threaded async I/O
- **Network**: Low bandwidth, depends on usage

## 🧪 Development

### Running Tests

```bash
# Syntax check
python -m compileall cmdchat

# Type checking (if mypy installed)
mypy cmdchat/

# Format code (if black installed)
black cmdchat/
```

### Project Structure

```
cmd-chat/
├── cmdchat/
│   ├── __init__.py
│   ├── server.py          # Server implementation
│   ├── client.py          # Client implementation
│   ├── crypto.py          # Cryptographic utilities
│   └── protocol.py        # Message framing
├── Dockerfile             # Container image
├── docker-compose.yml     # Docker orchestration
├── cmdchat-server.service # Systemd unit file
├── pyproject.toml        # Project metadata
└── README.md
```

## 📝 License

MIT License - see LICENSE file for details.

## 🙏 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📚 Additional Resources

- [Systemd Installation Guide](SYSTEMD_INSTALL.md)
- [Docker Deployment Guide](docker-compose.yml)
- [Environment Configuration](.env.example)

## ⚡ Troubleshooting

### Connection refused
```bash
# Check if server is running
netstat -tuln | grep 5050

# Check firewall
sudo ufw status
```

### Authentication failed
```bash
# Verify token matches on client and server
echo $CMDCHAT_TOKENS  # Server side
```

### File transfer fails
```bash
# Check file size (max 10MB)
ls -lh yourfile

# Check file permissions
chmod +r yourfile
```

### TLS certificate errors
```bash
# For testing, use --tls-insecure
cmdchat-client --tls --tls-insecure

# For production, verify certificate
openssl s_client -connect your-server:5050
```

## 🎯 Roadmap

See the project issues for planned features and improvements.

---

**CMD CHAT** - Secure, ephemeral console communication with zero compromise.
