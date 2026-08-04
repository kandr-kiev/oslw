# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-05

### Added

#### Foundation (Phase 1)
- **Project structure**: Clean Architecture layout with domain, application, infrastructure, api, cli
- **Configuration**: Pydantic Settings with env-based config (`config/settings.py`)
- **Logging**: Structured logging setup (`config/logging.py`)
- **Core exceptions**: Domain-specific exception hierarchy
- **Domain events**: Dataclasses for internal module communication

#### Wiki Domain
- **WikiPage model**: Full page representation with validation (`domain/wiki/page.py`)
- **WikiIndex**: index.md management with O(1) lookup (`domain/wiki/index.py`)
- **PageIntegrity**: SHA256 verification and wikilink validation (`domain/wiki/integrity.py`)

#### Sources Domain
- **SourceConfig**: Source monitor configuration with types (`domain/sources/monitor.py`)
- **ContentIngestor**: Raw → wiki ingestion pipeline (`domain/sources/ingest.py`)

#### Graph Domain
- **GraphGenerator**: Knowledge graph from wiki wikilinks (`domain/graph/generator.py`)
- **GraphQuery**: Conceptual search with BFS traversal (`domain/graph/query.py`)

#### Quality Domain
- **WikiDoctor**: Multi-layer diagnosis (index, wiki_pages, metadata) (`domain/quality/doctor.py`)
- **PageLint**: Structural validation (`domain/quality/lint.py`)
- **Deduplication**: SHA256-based duplicate detection (`domain/quality/cleanup.py`)

#### Digest Domain
- **NewspaperDigest**: Daily digest generation (`domain/digest/newspaper.py`)

#### Infrastructure
- **GitManager**: Git operations for wiki repo (`infrastructure/git.py`)
- **DatabaseManager**: SQLAlchemy SQLite with schema (`infrastructure/database.py`)

#### Application Layer
- Service layer placeholders for use-case orchestration

#### API Layer
- **FastAPI app**: Entry point with lifespan (`main.py`)
- **v1 endpoints**: health, wiki, sources, graph, doctor, digest, search
- **Pydantic schemas**: API request/response models
- **Dependency injection**: Shared dependencies via `api/deps.py`

#### CLI
- **Typer CLI**: status, doctor, sync, graph, digest, monitor commands (`cli/commands.py`)

#### Testing
- **conftest.py**: Fixtures for temp wiki root, sample pages
- Test directory structure: tests/domain, tests/application, tests/api

#### Documentation
- **README.md**: Project overview, structure, usage
- **CHANGELOG.md**: Version history
- **Makefile**: Dev commands (install, test, lint, format, run)
- **.env.example**: Configuration template
- **.gitignore**: Standard Python/Node.js ignores

### Tech Stack
- Backend: FastAPI + Uvicorn
- Database: SQLite + SQLAlchemy
- Frontend: Next.js 15 (App Router)
- CLI: Typer
- Configuration: Pydantic Settings
- Testing: pytest

### Architecture
- Clean Architecture: domain (framework-agnostic) → application → infrastructure → api
- Single wiki database instance
- Files remain source of truth; SQLite = cache/index/search
