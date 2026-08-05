# OSLW Development Guide

## 🎯 Project Overview

**OSLW** (Open Source Lightweight Wiki) — модульна система для управління wiki-базами знань, побудована за принципами Clean Architecture.

### Tech Stack
- **Backend**: Python 3.11+, FastAPI, Typer, Pydantic
- **Frontend**: Next.js 15, React, Tailwind CSS, Cytoscape.js
- **Storage**: File-based (Markdown + JSON)
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **CI/CD**: GitHub Actions

## 📁 Project Structure

```
oslw/
├── src/oslw/                    # Python package
│   ├── config/                  # Configuration & settings
│   │   ├── settings.py          # Pydantic BaseSettings
│   │   └── logging.py           # Logging setup
│   ├── core/                    # Domain primitives
│   │   ├── events.py            # Event system
│   │   └── exceptions.py        # Custom exceptions
│   ├── domain/                  # Business logic (framework-agnostic)
│   │   ├── wiki/                # Wiki pages, index, integrity
│   │   │   ├── page.py          # WikiPage model
│   │   │   ├── index.py         # WikiIndex model
│   │   │   └── integrity.py     # SHA256, wikilinks validation
│   │   ├── sources/             # Source monitoring & ingestion
│   │   │   ├── monitor.py       # SourceConfig, SourceMonitor
│   │   │   └── ingest.py        # ContentIngestor
│   │   ├── graph/               # Knowledge graph
│   │   │   ├── graph.py         # Graph model
│   │   │   └── query.py         # Graph queries
│   │   ├── quality/             # Quality assurance
│   │   │   ├── doctor.py        # WikiDoctor diagnostics
│   │   │   ├── lint.py          # Page linting
│   │   │   └── cleanup.py       # Deduplication
│   │   └── digest/              # Newspaper digest
│   │       └── digest.py        # Digest generation
│   ├── infrastructure/          # External integrations
│   │   ├── database.py          # FileManager (file operations)
│   │   └── git_manager.py       # Git operations
│   ├── application/             # Use-case services
│   │   ├── page_service.py      # CRUD operations
│   │   ├── index_service.py     # Index management
│   │   ├── integrity_service.py # Integrity checks
│   │   ├── graph_service.py     # Graph operations
│   │   ├── quality_service.py   # Quality monitoring
│   │   ├── digest_service.py    # Digest generation
│   │   └── source_service.py    # Source management
│   ├── api/                     # REST API
│   │   ├── app.py               # FastAPI entry point
│   │   └── v1/
│   │       └── endpoints/       # 7 endpoint modules
│   ├── cli/                     # CLI commands
│   │   └── commands.py          # Typer CLI (7 commands)
│   └── cron/                    # Scheduled jobs
│       ├── scheduler.py         # Async scheduler
│       └── jobs.py              # 6 cron jobs
├── frontend/                    # Next.js SPA
│   ├── src/
│   │   ├── components/          # 6 React components
│   │   ├── services/            # API client
│   │   └── App.jsx              # Main app
├── tests/                       # Pytest tests
│   ├── domain/                  # Domain tests
│   ├── cron/                    # Cron tests
│   └── conftest.py              # Test fixtures
├── docs/                        # Documentation
│   ├── api.md                   # API reference
│   ├── usage.md                 # Usage guide
│   ├── DEVELOPMENT.md           # This file
│   ├── CONTRIBUTING.md          # Contributing guide
│   └── ROADMAP.md               # Project roadmap
├── Makefile                     # Build automation
├── pyproject.toml               # Python config
├── .flake8                      # Linting config
└── README.md                    # Project overview
```

## 🚀 Development Workflow

### 1. Setup Environment

```bash
# Clone repository
git clone https://github.com/kandr-kiev/oslw.git
cd oslw

# Install dependencies
make dev

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### 2. Run Services

```bash
# Start API server (hot reload)
make run

# Start frontend dev server
make frontend-dev

# Run tests
make test
make test-fast
```

### 3. Development Commands

```bash
# Linting
make lint

# Formatting
make format

# Type checking
make typecheck

# Clean build artifacts
make clean
```

## 📝 Code Standards

### Python Style
- **PEP 8** compliance
- **Type hints** for all functions
- **Docstrings** for all public methods
- **Max line length**: 88 chars (Black)
- **Imports**: grouped and sorted

### Git Workflow
```bash
# Feature branch
git checkout -b feature/<name>

# Commit messages (conventional)
git commit -m "feat: add new feature
- bullet 1
- bullet 2"

# Push and create PR
git push origin feature/<name>
```

### Commit Types
- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation
- `test:` — tests
- `refactor:` — code refactoring
- `chore:` — maintenance

## 🧪 Testing

### Test Structure
```
tests/
├── conftest.py              # Shared fixtures
├── domain/                  # Domain layer tests
│   ├── test_page.py         # WikiPage tests
│   ├── test_integrity.py    # Integrity tests
│   ├── test_index.py        # Index tests
│   └── test_monitor.py      # Source tests
└── cron/                    # Cron tests
    └── test_scheduler.py    # Scheduler tests
