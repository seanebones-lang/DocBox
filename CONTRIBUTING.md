# Contributing to DocBox

Thank you for your interest in contributing to DocBox Healthcare RAG System.

## Code of Conduct

This project adheres to professional standards expected in healthcare software development:
- Write secure, tested code
- Maintain HIPAA compliance
- Follow established architecture patterns
- Document all changes

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/DocBox.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test thoroughly
6. Submit a pull request

## Development Setup

See README.md for detailed setup instructions.

## Pull Request Process

1. **Testing**: All PRs must include tests
   - Minimum 80% code coverage
   - All existing tests must pass
   - Security tests must pass

2. **Code Quality**: 
   - Run `black` for Python formatting
   - Run `prettier` for TypeScript/JavaScript
   - No linter errors

3. **Documentation**:
   - Update API documentation if endpoints change
   - Add/update code comments
   - Update README if user-facing changes

4. **Security**:
   - No hardcoded secrets
   - All PHI handling must be encrypted
   - Audit logging for sensitive operations
   - Pass OWASP security scan

5. **Review**:
   - Minimum 2 approvals required
   - Address all review comments
   - Squash commits before merge

## Commit Messages

Follow conventional commits format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Build process or auxiliary tool changes
- `security:` Security improvements

Example: `feat: add biometric authentication to kiosk`

## Security Issues

**DO NOT** create public issues for security vulnerabilities.

Email security concerns to: security@docbox.health

## Questions?

Open a GitHub Discussion or contact the maintainers.

