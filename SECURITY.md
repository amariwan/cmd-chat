# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please follow these steps:

1. **DO NOT** open a public issue
2. Email the details to: security@cmdchat.dev (replace with actual email)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to address the issue.

## Security Measures

CmdChat implements the following security measures:

- **Encryption**: AES-256-GCM for message encryption
- **Key Exchange**: RSA 4096-bit for secure key exchange
- **Password Security**: Argon2id for password hashing
- **TLS**: TLS 1.3 for transport security
- **Input Validation**: All inputs are sanitized and validated
- **Rate Limiting**: Protection against spam and DoS
- **Security Scanning**: Automated Bandit scans in CI/CD
- **Dependency Checks**: Regular dependency security audits

## Security Best Practices

When using CmdChat:

1. Use strong passwords
2. Keep your client software updated
3. Verify server certificates
4. Use secure networks
5. Don't share encryption keys

## Disclosure Policy

- Security issues are handled privately until a fix is available
- We credit researchers who report valid vulnerabilities
- Fixes are released as soon as possible
- Public disclosure occurs after fix deployment

Thank you for helping keep CmdChat secure!