```

### Running Tests
```bash
# All tests with coverage
pytest tests/ -v --cov=src/oslw

# Fast tests (no coverage)
pytest tests/ -v

# Specific test file
pytest tests/domain/test_page.py -v

# Specific test class
pytest tests/domain/test_page.py::TestWikiPage -v
```

### Test Coverage Goals
- **Domain layer**: 90%+
- **Application layer**: 80%+
- **API layer**: 70%+
- **Overall**: 75%+

## 🔧 Architecture Principles

### Clean Architecture
```
┌─────────────────────────────────────────┐
│              API Layer                  │  ← FastAPI, Typer
├─────────────────────────────────────────┤
│           Application Layer             │  ← Services, Use Cases
├─────────────────────────────────────────┤
│              Domain Layer               │  ← Business Logic
├─────────────────────────────────────────┤
│           Infrastructure Layer          │  ← FileManager, GitManager
└─────────────────────────────────────────┘
```

### Dependency Rule
- **Domain** → no dependencies
- **Application** → Domain only
- **API/CLI** → Application + Domain
- **Infrastructure** → Domain (implements interfaces)

### Key Patterns
1. **Service Pattern**: Application layer services orchestrate domain logic
2. **Repository Pattern**: Infrastructure provides data access
3. **Dependency Injection**: Services receive dependencies via `__init__`
4. **Async/Sync**: I/O operations are async, computation is sync

## 📊 Cron Jobs

### Available Jobs
| Job | Description | Interval |
|-----|-------------|----------|
| `doctor` | Wiki integrity checks | Daily |
| `graph` | Knowledge graph rebuild | Daily |
| `digest` | Daily digest generation | Daily |
| `sources` | Source monitoring | Hourly |
| `quality` | Linting & deduplication | Daily |
| `index` | Index rebuild | Hourly |

### Running Jobs
```bash
# List all jobs
oslw cron --list

# Run specific job
oslw cron --run doctor

# Run all jobs
oslw cron --run-all
```

### Adding New Jobs
```python
# 1. Create job class in src/oslw/cron/jobs.py
class MyJob:
    def __init__(self, service: MyService = None):
        self.service = service or MyService()

    def execute(self, **kwargs: Any) -> dict:
        # Your logic here
        return {"status": "success"}

# 2. Register in scheduler
scheduler = CronScheduler()
scheduler.register(
    name="my_job",
    func=MyJob().execute,
    interval=3600,  # 1 hour
)
```

## 🎨 Frontend Development

### Tech Stack
- **Next.js 15**: SPA with App Router
- **React 18**: Component library
- **Tailwind CSS**: Utility-first styling
- **Cytoscape.js**: Graph visualization
- **Vite**: Build tool

### Component Structure
```
frontend/src/
├── components/
│   ├── Dashboard.jsx    # Wiki statistics
│   ├── Pages.jsx        # Page management
│   ├── Search.jsx       # Full-text search
│   ├── Graph.jsx        # Knowledge graph
│   ├── Tools.jsx        # Doctor & Digest tools
│   └── Settings.jsx     # Configuration
├── services/
│   └── api.js           # API client
└── App.jsx              # Main app with routing
```

### Running Frontend
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

## 📚 Documentation

### Docs Structure
```
docs/
├── api.md               # API reference
├── usage.md             # Usage guide
├── DEVELOPMENT.md       # This file
├── CONTRIBUTING.md      # Contributing guide
└── ROADMAP.md           # Project roadmap
```

### Writing Documentation
- Use **Markdown** format
- Include **code examples**
- Add **screenshots** where helpful
- Keep **examples up-to-date**
- Use **consistent formatting**

## 🚨 Troubleshooting

### Common Issues

**Import errors**
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/workspace/projects/oslw/src
```

**Test failures**
```bash
# Run with verbose output
pytest -v --tb=long

# Check specific test
pytest tests/domain/test_page.py::TestWikiPage::test_create_valid_page -v
```

**API server issues**
```bash
# Check logs
tail -f logs/oslw.log

# Verify environment
env | grep WIKI
```

## 📈 Performance

### Optimization Tips
1. **Use async I/O** for database/file operations
2. **Cache frequently accessed data**
3. **Batch operations** where possible
4. **Use generators** for large datasets
5. **Profile with cProfile** before optimizing

### Monitoring
```bash
# Check wiki status
oslw status

# Run doctor
oslw doctor diagnose

# Check sources
oslw sources monitor
```

## 🔐 Security

### Best Practices
1. **Never commit secrets** — use `.env` files
2. **Validate all inputs** — use Pydantic
3. **Sanitize file paths** — prevent path traversal
4. **Use HTTPS** in production
5. **Regular dependency updates**

### Environment Variables
```bash
# Required
WIKI_ROOT=/path/to/wiki

# Optional
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Quick Start for Contributors
1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Ensure all tests pass
5. Update documentation
6. Submit a pull request

## 📝 Changelog

See [CHANGELOG.md](../CHANGELOG.md) for version history.

---

**Last Updated**: 2026-08-05  
**Version**: 0.2.0
