# Contributing to OSLW

Thank you for your interest in contributing to OSLW! This document provides guidelines and instructions for contributing.

## 🎯 How to Contribute

### Reporting Bugs

Before creating a bug report:
1. **Search existing issues** — check if the problem is already reported
2. **Verify the issue** — reproduce it locally if possible
3. **Gather information** — include logs, screenshots, steps to reproduce

When creating a bug report, include:
- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Logs or error messages

### Suggesting Features

Feature suggestions are welcome! Please include:
- Clear description of the feature
- Use case or problem it solves
- Any relevant examples or mockups
- Potential implementation approaches (optional)

### Code Contributions

1. **Fork** the repository
2. **Create a feature branch** from `main`
3. **Make your changes** following the guidelines below
4. **Write/update tests** for your changes
5. **Update documentation** as needed
6. **Submit a pull request**

## 📋 Development Guidelines

### Code Style

#### Python
- Follow **PEP 8** conventions
- Use **type hints** for all function parameters and return values
- Maximum line length: **88 characters** (Black formatter)
- Use **f-strings** for string formatting
- Import groups: `stdlib → third-party → local`

```python
# ✅ Good
from pathlib import Path
from typing import Optional

from oslw.config import settings


async def get_page(slug: str) -> Optional[WikiPage]:
    """Retrieve a wiki page by slug.

    Args:
        slug: Page slug identifier

    Returns:
        WikiPage if found, None otherwise
    """
    page_path = Path(settings.wiki_root) / f"{slug}.md"
    if not page_path.exists():
        return None
    return await WikiPage.from_file(page_path)
```

#### JavaScript/JSX
- Use **functional components** with hooks
- Follow **React best practices**
- Use **Tailwind CSS** for styling
- Keep components **small and focused**

### Git Workflow

#### Branch Naming
```
feature/<name>      # New features
fix/<name>          # Bug fixes
docs/<name>         # Documentation changes
refactor/<name>     # Code refactoring
test/<name>         # Test additions
chore/<name>        # Maintenance tasks
```

#### Commit Messages
Follow **Conventional Commits** format:

```
<type>: <description>

Optional body with details.

Types:
  feat:     New feature
  fix:      Bug fix
  docs:     Documentation
  test:     Tests
  refactor: Code refactoring
  chore:    Maintenance
  style:    Code style (formatting, semicolons, etc.)
```

Examples:
```bash
feat: add graph visualization component
fix: resolve wiki link case sensitivity issue
docs: update API documentation for search endpoint
test: add integration tests for digest service
```

### Testing Requirements

All new code must include tests:
- **Domain logic**: Unit tests
- **API endpoints**: Integration tests
- **CLI commands**: Command tests
- **Edge cases**: Boundary condition tests

#### Test Quality Checklist
- [ ] Tests cover happy path
- [ ] Tests cover error paths
- [ ] Tests are deterministic
- [ ] Tests use meaningful names
- [ ] Tests have clear assertions
- [ ] No test dependencies on execution order

#### Running Tests
```bash
# All tests
make test

# Fast tests (no coverage)
make test-fast

# Specific test file
pytest tests/domain/test_page.py -v

# With coverage
pytest tests/ --cov=src/oslw --cov-report=html
```

### Documentation Requirements

Every PR should update documentation if it changes:
- **API changes**: Update `docs/api.md`
- **New features**: Update `docs/usage.md`
- **Architecture changes**: Update `docs/architecture/ARCHITECTURE.md`
- **CLI changes**: Update help text and examples

## 🔍 Code Review Process

### For Contributors
1. Ensure your PR passes all CI checks
2. Address all review comments
3. Keep PRs focused and small
4. Provide clear PR description
5. Link related issues

### For Reviewers
1. Review within 24 hours when possible
2. Provide constructive feedback
3. Ask questions, don't make demands
4. Approve when changes are addressed
5. Request changes with clear rationale

### PR Template
```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for changes
- [ ] Edge cases covered

## Documentation
- [ ] Documentation updated
- [ ] Examples provided
- [ ] Changelog updated

## Screenshots (if applicable)
Add screenshots of UI changes.
```

## 🚀 Deployment

### Release Process
1. Update `CHANGELOG.md`
2. Update version in `pyproject.toml`
3. Create release branch
4. Run full test suite
5. Create GitHub release
6. Tag the release

### Versioning
Follow **Semantic Versioning**:
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes

## 📚 Resources

- [Development Guide](DEVELOPMENT.md) — Detailed development workflow
- [Architecture Docs](architecture/ARCHITECTURE.md) — System architecture
- [API Reference](api.md) — API endpoints documentation
- [Usage Guide](usage.md) — User guide and examples

## ❓ Getting Help

- **GitHub Issues**: Report bugs or request features
- **GitHub Discussions**: Ask questions or share ideas
- **Code of Conduct**: All contributors must follow our CoC

## 🙏 Thank You!

Your contributions make OSLW better for everyone. Every bug report, feature suggestion, and code contribution is valued.

---

**Last Updated**: 2026-08-05
