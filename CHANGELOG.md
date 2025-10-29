# Changelog

All notable changes to CMD Chat will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-29

### Added

#### Features
- **File transfer support** - Encrypted file sharing up to 10MB via `/send` command
  - Chunked transfer with progress tracking
  - Automatic download to `~/Downloads/cmdchat/`
  - Real-time progress indicators
  - Base64 encoding for binary safety

#### Security
- **Enhanced logging security** - No sensitive data in logs
  - Token sanitization (shows `abc1...xyz9` instead of full token)
  - Data truncation for long strings in logs
  - Custom log formatter to prevent leaks
  - `CMDCHAT_METRICS` environment variable to disable metrics
  - Sanitized connection attempt logging

#### Deployment
- **Docker support** - Production-ready containerization
  - Multi-stage Dockerfile with security hardening
  - Non-root user execution
  - Health check integration
  - Resource limits (512MB memory, 1 CPU)
  - `.dockerignore` for optimized builds

- **Docker Compose** - Full orchestration
  - Service definition with health checks
  - Environment variable configuration
  - TLS support (commented, ready to enable)
  - Optional nginx reverse proxy setup
  - Network isolation

- **Systemd service** - Native Linux service
  - Security-hardened unit file
  - Non-root execution
  - Automatic restart on failure
  - Resource limits
  - Complete installation guide

#### Documentation
- **Comprehensive README** - Complete project documentation
  - Security considerations and limitations
  - Deployment options (local, Docker, systemd)
  - Configuration examples
  - Troubleshooting guide
  - Performance metrics

- **QUICKSTART.md** - 5-minute getting started guide
  - Step-by-step installation
  - Common commands
  - Docker quick start
  - Troubleshooting tips

- **SYSTEMD_INSTALL.md** - Production deployment guide
  - Complete installation steps
  - TLS certificate setup
  - Service management
  - Log rotation
  - Health checks
  - Firewall configuration

- **FEATURES.md** - Feature tracking and roadmap
  - Implementation status of all features
  - Technical debt tracking
  - Performance benchmarks
  - Future enhancement ideas

- **IMPLEMENTATION_SUMMARY.md** - Project summary
  - Complete feature list
  - Deployment options
  - Security enhancements
  - Quick reference commands

#### Infrastructure
- `.env.example` - Environment configuration template
- Enhanced `crypto.py` with file chunking constants
- Message sequence tracking for future delta updates
- File transfer state management in sessions

### Changed
- Updated client help message to include `/send` command
- Enhanced server logging with sanitization
- Updated connection welcome message

### Fixed
- Log level configuration now properly applied
- Metrics can be disabled via environment variable

## [0.0.1] - Prior to 2025-10-29

### Existing Features (Already Implemented)

#### Core Stability
- JSON message serialization
- Heartbeat with ping/pong (15s interval, 45s timeout)
- Clean error handling without stack traces
- Rate limiting (12 messages per 5 seconds)
- Message size limits (4KB messages, 64KB frames)

#### Security
- Per-client AES-256-GCM symmetric keys
- RSA-2048 asymmetric encryption for key exchange
- Token-based authentication via `CMDCHAT_TOKENS`
- TLS/WSS transport encryption support
- Memory-only operation (no disk persistence)

#### Chat Features
- Multiple chat rooms with `/join` command
- User commands: `/nick`, `/join`, `/clear`, `/help`, `/quit`
- UTC timestamps on all messages
- Per-room message sequence numbers
- Automatic reconnection with backoff

#### Client Features
- Local encrypted history with `--history-file`
- Three renderer modes: `rich`, `minimal`, `json`
- Quiet reconnect mode via `--quiet-reconnect`
- Configurable message buffer (10-1000 messages)
- Customizable client name and room

#### Server Features
- Asynchronous I/O with asyncio
- Graceful shutdown on SIGINT/SIGTERM
- Optional metrics logging (connections, msg/sec)
- Configurable host, port, and TLS settings
- Automatic client session cleanup

## [Unreleased]

### Future Enhancements
- Delta updates for message synchronization
- Typing indicators
- User list command (`/who`)
- Message search in history
- uvloop integration for performance
- Multi-server federation

---

## Version History

- **0.1.0** (2025-10-29) - Production-ready release with file transfer, deployment options, and enhanced security
- **0.0.1** (Prior) - Initial implementation with core chat features

## Migration Guide

### From 0.0.1 to 0.1.0

No breaking changes! All existing functionality is preserved.

**New features available:**
1. Use `/send <filepath>` to transfer files
2. Deploy with `docker-compose up -d`
3. Install as systemd service (see `SYSTEMD_INSTALL.md`)
4. Disable metrics with `CMDCHAT_METRICS=0`

**Recommended actions:**
1. Review the updated `README.md` for new features
2. Consider Docker or systemd deployment for production
3. Enable TLS for remote connections
4. Set up token authentication for security

## Contributing

See the main [README.md](README.md) for contribution guidelines.

## License

MIT License - See LICENSE file for details.
