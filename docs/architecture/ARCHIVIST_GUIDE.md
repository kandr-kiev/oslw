---
title: Архітектурний протокол та керівництво оператора
type: reference
category: references
tags: [architecture, audit, archivist, guidelines, system-integrity]
created: 2026-07-23
updated: 2026-07-25
confidence: high
---

# 📘 ЛК "Архітектурний протокол та керівництво оператора" (LLM Wiki)

**Для кого:** Профіль "Архіваріус" та оператори системи.
**Мета:** Стандартизація процесів, усунення дублювання, підвищення якості даних та оптимізація графа знань.
**Статус:** Актуальний | **Останній аудит:** 2026-07-31

---

## 1. 🏗️ Архітектура системи (5 шарів, v2.0)

Система LLM Wiki будується за принципом конвеєра даних. Кожен шар має чітку відповідальність.

| ШАРОК | КОМПОНЕНТИ | ВІДПОВІДАЛЬНІСТЬ |
|:---:|:---|:---|
| **1. Ingestion** | `source_monitor.py` (RSS+GitHub+Local+HF), `inbox_router.py` (/towiki) | Збір "сирого" контенту в `raw/articles/`. Дедуплікація (SHA256). |
| **2. Processing** | `IntegratorTool` (wiki_app/tools/integrator.py) | Трансформація `raw/` → `wiki/` (концепти, сутності, порівняння). |
| **3. Graph** | `WikiGraphGenerator`, `GraphifyBridgeTool` | Побудова `graph-from-wiki.json` на основі wikilinks. Синхронізація графа з контентом. |
| **4. Quality** | `WikiDoctorTool`, `WikiLintTool`, `FixWikilinksTool`, `FixSha256Tool`, `CleanupDuplicatesTool` | Діагностика, фікс хешів, перевірка індексу, виправлення посилань. |
| **5. Consumption** | `AGENTS.md` (Graph-First Protocol), `SCHEMA.md`, `services/utils.py::APPROVED_TAGS` | Пошук контексту через BFS, формування відповідей. SCHEMA.md — єдине джерело істини для тегів та конвенцій. |

### v2.0 OOP-пакет

```
wiki_app
├── cli/app.py              # Typer CLI — 13 commands
├── core/                   # DI Container, Config, Logger, Exceptions
├── models/                 # Pydantic: WikiPage, RawArticle, DoctorReport, GraphNode
├── services/               # FileUtils, ConfigService, FrontmatterService, SlugService, ReportFormatter, Utils
└── tools/                  # Integrator, Doctor, Router, Graphify, Lint, Maintenance
```

---

## 2. ⚠️ Критичні проблеми (Audit Findings)

### 🔴 Критичні дублі (видалені в v2.0)

Ці скрипти **видалені** — функціонал повністю покритий `wiki_app/` модулями:

| Файл | Статус | Чому видалено |
|:---|:---|:---|
| `tools/rss_monitor.py` | ✅ видалено | `source_monitor.py` моніторить 27+ RSS фідів |
| `tools/github_monitor.py` | ✅ видалено | `source_monitor.py` моніторить GitHub Issues/PRs |
| `tools/github_release_monitor.py` | ✅ видалено | `source_monitor.py` моніторить GitHub Releases |
| `tools/local_file_monitor.py` | ✅ видалено | `inbox_router.py` класифікує та обробляє локальні файли краще |
| `framework/` (8 файлів) | ✅ видалено | Повний дубль `wiki_app/` — власні BaseTool, ConfigManager, FileUtils, Logger, PathManager, ReportFormatter, models |
| `tools/` (30 файлів) | ✅ видалено | Повний дубль `wiki_app/tools/` — всі інструменти перенесено |

### 🟡 Ризики якості (актуальні)

1. **Orphan Nodes:** ~20% нод у графі не мають зв'язків. Bridge tool фільтрує non-content nodes.
2. **Match Rate:** graphify_bridge match rate ~20.9% — bridge фільтрує non-content nodes (docs, templates).
3. **Page Size:** Деякі сторінки >200 рядків — потребують розбиття на підтеми.

---

## 3. 📊 Ключові метрики (2026-07-31)

|| Показник | Значення ||
|----------|---------||
| **Wiki Pages** | 3,436 ||
| **Raw Articles** | 2,581 ||
| **Python Files (wiki_app/)** | 43 ||
| **Tests** | 472 (472 passing, 100%) ||
| **Graph Nodes** | 4,093 ||
| **Graph Edges** | 7,399 ||
| **Communities** | 26 ||
| **Approved Tags** | 290 ||
| **ERROR Linting** | 0 [CLEAN] ||
| **RSS Feeds** | 27+ ||
| **GitHub Repos** | 15+ ||
| **Cron Jobs** | 6 (всі active) ||

---

## 4. 🔄 Регламент роботи (SOP)

### 4.1. Інгест (Ingestion)

- **RSS/GitHub:** `source_monitor.py` (cron, every 2-6h). Результат — `raw/articles/`.
- **Ручний завантажений файл:** `/workspace/towiki/` → `inbox_router.py` → `raw/` з frontmatter.
- **Правило:** Ніколи не редагуй файли в `raw/` після інгесту. `raw/` — це Ground Truth.

### 4.2. Обробка (Processing)

1. Перевір `raw/` на наявність нових файлів (`check_new_raw.py`).
2. Запусти `llmwiki ingest --dry-run` (перевірка).
3. Запусти `llmwiki ingest` (генерація wiki).
4. Запусти `llmwiki doctor --cure` (діагностика + лікування).

### 4.3. Запит (Querying)

**Завжди слідуй протоколу AGENTS.md:**
1. Завантаж `graph-from-wiki.json`.
2. Знайди seed-ноду (тема запиту).
3. BFS(depth=2) → знайди community.
4. Завантаж топ-5 wiki-сторінок.
5. Синтезуй відповідь.
6. *Fallback:* Якщо граф 0 results → `wiki/index.md`.

---

## 5. 🚀 Найкращі практики

1. **Wiki Links:** Кожна сторінка wiki повинна мати мінімум 2 outbound wikilinks.
2. **Tags:** Використовуй тільки затверджені теги з `SCHEMA.md`.
3. **Frontmatter:** Кожна сторінка wiki має YAML frontmatter.
4. **Index:** Кожна нова сторінка додається в `wiki/index.md`.
5. **Log:** Кожна дія фіксується в `log.md`.
6. **Graph:** Граф — це скелет. Wiki — це м'ясо. Без графа пошук сліпий.

---

**Документ підтримується в актуальному стані. Останній аудит: 2026-07-25.**
