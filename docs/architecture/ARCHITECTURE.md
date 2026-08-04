# Local LLM Wiki — Повна архітектурна документація v2.0

> **Останнє оновлення:** 2026-07-29
> **Версія системи:** 2.0.0 (OOP Refactor)
> **Статус:** Production

---

## Зміст

1. [Термінологічна база](#1-термінологічна-база)
2. [Загальна архітектура](#2-загальна-архітектура)
3. [OOP-пакет wiki_app/](#3-oop-пакет-llmwiki)
4. [Сервіси](#4-сервіси)
5. [DI Container](#47-di-container-corecontainerpy)
6. [Інструменти (Tools)](#5-інструменти-tools)
7. [CLI (Typer)](#6-cli-typer)
8. [Моделі (Pydantic)](#7-моделі-pydantic)
9. [Залежності](#8-залежності)
10. [Потоки даних](#9-потоки-даних)
11. [Поточна статистика системи](#10-поточна-статистика-системи)

---

## 1. Термінологічна база

| Термін | Визначення | Приклад використання |
|--------|-----------|---------------------|
| **Сканування** (Scan) | Процес виявлення нових джерел у вхідних директоріях (`raw/`) | RSS-сканування, моніторинг файлів |
| **Інтеграція** (Integration) | Автоматичне перетворення сирого джерела на сторінку вікі з класифікацією та тегуванням | `llmwiki ingest` |
| **Лінтинг** (Linting) | Перевірка структурної цілісності вікі: frontmatter, брукен-лінки, SHA256-дрейф | `llmwiki maintenance wiki-lint` |
| **Сире джерело** (Raw source) | Необроблений контент, збережений як доказ — неизмінний після інгестації | `raw/articles/filename.md` |
| **Синтез** (Synthesis) | Сторінка вікі, створена на основі аналізу сирого джерела | `wiki/concepts/*.md` |
| **Frontmatter** | YAML-блок на початку файлу з метаданими (тип, теги, дати, джерела) | `---\ntype: concept\n---` |
| **Вікілінк** (Wikilink) | Посилання на іншу сторінку вікі у форматі `[[slug]]` | `[[llm-wiki]]` |
| **SHA256-дрейф** | Розбіжність між обчисленим хешем тіла файлу та збереженим хешем | `sha256: abc123...` ≠ обчислений |
| **Tag map** | Мапінг тегів → назви сторінок, використовується для пошуку зв'язків | `{"llm-wiki": ["llm-wiki.md", "rag.md"]}` |
| **Central utilities** | Модуль `services/utils.py` — єдине джерело правди для хешування, frontmatter, тегів | `wiki_app/services/utils.py` |
| **Index** | Каталог-навігація, що містить усі сторінки вікі з категоризацією | `wiki/index.md` |
| **Log** | Журнал дій append-only, фіксує всі операції | `log.md` |

---

## 2. Загальна архітектура

### 2.1 Тришарова модель даних

```
┌─────────────────────────────────────────────────────────────────────┐
│                 ШАР 1: СИРІ ДЖЕРЕЛА (Immutable)                     │
│  raw/articles/  raw/papers/  raw/transcripts/  raw/assets/          │
│  → Ніколи не редагуються після збереження                            │
└─────────────────────────────────────────────────────────────────────┘
                              ↓ сканування
┌─────────────────────────────────────────────────────────────────────┐
│               ШАР 1.5: ПРОМІЖНИЙ КЕШ (.processed/)                   │
│  HTML→MD конверсія, НЕ в git                                        │
│  → Проміжна ланка між raw/ і wiki/                                   │
└─────────────────────────────────────────────────────────────────────┘
                              ↓ інтеграція
┌─────────────────────────────────────────────────────────────────────┐
│                    ШАР 2: СИНТЕЗ (Mutable)                           │
│  wiki/concepts/  wiki/entities/  wiki/comparisons/                   │
│  wiki/playbooks/  wiki/synthesis/  wiki/queries/                     │
│  wiki/references/  wiki/templates/                                   │
│  → Редагуються агентами на основі сирого шару                        │
└─────────────────────────────────────────────────────────────────────┘
                              ↓ лінтинг
┌─────────────────────────────────────────────────────────────────────┐
│                    ШАР 3: ОПЕРАЦІЇ (Tooling)                         │
│  SCHEMA.md  ARCHITECTURE.md  ALGORITHM.md  AGENTS.md                 │
│  wiki_app/  index.md  log.md                                          │
│  → Керують процесом, визначають правила                              │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Потоки даних

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  External    │    │  RSS/File/   │    │  Integrator  │    │  Wiki Pages  │
│  Sources     │───▶│  GitHub      │───▶│  (auto)      │───▶│  (wiki/)     │
│  (URL, PDF,  │    │  Monitor     │    │              │    │              │
│   paste)     │    │  (cron)      │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                                        │
                                                        ├─ index.md (оновлення)
                                                        ├─ log.md (запис)
                                                        └─ processed.db (трекинг)
```

---

## 3. OOP-пакет wiki_app/

### 3.1 Структура пакету

```
wiki_app
├── __init__.py
├── cli/
│   ├── __init__.py
│   └── app.py              # Typer CLI — entry point
├── core/
│   ├── __init__.py
│   ├── container.py        # DI Container (DependencyInjector)
│   ├── config.py           # Configuration (Pydantic BaseSettings)
│   ├── logger.py           # Structured logging (loguru)
│   └── exceptions.py       # Custom exception hierarchy
├── models/
│   ├── __init__.py
│   ├── wiki_page.py        # WikiPage — Pydantic model
│   ├── raw_article.py      # RawArticle — Pydantic model
│   ├── doctor_report.py    # DoctorReport — structured diagnostic
│   └── graph_node.py       # GraphNode — graphify integration
├── services/
│   ├── __init__.py
│   ├── file_service.py     # FileUtils + PathManager (atomic ops)
│   ├── config_service.py   # ConfigService + CATEGORY_ICONS
│   ├── frontmatter_service.py  # Frontmatter parsing/generation
│   ├── slug_service.py     # Slug generation & validation
│   ├── report_formatter.py # Report generation (console + JSON)
│   └── utils.py            # Central utilities (SHA256, tags, YAML)
└── tools/
    ├── __init__.py
    ├── integrator.py       # IntegratorTool
    ├── wiki_doctor.py      # WikiDoctorTool (6 layers, 7 cures)
    ├── inbox_router.py     # InboxRouterTool (Telegram)
    ├── graphify_bridge.py  # GraphifyBridgeTool
    ├── graphify_query.py   # GraphifyQueryTool (BFS/DFS)
    ├── fix_wikilinks.py    # FixWikilinksTool
    ├── fix_sha256.py       # FixSha256Tool
    ├── wiki_lint.py        # WikiLintTool
    ├── cleanup_duplicates.py # CleanupDuplicatesTool
    ├── git_sync.py         # GitSyncTool
    ├── wiki_graph_generator.py # WikiGraphGenerator
    ├── github_repos.py     # REPOS (single source of truth)
    ├── newspaper_digest.py # NewspaperDigest
    └── source_monitor.py   # RSS + GitHub + Local + HuggingFace
```

### 3.2 Архітектурні принципи

| Принцип | Опис | Приклад |
|---------|------|---------|
| **OOP** | Усі інструменти — класи з інкапсульованою логікою | `class WikiDoctorTool` |
| **DI** | Залежності через Dependency Injection Container | `Container().inject()` |
| **Pydantic** | Моделі з валідацією типів | `WikiPage(title: str, type: str)` |
| **Single Source of Truth** | `services/utils.py` — єдине джерело для хешів, тегів, frontmatter | `APPROVED_TAGS` в одному місці |
| **Atomic Operations** | FileService — atomic write (temp file + rename) | `write_atomic()` |
| **Structured Logging** | loguru замість print() | `logger.info("Message {var}")` |
| **Configuration** | Pydantic BaseSettings замість hardcoded | `config: Config = Config()` |

---

## 4. Сервіси

### 4.1 `services/file_service.py` — FileUtils + PathManager

**Роль:** Робота з файлами з atomic operations (temp file + rename), валідація шляхів.

**Ключові методи:**

| Метод | Призначення | Повертає |
|-------|-------------|----------|
| `write_atomic(path, content)` | Атомарний запис (temp + rename) | bool |
| `read_file(path)` | Читання файлу | str |
| `ensure_dir(path)` | Створення директорії | None |
| `file_exists(path)` | Перевірка існування | bool |
| `delete_file(path)` | Видалення файлу | bool |
| `list_files(dir_path, pattern)` | List files by glob | list[str] |

### 4.2 `services/config_service.py` — ConfigService + CATEGORY_ICONS

**Роль:** Керування конфігурацією, іконками категорій, шляхами.

**Ключові методи:**

| Метод | Призначення | Повертає |
|-------|-------------|----------|
| `get_config()` | Отримати конфігурацію | Config |
| `get_category_icon(category)` | Іконка для категорії | str |
| `get_category_icon_all()` | Всі іконки категорій | dict |
| `validate_path(path)` | Валідація шляху | bool |

### 4.3 `services/frontmatter_service.py` — Frontmatter Parser

**Роль:** Парсинг та генерація YAML frontmatter.

**Ключові методи:**

| Метод | Призначення | Повертає |
|-------|-------------|----------|
| `split_frontmatter(content)` | Парсинг frontmatter | `{fm, body, raw}` |
| `parse_simple_yaml(fm_text)` | Парсинг YAML | dict |
| `build_frontmatter(data)` | Генерація frontmatter | YAML string |
| `extract_frontmatter(content)` | Extract + parse | dict |
| `validate_required_fields(data)` | Валідація полів | list[str] errors |
| `update_frontmatter(content, new_data)` | Оновлення frontmatter | str |

### 4.4 `services/slug_service.py` — Slug Generation

**Роль:** Уніфікована генерація slug, валідація, унікальність.

**Ключові методи:**

| Метод | Призначення | Повертає |
|-------|-------------|----------|
| `slugify(text)` | Генерація slug | str |
| `generate_unique_slug(base, existing)` | Унікальний slug | str |
| `validate_slug(slug)` | Валідація slug | bool |
| `extract_slugs(content)` | Extract [[slugs]] from content | list[str] |

### 4.5 `services/report_formatter.py` — Report Generation

**Роль:** Генерація звітів у console + JSON форматі.

**Ключові методи:**

|| Метод | Призначення | Повертає |
||-------|-------------|----------|
|| `format_report(title, stats, sections, errors, warnings)` | Console report | str |
|| `format_stats_table(stats)` | Stats as Markdown table | str |
|| `format_article_entry(title, summary, url, category, icon)` | Article entry for digest | str |
|| `format_doctor_report(report)` | Doctor report formatting | str |

### 4.5.1 `services/config_service.py` — ConfigService

**Роль:** Керування конфігурацією, тегами, категоріями.

**Ключові методи:**

|| Метод | Призначення | Повертає |
||-------|-------------|----------|
|| `load_approved_tags()` | Завантажити теги з JSON | set[str] |
|| `save_approved_tags(tags)` | Зберегти теги | None |
|| `get_config()` | Отримати Config | Config |
|| `get_category_icon(category)` | Іконка для категорії | str |
|| `validate_path(path)` | Валідація шляху | bool |

### 4.6 `services/utils.py` — Central Utilities

**Роль:** Модуль сумісності — делегує всі операції до сервісів `services/`.

**Ключові функції (backward compat):**

|| Функція | Призначення | Повертає |
||---------|-------------|----------|
|| `split_frontmatter(content)` | Делегує `FrontmatterOps.split_frontmatter()` | `(fm, body)` |
|| `compute_sha256(content)` | Делегує `FileUtils.sha256_body()` — `.lstrip('\n')` | hex digest |
|| `parse_simple_yaml(fm_text)` | Власна реалізація (fallback) | dict |
|| `verify_file_hash(filepath)` | Перевірка хешу одного файлу | `{status, stored, computed}` |
|| `check_raw_integrity(raw_dir)` | Сканування raw/ → звіт | `{total, ok, mismatch, no_hash, no_fm}` |
|| `fix_file_hash(filepath)` | Оновлення хешу у frontmatter | bool |
|| `slugify(text)` | Делегує `SlugService.generate()` | string |
|| `APPROVED_TAGS` | Делегує `ConfigService.load_approved_tags()` | set |
| `retry_for_status(url, ...)` | Делегує `FileUtils.retry_for_status()` | response |
| `print_status(has_new, label, count, source_count)` | Канонічний формат статусу | — |

**Ключові особливості:**
- `compute_sha256()` виконує `.lstrip('\n')` — узгоджено з `FileUtils.sha256_body`
- `APPROVED_TAGS` — делегує `ConfigService`, завантажує з `approved_tags.json`
- Усі функції — backward compat, реальна логіка у сервісах
- `parse_simple_yaml()` — власна реалізація (fallback, не використовує PyYAML)
- `retry_for_status()` — делегує `FileUtils.retry_for_status` (P1-1)

---

## 4.7 DI Container (`core/container.py`)

**Роль:** Dependency Injection Container — епіцентр залежностей. Використовує `dependency-injector` для уникнення циклічних імпортів.

**Реєстрація сервісів (Singleton):**

| Сервіс | Provider | Призначення |
|--------|----------|-------------|
| `Config` | `providers.Singleton(Config.from_env)` | Централізована конфігурація |
| `Logger` | `providers.Singleton(Logger.get)` | Структуроване логування |
| `FileUtils` | `providers.Singleton(FileUtils)` | Atomic file operations |
| `PathManager` | `providers.Singleton(PathManager)` | Path operations |
| `FrontmatterOps` | `providers.Singleton(FrontmatterOps)` | YAML frontmatter parsing/generation |
| `SlugService` | `providers.Singleton(SlugService)` | Slug generation |
| `ConfigService` | `providers.Singleton(ConfigService)` | Tag/config management |

**Інструменти (Lazy Loading via `providers.Callable`):**

| Інструмент | Фабрика | Призначення |
|------------|---------|-------------|
| `WikiDoctor` | `Callable(lambda dry_run=False: ...)` | 6-layer diagnostic & auto-cure |
| `IntegratorTool` | `Callable(lambda dry_run=False, limit=0: ...)` | Raw → Wiki integration |
| `InboxRouterTool` | `Callable(lambda: ...)` | Telegram message routing |

**Використання:**

```python
from wiki_app.core.container import DIContainer

container = DIContainer()
config = container.get_config()
file_utils = container.get_file_utils()
doctor = container.get_wiki_doctor(dry_run=False)
```

---

## 5. Інструменти (Tools)

### 5.1 `wiki_app/tools/integrator.py` — IntegratorTool

**Роль:** Перетворення raw-джерел на wiki-сторінки з класифікацією та тегуванням.

**Клас:** `class IntegratorTool`

**Конструктор:**
```python
IntegratorTool(
    config=Config,
    file_utils=FileUtils,
    path_manager=PathManager,
    frontmatter_ops=FrontmatterOps,
    config_service=ConfigService,
    dry_run=False,
    limit=0,
    approved_tags=set(),
)
```

**Основні методи:**
- `run()` → `Dict[str, int]` — Повний pipeline: scan → process → index → stats
- `_scan_raw()` → `List[Path]` — Сканування raw/articles/
- `_process_file(raw_file)` → `bool` — Обробка одного файлу
- `_generate_wiki_page(title, slug, category, content, url, tags)` → `str` — Генерація wiki-сторінки
- `_update_index(full_rebuild=False)` — Incremental update index.md (P0-5)
- `_detect_page_type(content, tags)` → `str` — Визначення типу сторінки
- `_extract_tags(content, approved_tags)` → `List[str]` — Вилучення тегів

**HTML→Markdown конвертер `_html_to_markdown()`:**
- Конвертація heading, paragraph, bold, italic, links, images
- Lists (ordered + unordered), tables, code blocks, blockquotes (P1-8)

### 5.2 `wiki_app/tools/wiki_doctor.py` — WikiDoctorTool

**Роль:** 6-layer diagnostic & auto-cure.

**Клас:** `class WikiDoctorTool`

**Конструктор:**
```python
WikiDoctorTool(config=Config, dry_run=False)
```

**6 шарів діагностики:**

| № | Шар | Що перевіряє | severity | auto-fix |
|---|-----|-------------|----------|----------|
| 1 | `wiki_pages` | frontmatter, required fields, broken wikilinks, unapproved tags | ERROR/WARN | ✅ |
| 2 | `raw_sources` | frontmatter, SHA256 integrity | ERROR | ✅ |
| 3 | `index` | duplicate entries, stale links, meta | WARN | ✅ |
| 4 | `infrastructure` | root files, _N dups, APPROVED_TAGS drift | WARN | ✅ |
| 5 | `integrator` | critical bug detection | ERROR/WARN | ✅ |
| 6 | `config` | SCHEMA.md tag sync | ERROR/WARN | ✅ |

**7 cure-функцій (priority order):**

```
P1: cure_broken_wikilinks()     → replace with existing slugs or remove
P2: cure_missing_frontmatter()  → add default frontmatter with type=concept
P3: cure_sha256_drift()         → recompute & update hashes
P4: cure_missing_fields()       → add missing frontmatter fields
P5: cure_missing_sources()      → remove non-existent source paths
P6: cure_missing_index_entries() → add pages to index.md
P7: cure_approved_tags_drift()  → sync APPROVED_TAGS with SCHEMA.md
```

**Методи:**
- `diagnose()` → `DoctorReport` — Повна діагностика
- `cure()` → `Dict[str, int]` — Діагностика + auto-fix
- `report(report)` → `str` — Форматування звіту

**CLI:**
```bash
llmwiki doctor              # Full diagnosis
llmwiki doctor --cure       # Diagnosis + auto-fix
llmwiki doctor --dry-run    # Diagnosis only (no file changes)
```

### 5.3 `wiki_app/tools/inbox_router.py` — InboxRouterTool

**Роль:** Маршрутизація повідомлень з Telegram та інших джерел.

**Клас:** `class InboxRouterTool`

**Конструктор:**
```python
InboxRouterTool(
    inbox_dir=Path("/workspace/towiki"),
    raw_dir=Path("/workspace/llm-wiki/raw"),
    processed_db=Path("/workspace/llm-wiki/.processed/inbox_files.txt"),
    file_utils=FileUtils,
)
```

**Основні методи:**
- `scan_and_route(dry_run=False)` → `List[Dict]` — Сканирует inbox, маршрутизує файли до raw/
- `process_inbox_message(message)` → `Dict` — Обробка повідомлення з Telegram
- `_process_text_file(filepath, target_dir)` → `dict` — Text file + frontmatter + SHA256
- `_process_binary_file(filepath, target_dir)` → `dict` — Binary file copy
- `_classify_file(filepath)` → `Optional[str]` — Класифікація за extension
- `_mark_processed(filepath, mtime)` — Фіксація обробленого файлу (fcntl.flock)
- `_is_processed(filepath, mtime)` → `bool` — Dedup через processed DB

**Правила маршрутизації:**
| Extension | Target |
|-----------|--------|
| `.md`, `.txt`, `.rst`, `.html` | `raw/articles/` |
| `.pdf` | `raw/papers/` |
| `.png`, `.jpg`, `.svg`, `.mp4` | `raw/assets/` |
| `.json`, `.yaml`, `.toml` | `raw/configs/` |
| `.mp3`, `.wav`, `.m4a` | `raw/transcripts/` |

**P1-9:** Memory limit 5MB на файл
**P1-10:** `fcntl.flock` для `_mark_processed`
**Empty dir cleanup:** Після обробки файлу — видалення порожніх піддиректорій inbox

### 5.4 `wiki_app/tools/graphify_bridge.py` — GraphifyBridgeTool

**Роль:** Міст між `graph-from-wiki.json` та фактичними wiki-файлами. Верифікація edge coverage, додавання wikilinks, backlinks, Dataview queries.

**Клас:** `class GraphifyBridgeTool`

**Конструктор:**
```python
GraphifyBridgeTool(
    file_utils=FileUtils,
    path_manager=PathManager,
    graph_path=Path("graphify-out/graph-from-wiki.json"),
    dry_run=False,
    auto_fix=False,
)
```

**Основні методи:**
- `run()` → `Dict[str, Any]` — Повний pipeline: load_graph → load_slugs → verify_edges → add_links → add_backlinks → add_dataview → find_orphans → report
- `_load_graph()` → `Optional[GraphData]` — Завантаження graph-from-wiki.json → GraphNode + GraphEdge
- `_load_slugs()` → `dict` — Збір усіх slug з wiki/index.md та wiki/**/*.md
- `_verify_edges(graph, slugs)` — Перевірка edge coverage (matched vs missing_links)
- `_add_missing_links(graph, slugs)` — Додавання [[wikilinks]] для missing edges
- `_add_backlinks(graph, slugs)` — Додавання секції Backlinks
- `_add_dataview(graph, slugs)` — Додавання Dataview query
- `_find_orphans(graph)` — Визначення orphan nodes (без edges)

**Звіт (report):**
| Поле | Призначення |
|------|-------------|
| `matched` | Edges, що знайшли відповідні сторінки |
| `orphans` | Nodes без edges |
| `missing_links` | Missing [[wikilinks]] |
| `dataview_added` | Dataview queries додано |
| `backlinks_added` | Backlinks секцій додано |

**Fuzzy match:** `FUZZY_THRESHOLD = 0.65` для нечіткого відповідності graph node ↔ wiki slug

### 5.5 `wiki_app/tools/graphify_query.py` — GraphifyQueryTool

**Роль:** BFS/DFS пошук по графу знань.

**Клас:** `class GraphifyQueryTool`

**Конструктор:**
```python
GraphifyQueryTool(graph_path=Path("graphify-out/graph-from-wiki.json"))
```

**Основні методи:**
- `bfs(seed, depth=2)` — Breadth-first search
- `dfs(seed, depth=2)` — Depth-first search
- `shortest_path(start, end)` — Shortest path between nodes
- `community_filter(tag)` — Filter by community
- `god_nodes()` — Most linked nodes
- `query(query_text)` — Semantic query via BFS

### 5.6 `wiki_app/tools/fix_wikilinks.py` — FixWikilinksTool

**Роль:** Виправлення брукен-лінків з title-based на slug-based.

**Клас:** `class FixWikilinksTool`

**Конструктор:**
```python
FixWikilinksTool(wiki_dir=Path("wiki"))
```

**Основні методи:**
- `scan()` — Сканирувати всі wiki-сторінки на [[title]] замість [[slug]]
- `fix()` — Виправити брукен-лінки (title → slug mapping)
- `dry_run()` — Безпечне сканування без змін

### 5.7 `wiki_app/tools/fix_sha256.py` — FixSha256Tool

**Роль:** Оновлення SHA256 хешів у frontmatter.

**Клас:** `class FixSha256Tool`

**Конструктор:**
```python
FixSha256Tool(wiki_dir=Path("wiki"))
```

**Основні методи:**
- `scan()` — Знайти файли з SHA256 drift (stored ≠ computed)
- `fix()` — Оновити хеші (FileUtils.sha256_body)
- `verify()` — Верифікація всіх хешів

### 5.8 `wiki_app/tools/wiki_lint.py` — WikiLintTool

**Роль:** Перевірка структурної цілісності wiki.

**Клас:** `class WikiLintTool`

**Конструктор:**
```python
WikiLintTool(wiki_dir=Path("wiki"), config=Config, approved_tags=tags)
```

**Основні методи:**
- `scan_all()` — Сканирувати всі wiki-сторінки
- `validate_frontmatter(content)` — Валідація frontmatter
- `validate_required_fields(frontmatter)` — Required fields check (title, slug, category, created)
- `validate_tags(tags)` — Tag validation against APPROVED_TAGS
- `extract_wikilinks(content)` — Extract [[wikilinks]]
- `check_sha256_drift(stored_sha, computed_sha)` — SHA256 drift check
- `check_line_count(content)` — Line count check (>200)
- `check_confidence(content)` — Confidence check (low/contested)

### 5.9 `wiki_app/tools/cleanup_duplicates.py` — CleanupDuplicatesTool

**Роль:** Знаходження та видалення дублікатів wiki-сторінок з суфіксами `_1`, `_2`, `_3`, `_4`.

**Клас:** `class CleanupDuplicatesTool`

**Конструктор:**
```python
CleanupDuplicatesTool(wiki_dir=Path("wiki"))
```

**Основні методи:**
- `scan()` — Знайти дублікати (файли з `_1`, `_2`, `_3`, `_4` суфіксами)
- `cleanup()` — Видалити дублікати
- `dry_run()` — Безпечне сканування без змін

### 5.11 `wiki_app/tools/wiki_graph_generator.py` — WikiGraphGenerator

**Роль:** Генерація `graph-from-wiki.json` з wiki wikilinks. Без LLM — використовує існуючі [[wikilinks]] як edges.

**Клас:** `class WikiGraphGenerator`

**Конструктор:**
```python
WikiGraphGenerator(root="/workspace/llm-wiki", output_dir="/workspace/graphify-out")
```

**Основні методи:**
- `run(output_path=None)` → `dict` — Повний pipeline: scan → build → report → save
- `scan_wiki_files()` → `list` — Сканування wiki/**/*.md (excludes index.md)
- `build_graph(pages)` → `dict` — Побудова graph: nodes + edges + communities
- `extract_wikilinks(content)` → `list` — Extract [[wikilink]] references
- `extract_frontmatter(content)` → `dict` — Парсинг frontmatter
- `sanitize_id(raw)` → `str` — Sanitize slug → valid graph node ID
- `generate_report(graph)` → `dict` — Summary: type_dist, top_tags, top_inbound, communities

**Output:** `graph-from-wiki.json` + `wiki_graph_report.json`

### 5.12 `wiki_app/tools/git_sync.py` — GitSyncTool

**Роль:** Синхронізація з GitHub.

**Клас:** `class GitSyncTool`

**Конструктор:**
```python
GitSyncTool(repo_path=Path("/workspace/llm-wiki"), remote_url=remote)
```

**Основні методи:**
- `sync()` — Sync: pull → status → add → commit → push
- `cmd_add()` — Git add wiki/ + raw/
- `cmd_clean()` — Git clean untracked
- `cmd_status()` → `str` — Git status

### 5.13 `wiki_app/tools/newspaper_digest.py` — NewspaperDigest

**Роль:** Генерація щоденного newspaper digest з raw статей за останні N годин.

**Клас:** `class NewspaperDigest`

**Конструктор:**
```python
NewspaperDigest(hours=24, dry_run=False)
```

**Основні методи:**
- `run()` — Повний pipeline: scan recent → filter → sort by created → format → save
- `scan_recent()` → `list` — Сканування raw/articles/ за last N hours
- `format_entry(title, summary, url, created)` → `str` — Форматування однієї статті
- `generate_digest()` → `str` — Генерація markdown digest

### 5.14 `wiki_app/tools/source_monitor.py` — SourceMonitor

**Роль:** Моніторинг джерел: RSS, GitHub, Local, HuggingFace.

**Клас:** `class SourceMonitor`

**Основні методи:**
- `monitor()` — Повний моніторинг усіх джерел
- `check_rss_feeds()` — Перевірка RSS каналів
- `check_github_repos()` — Перевірка GitHub репозиторіїв
- `check_local_paths()` — Моніторинг локальних шляхів
- `check_huggingface()` — Перевірка HuggingFace моделей

---

## 6. CLI (Typer)

### 6.1 Структура команд

```
llmwiki
├── ingest                    # Ingest URL/file/paste
│   ├── --dry-run            # Preview without changes
│   └── --limit N            # Limit number of files
├── doctor                    # Wiki Doctor (diagnose + cure)
│   ├── --cure               # Auto-fix all issues
│   └── --dry-run            # Diagnose only
├── router <message>          # Route Telegram message
├── tags                      # Tag management
│   ├── --list               # List all tags
│   ├── --add TAG            # Add new tag
│   └── --remove TAG         # Remove tag
├── graphify
│   ├── bridge                # Bridge graph.json ↔ wiki/
│   │   ├── --dry-run        # Preview only
│   │   └── --auto-fix       # Auto-fix bridge links
│   └── query <query>         # Graph query
│       ├── --depth N         # BFS depth (default 2)
│       └── --json            # JSON output
├── maintenance
│   ├── fix-wikilinks         # Fix broken wikilinks
│   │   ├── --dry-run        # Preview only
│   │   └── --limit N        # Limit number of fixes
│   ├── fix-sha256            # Fix SHA256 drift
│   │   └── --dry-run        # Preview only
│   ├── wiki-lint             # Run wiki lint
│   ├── cleanup-duplicates    # Remove duplicate pages
│   │   └── --apply          # Actually delete duplicates
│   ├── git-sync              # Git sync operations
│   │   └── --command         # add|clean|status
│   └── wiki-graph            # Regenerate graph.json
│       └── --dry-run        # Preview only
└── monitor
    ├── newspaper-digest      # Generate news digest
    │   └── --hours N         # Hours to look back (default 24)
    └── source-monitor        # Run all monitors
```

### 6.2 Використання

```bash
# Встановлення
pip install -e ".[dev]"

# Виклик CLI
llmwiki --help
llmwiki ingest --dry-run
llmwiki doctor --cure
llmwiki maintenance wiki-lint
llmwiki graphify query "machine learning" --depth 2 --json
```

---

## 7. Моделі (Pydantic)

### 7.1 `models/wiki_page.py` — WikiPage

```python
class WikiPage(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, pattern=r'^[a-z0-9]+(-[a-z0-9]+)*$')
    category: str = Field(..., pattern=r'^[a-z][a-z0-9]*$')
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    tags: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    summary: Optional[str] = Field(None, max_length=5000)
    created: datetime = Field(default_factory=datetime.now)
    updated: datetime = Field(default_factory=datetime.now)
```

### 7.2 `models/raw_article.py` — RawArticle

```python
class RawArticle(BaseModel):
    title: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    content: str = Field(default="")
    source: str = Field(default="")
    published_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    language: str = Field(default="en")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    
    @property
    def slug(self) -> str:
        # slug[:80]
```

### 7.3 `models/doctor_report.py` — DoctorReport

```python
class CheckResult(BaseModel):
    check_name: str
    status: str = Field(pattern=r'^(PASS|FAIL|WARN|SKIP)$')
    message: str = ""
    details: Optional[Dict] = None
    severity: str = Field(default="info", pattern=r'^(low|medium|high|critical)$')
    layer: str = ""

class DoctorReport(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    wiki_root: Optional[str] = None
    checks: List[CheckResult] = Field(default_factory=list)
    summary: Dict[str, int] = Field(default_factory=lambda: {
        "total": 0, "pass": 0, "fail": 0, "warn": 0, "skip": 0
    })
    
    @property
    def passed(self) -> int
    @property
    def failed(self) -> int
    @property
    def warnings(self) -> int
    @property
    def total_checks(self) -> int
    @property
    def is_healthy(self) -> bool
    def get_all_issues(self) -> List[CheckResult]
```

### 7.4 `models/graph_node.py` — GraphNode

```python
class GraphNode(BaseModel):
    id: str = Field(..., pattern=r'^[a-z0-9]+(-[a-z0-9]+)*$')
    label: str = Field(..., min_length=1)
    category: str = Field(default="concept")
    weight: float = Field(default=1.0, ge=0.0)
    summary: str = Field(default="", max_length=3000)
    content: str = Field(default="", max_length=500)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def has_content(self) -> bool

class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str = Field(default="related")
    weight: float = Field(default=1.0, ge=0.0)

class GraphData(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    version: str = Field(default="1.0")
    generated_at: datetime = Field(default_factory=datetime.now)
```

---

## 8. Залежності

| Бібліотека | Версія | Призначення |
|------------|--------|-------------|
| **typer** | >=0.27.0 | CLI framework |
| **rich** | >=15.0.0 | Console formatting |
| **pydantic** | >=2.13.0 | Data validation (models) |
| **dependency-injector** | >=4.49.0 | DI Container |
| **requests** | >=2.32.0 | HTTP (RSS, GitHub API) |
| **PyYAML** | >=6.0 | YAML frontmatter |
| **python-frontmatter** | >=1.1.0 | Frontmatter parsing |

Dev dependencies: pytest, pytest-cov, ruff.

**Python version:** >=3.11

---

## 9. Потоки даних

### 9.1 Ingest Pipeline

```
External Source → raw/ (immutable) → IntegratorTool → wiki/ (mutable)
     ↓                 ↓                  ↓              ↓
  URL/Paste        SHA256 verify    Classify +     Index + Log
  (RSS/GitHub)     Atomic write     Generate       Updated
```

### 9.2 Maintenance Pipeline

```
WikiDoctorTool → 6 layers → 7 cures → Re-scan → Report
     ↓              ↓          ↓         ↓         ↓
  Diagnose     Find issues  Fix P1-P7  Verify  Console + JSON
```

### 9.3 Graph Pipeline

```
wiki/ (wikilinks [[slug]]) → WikiGraphGenerator → graph.json
                                                              ↓
graphify-out/graph.json → GraphifyBridgeTool → cross-references
```

---

## 10. Поточна статистика системи (оновлено 2026-07-29)

||| Показник | Значення ||
|----------|---------||
| **Сторінки wiki** | **3441** ||
| **Сирі джерела** | **2581** ||
| **Python-файлів (wiki_app/)** | **57** ||
| **Тестових файлів** | **13** ||
| **Nodes графа** | **3437** ||
| **Edges графа** | **6498** ||
| **Communities** | **41** ||
| **Тегів (taxonomy)** | **262** ||
| **ERROR лінтингу** | **? [ПЕРЕВІРИТИ]** ||
| **Obsidian плагінів** | **3** (dataview, git, templater) ||

### Граф знань

|| Метрика | Значення ||
|---------|---------||
| Avg edges/node | 1.89 ||
| Top tag | `llm-wiki` (136) ||
| Top type | `comparison` (1129) ||
| Most linked | "Automating Ai Away" (91 inbound) ||

### CLI Commands (фактичний стан)

|| Command | Підкоманди | Призначення ||
|---------|-----------|-------------||
| `llmwiki ingest` | `--dry-run`, `--limit N` | Ingest URL/file/paste ||
| `llmwiki doctor` | `--cure`, `--dry-run` | Wiki Doctor (diagnose + cure) ||
| `llmwiki router` | `<message>` | Route Telegram message ||
| `llmwiki tags` | `--list`, `--add`, `--remove` | Tag management ||
| `llmwiki graphify` | `bridge`, `query` | Graph bridge + BFS/DFS query ||
| `llmwiki maintenance` | `fix-wikilinks`, `fix-sha256`, `wiki-lint`, `cleanup-duplicates`, `git-sync`, `wiki-graph` | Maintenance toolkit ||
| `llmwiki monitor` | `newspaper-digest`, `source-monitor` | Monitoring ||
| `llmwiki version` | — | Версія системи ||

**Разом: 8 top-level commands + 15 subcommands (включаючи version).**

---

**Версія:** 2.0.0 | **Дата:** 2026-07-29 | **Статус:** Production
