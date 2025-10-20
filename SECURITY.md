# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: security@docbox.health

Include the following information:
- Type of vulnerability
- Full path of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue

## Security Measures

### Data Protection
- AES-256 encryption for data at rest
- TLS 1.3 for data in transit
- Field-level encryption for highly sensitive data (SSN, genomic)
- Encrypted database backups

### Authentication & Authorization
- JWT with short expiration (15 minutes)
- Refresh tokens (7 days)
- Multi-factor authentication (TOTP)
- WebAuthn/passkey support
- Role-based access control (RBAC)
- Automatic session timeout (30 minutes)

### Audit & Compliance
- Comprehensive audit logging
- 7-year retention for HIPAA compliance
- Immutable blockchain audit trail (optional)
- Regular security assessments
- HIPAA compliance validation
- GDPR compliance features

### Infrastructure Security
- Container security scanning
- Dependency vulnerability scanning
- Regular penetration testing
- WAF (Web Application Firewall)
- DDoS protection
- Intrusion detection system

### Development Practices
- Security code reviews
- OWASP Top 10 protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection

## Compliance Certifications

- HIPAA (planned)
- GDPR (planned)
- SOC 2 (planned)

## Security Updates

Security updates are released as needed. Subscribe to repository notifications to stay informed.

## Contact

For security inquiries: security@docbox.health
For general support: support@docbox.health

