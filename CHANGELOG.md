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
- **FileManager**: File-based storage layer — NO SQL, markdown files on disk (`infrastructure/database.py`)

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

## [0.2.0] - 2026-08-05

### Added

#### Phase 3: Application Layer
- **PageService**: CRUD operations for wiki pages (page_service.py)
- **IndexService**: index.md management and updates (index_service.py)
- **IntegrityService**: Integrity checks and validation (integrity_service.py)
- **GraphService**: Knowledge graph generation and queries (graph_service.py)
- **QualityService**: Quality monitoring, linting, deduplication (quality_service.py)
- **DigestService**: Newspaper digest generation (digest_service.py)
- **SourceService**: Content source management and ingestion (source_service.py)

#### Phase 4: API Layer
- **7 endpoints** with full implementation:
  - `/api/v1/wiki/pages` — CRUD for wiki pages
  - `/api/v1/search` — Full-text search
  - `/api/v1/graph` — Knowledge graph operations
  - `/api/v1/doctor/diagnose` — Wiki audit
  - `/api/v1/digest` — Digest generation
  - `/api/v1/sources` — Source monitoring
- **API schemas**: Pydantic models for all requests/responses
- **API router**: Clean v1 router aggregation

#### Phase 5: CLI Layer
- **7 Typer commands**: status, doctor, sync, graph, digest, monitor, page
- **Full integration**: CLI commands use application services
- **Error handling**: User-friendly error messages

#### Phase 6: Testing
- **47 tests passing** across domain layer
- **Bug fixes**: fix_sha256 (returns False when no sha256), fix_wikilinks (converts all [[Page Title]] → [[page-title]])
- Test coverage: index, integrity, monitor, page modules

#### Phase 7: Documentation
- **docs/api.md**: Full REST API documentation (8 endpoints, request/response examples)
- **docs/usage.md**: Usage guide with CLI examples, API usage, automation patterns

#### Phase 8: Integration
- **Backend**: FastAPI entry point with CORS, v1 router, health endpoint
- **Frontend** (React + Vite + Tailwind + Cytoscape):
  - `services/api.js`: Full OSLW API client (12 endpoints)
  - `components/Dashboard.jsx`: Stats, health, recent pages, quick actions
  - `components/Pages.jsx`: CRUD for wiki pages with filters
  - `components/Search.jsx`: Full-text search with type filter
  - `components/Graph.jsx`: Interactive Cytoscape knowledge graph
  - `components/Tools.jsx`: Tool management (Doctor, Graph, Digest, Sources)
  - `components/Settings.jsx`: System configuration display
  - `App.jsx`: Unified tab navigation, lazy loading

#### Phase 9: Cleanup
- Removed dead directories: `.processed/`, `migrations/`, `scripts/`
- Removed stale frontend: `frontend/src/app/`, `hooks/`, `store/`
- Removed empty test dirs: `tests/api/`, `tests/application/`
- Removed brace artifacts: `src/oslw/api/{v1/`, `infrastructure/{repositories/`
- Removed 12 empty .log files and all __pycache__ directories

### Changed

#### Architecture — Complete Separation from wiki_app
- **NO dependency on wiki_app**: OSLW is fully isolated, self-contained
- **File-based storage ONLY**: No SQL, no SQLite, no database cache
- **All data lives in markdown files**: wiki/, raw/, index.md are the source of truth
- **Configuration-driven paths**: No hardcoded paths — all from Settings

#### Infrastructure
- **REMOVED DatabaseManager (SQLAlchemy)**: Replaced with FileManager
- **FileManager**: Direct file operations on wiki/, raw/ directories
  - Read/write wiki pages by slug or path
  - Parse frontmatter (slug, title, type, tags, sources, sha256, created, updated)
  - List wiki pages with optional category filter
  - List raw articles
  - Update/rebuild index.md from all pages
  - Delete pages with index cleanup
  - Page count statistics
- **GitManager**: Path from Settings (not hardcoded)

#### Configuration
- **REMOVED database_url, database_echo**: No database configuration
- **wiki_root**: Configurable path to wiki files (default: `./wiki`)
- **Properties**: raw_path, wiki_path, index_path, schema_path, inbox_path, graph_file, graphify_dir

#### Domain Layer
- All domain modules use Settings for paths (not hardcoded)
- No imports from wiki_app
- No SQL/database dependencies

### Technical Stack
- Backend: FastAPI + Uvicorn
- Storage: Markdown files on disk (NO database)
- Frontend: Next.js 15 (App Router)
- CLI: Typer
- Configuration: Pydantic Settings
- Testing: pytest

### Architecture
- Clean Architecture: domain (framework-agnostic) → application → infrastructure → api
- **File-based storage**: All data in markdown files
- **No database**: No SQL, no cache, no separate data store
- **Fully isolated**: Zero dependency on wiki_app
