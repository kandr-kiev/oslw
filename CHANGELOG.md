# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

#### oslw-cli slug normalization & deduplication (task t_13b3807a)
- **Canonical slug normalization** (`src/oslw/utils/slug.py`): new single
  `norm_name()` is now the one source of truth for every slug producer —
  `RSSScanner`, `GitHubScanner`, `HuggingFaceScanner`, `YouTubeScanner`,
  `ContentIngestor`, `WikiPage.generate_slug`, `PageService.create_page`, and
  the CLI `sync` command. Normalization is the audit etalon
  (`re.sub(r'[^\\w\\u0400-\\u04ff]+', '-', s)`): lowercase, all non-word /
  non-Cyrillic runs (including `# : @ ? [ ] ( ) ,`) collapse to a single
  hyphen, hyphens collapse and trim. Cyrillic is preserved to match the
  existing wiki. This fixes `role:`, `role--`, `issue-#123:`, etc. producing
  divergent file names.
- **Cross-category deduplication** (`FileManager.write_page`): a normalized
  slug is now unique across ALL Layer-2 categories (`entities`, `concepts`,
  `comparisons`, `queries`, `references`, `playbooks`, `synthesis`,
  `transcripts`). A re-sync of the same concept into a different category
  updates the existing page in place instead of creating a twin; identical
  content is a no-op. A `sha256` field is now written into page frontmatter
  and used for change detection.
- **SHA256-only dedup** (`ContentIngestor.ingest`): identical raw content is
  skipped (not rewritten), keyed on the content body hash rather than slug.
  Also fixed a malformed double `---` separator in the written raw file.
- **CLI `sync`**: slug is now derived with `norm_name` and the existing-page
  set is built from normalized slugs, so a raw article whose title normalizes
  to an existing page's slug is correctly skipped regardless of punctuation.

### Tests
- Added `tests/test_dedup.py` (13 cases): slug normalization, cross-category
  collision, identical-content skip, and sync slug edge cases.
- Updated `tests/test_scanners.py` GitHub slug assertion to the corrected
  `release-v1-0-0` output.

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

## [0.3.0] - 2026-08-05

### Added

#### Phase 12: Architectural Refactoring & Documentation
- **Cron architecture unified**: Internal `CronScheduler` removed — OSLW cron tasks are now pure functions in `src/oslw/cron/jobs.py`
- **System cron integration**: 5 OSLW cron jobs managed by Hermes scheduler (not internal async loop):
  - `OSLW Source Monitor` (every 360m) → `python -m oslw.cli monitor`
  - `OSLW Wiki Integrator` (every 720m) → `python -m oslw.cli sync`
  - `OSLW Wiki Doctor` (every 720m) → `python -m oslw.cli doctor`
  - `OSLW Daily Digest` (0 9 * * *) → `python -m oslw.cli digest`
  - `OSLW Graph & Quality Monitor` (0 10 * * *) → `python -m oslw.cli graph`
- **CLI entry point**: `__main__.py` created for `python -m oslw.cli` execution
- **CLI command syntax**: `python -m oslw.cli <command>` (e.g., `sync`, `doctor`, `graph`)
- **wiki_root configuration**: Default `/workspace/llm-wiki` via `settings.py`, overridable via `OSLW_WIKI_ROOT` env var — no hardcoded paths in cron prompts

### Changed

#### Application Layer — Async → Sync
- **All async methods converted to sync** in 7 application services:
  - `page_service.py`, `index_service.py`, `integrity_service.py`
  - `graph_service.py`, `quality_service.py`, `digest_service.py`, `source_service.py`
- **No `async/await` remains** in the entire codebase — file-based storage doesn't require async I/O
- **0 async methods** across all application layer files

#### Cron Jobs
- **`DoctorService` → `QualityService`**: Renamed and updated
- **SourceMonitor**: Added to `domain/sources/monitor.py` with `list_sources()`, `add_source()`, `remove_source()`, `monitor_all()`
- **Cron jobs refactored to pure functions**: `doctor_job()`, `graph_job()`, `digest_job()`, `sources_job()`, `quality_job()`, `index_job()`
- **`scheduler.py` removed**: Internal async scheduler deleted — system cron handles scheduling

#### CLI Commands
- **`cron` subcommand removed**: No longer needed (system cron handles scheduling)
- **`page` command implemented**: `--list`, `--count`, `--slug <slug>` options
- **Typer OptionInfo handling**: Fixed direct Python calls (when not invoked via CLI)
- **Missing `Path` import fixed**: Added to `domain/sources/monitor.py`

#### Documentation
- **`docs/DEVELOPMENT.md`**: Created (408 lines) — full development guide
- **`docs/CONTRIBUTING.md`**: Created (232 lines) — contributor guidelines
- **`docs/ROADMAP.md`**: Created — project roadmap

### Testing
- **61/61 tests passing** (up from 47)
- **New cron tests**: 14 tests for cron job functions in `tests/cron/test_jobs.py`
- **Removed**: `tests/cron/test_scheduler.py` (scheduler deleted)

### Technical
- **All scripts use `wiki_app` services**: No standalone scripts bypassing config
- **Logging migrated**: All 5 cron scripts use `logger.*` via `wiki_app.backend.core.logger.get_logger`
- **LOG_DIR**: `/workspace/llm-wiki/logs/`

### Architecture
- **Clean separation**: OSLW fully isolated, file-based, no database
- **System cron over internal scheduler**: More reliable, better logging, no daemon process
- **Configuration-driven**: `wiki_root` from settings/env, not hardcoded in cron prompts
- **Sync-first**: No async/await anywhere — simpler, more maintainable for file-based operations
