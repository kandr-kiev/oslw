---
type: playbook
title: Wiki Doctor — діагностика та лікування вікі
description: Посібник з використання інструменту Wiki Doctor для автоматичної діагностики та виправлення проблем LLM Wiki системи
tags: [llm-wiki, wiki-maintenance, wiki-doctor, diagnostics, automated-fix]
sources: [wiki_app/tools/wiki_doctor.py]
confidence: high
links: [wiki-maintenance, wiki-indexer, wiki-lint]
created: 2026-07-11
updated: 2026-07-29
---

# Wiki Doctor — Діагностика та лікування вікі

**Wiki Doctor** — комплексний інструмент для багаторівневої діагностики та автоматичного лікування LLM Wiki системи.

**Версія:** 2.0.0 (OOP Refactor)
**Дата оновлення:** 2026-07-29

## Архітектура (v2.0)

```
┌─────────────────────────────────────────────────────────────┐
│                    Wiki Doctor CLI                           │
│                                                              │
│  llmwiki doctor              — тільки діагностика           │
│  llmwiki doctor --cure       — діагностика + лікування      │
│  llmwiki doctor --dry-run    — безпечна діагностика         │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    ┌─────────────────┐ ┌─────────────┐ ┌──────────────┐
    │ DoctorReport    │ │ cure_*()    │ │ outputs/     │
    │ (Pydantic)      │ │ methods     │ │ doctor-      │
    │                 │ │             │ │ report.json  │
    └─────────────────┘ └─────────────┘ └──────────────┘
              │
              ▼
    ┌─────────────────────────────────────────────────────┐
    │               6 Diagnostic Layers                    │
    │                                                     │
    │  L1: wiki_pages  — frontmatter, wikilinks, tags     │
    │  L2: raw_sources — frontmatter, SHA256 integrity    │
    │  L3: index       — duplicates, stale links, meta    │
    │  L4: infra       — root files, _N dups, Astro       │
    │  L5: integrator  — critical bug detection           │
    │  L6: config      — SCHEMA.md tag sync               │
    └─────────────────────────────────────────────────────┘
```

### v2.0 OOP Structure

**Клас:** `class WikiDoctorTool(BaseTool)`
**Шлях:** `wiki_app/tools/wiki_doctor.py`

**Залежності:**
- `services/file_service.py` — atomic write/reads
- `services/frontmatter_service.py` — frontmatter parsing
- `services/slug_service.py` — slug validation
- `services/utils.py` — SHA256, APPROVED_TAGS, YAML parsing
- `models/doctor_report.py` — DoctorReport (Pydantic model)

## Шари діагностики

| № | Шар | Що перевіряє | severity | auto-fix |
|---|-----|-------------|----------|----------|
| 1 | `wiki_pages` | frontmatter, required fields, broken wikilinks, unapproved tags, missing from index, page size >200 lines, low confidence, contested pages, missing source files | ERROR/WARN/INFO | ✅ так |
| 2 | `raw_sources` | frontmatter, SHA256 drift | ERROR | ✅ так |
| 3 | `index` | duplicate entries, missing Last updated/Total pages, stale paths (singular→plural) | WARN | ✅ так |
| 4 | `infrastructure` | root-level wiki files, _N duplicates, APPROVED_TAGS drift, truncated Astro files | WARN | ✅ так |
| 5 | `integrator` | dict iteration without .items(), double-escaped regex | ERROR/WARN | ✅ так |
| 6 | `config` | SCHEMA.md existence, tag taxonomy completeness | ERROR/WARN | ✅ так |

## Алгоритм лікування (priority order)

```
Phase 1: diagnose() — full scan across all 6 layers
Phase 2: cure() — priority-based auto-fix
  P1: cure_broken_wikilinks()     → replace with existing slugs or remove
  P2: cure_missing_frontmatter()  → add default frontmatter with type=concept
  P3: cure_sha256_drift()         → recompute & update hashes
  P4: cure_missing_fields()       → add missing frontmatter fields
  P5: cure_missing_sources()      → remove non-existent source paths
  P6: cure_missing_index_entries() → add pages to index.md
  P7: cure_approved_tags_drift()  → sync APPROVED_TAGS with SCHEMA.md + wiki usage
Phase 3: diagnose() — re-scan to verify fixes
Phase 4: generate final status report + JSON output
```

## Вихідні дані

### Консольний вивід

```
============================================================
  WIKI DOCTOR — Повна діагностика та лікування
  2026-07-11 18:16 UTC
============================================================

🔍 Фаза 1: Діагностика всіх шарів...

📊 Результати діагностики:
   ERROR: 0 | WARN: 30 | INFO: 10 | Auto-fixable: 3

💊 Фаза 2: Лікування...

🔍 Фаза 3: Повторна діагностика (після лікування)...

📊 Результати після лікування:
   ERROR: 0 | WARN: 30 | INFO: 10 | Auto-fixable: 3

============================================================
  📋 ФІНАЛЬНИЙ ЗВІТ
============================================================

До лікування: ERROR: 0 | WARN: 30 | INFO: 10 | Auto-fixable: 3
Після лікування: ERROR: 0 | WARN: 30 | INFO: 10 | Auto-fixable: 3

✅ Статус: [CLEAN] — критичних помилок не виявлено
```

### JSON звіт (`outputs/doctor-report.json`)

```json
{
  "timestamp": "2026-07-11 18:16 UTC",
  "before": {"total": 40, "ERROR": 0, "WARN": 30, "INFO": 10, "auto_fixable": 3},
  "after": {"total": 40, "ERROR": 0, "WARN": 30, "INFO": 10, "auto_fixable": 3},
  "cure_stats": {},
  "remaining_issues": [...]
}
```

### Log entry

Додається до `log.md` як новий запис:
```
## [2026-07-11 18:16 UTC] wiki_doctor | Wiki Doctor — до: ERROR: 0 | WARN: 30 | INFO: 10 | Auto-fixable: 3, після: ERROR: 0 | WARN: 30 | INFO: 10 | Auto-fixable: 3, виправлень: 0
```

## Функції лікування

### `cure_broken_wikilinks(report)`
Замінює розбиті wikilinks на існуючі slug-и (найкращий match за word overlap ≥ 2 слів) або видаляє. Конвертує `[[name](url)]` у стандартний markdown `[name](url)`.

### `cure_missing_frontmatter(report)`
Додає default frontmatter (type=concept, tags=[llm-wiki], confidence=medium) до сторінок без frontmatter.

### `cure_sha256_drift(report)`
Перераховує SHA256 хеші для всіх raw-файлів з drift.

### `cure_missing_fields(report)`
Додає відсутні required fields (description, tags, sources, confidence, links, created, updated). Не змінює `type` — це критичне поле.

### `cure_missing_sources(report)`
Видаляє non-existent source paths з frontmatter.

### `cure_missing_index_entries(report)`
Додає сторінки, відсутні в `index.md`, у правильний розділ (за page type). Оновлює Total pages count.

### `cure_approved_tags_drift(report)`
Синхронізує `APPROVED_TAGS` у `wiki_app/services/utils.py` з SCHEMA.md + фактичним використанням тегів у wiki.

## Статус-звіти

| Статус | Значення | Коли |
|--------|----------|------|
| `[CLEAN]` | 0 ERROR після лікування | Система в порядку |
| `[DRIFT]` | Залишилися ERROR | Потрібна ручна увага |
| `[ACTIVE]` | Виявлено та виправлено проблеми | Лікування успішне |
| `[SILENT]` | Немає проблем для лікування | Система стабільна |

## Використання

### Тільки діагностика
```bash
llmwiki doctor
```

### Діагностика + лікування (recommended)
```bash
llmwiki doctor --cure
```

### Безпечна діагностика (без змін файлів)
```bash
llmwiki doctor --dry-run
```

### В Python-коді
```python
from wiki_app.tools.wiki_doctor import WikiDoctorTool

# Create tool instance
doctor = WikiDoctorTool()

# Only diagnosis
report = doctor.diagnose()
print(report.severity_summary())  # "ERROR: 0 | WARN: 30 | INFO: 10 | Auto-fixable: 3"

# Diagnosis + cure
report = doctor.diagnose_and_cure()  # returns final report after re-scan

# Dry-run mode — no file changes, only report
report = doctor.diagnose_and_cure(dry_run=True)
# report.mode == 'dry-run'
# report.fixes == 0 (none applied)
# JSON saved with mode='dry-run' in outputs/doctor-report.json
```

## `--dry-run` режим

**Призначення:** Безпечна діагностика без зміни жодного файлу. Використовується у cron Wiki Doctor (`wiki_doctor.py cure --dry-run`) для щоденного health-check.

**Як працює:**
- `diagnose_and_cure(dry_run=True)` встановлює `__dict__['_DRY_RUN'] = True`
- Усі 7 cure-функцій перевіряють `_DRY_RUN` перед викликом `_write_if_not_dry()`
- `fixes` завжди 0 — нічого не записується на диск
- JSON звіт зберігається з `mode: 'dry-run'`
- Console report показує, що БУЛО б виправлено

**CLI:**
```bash
# Безпечний health-check — жодних змін файлів
llmwiki doctor --dry-run

# Тільки діагностика (без cure взагалі)
llmwiki doctor
```

**Порівняння:**

| Режим | Файли змінюються? | JSON mode | Fixes | Використання |
|-------|-------------------|-----------|-------|--------------|
| `diagnose` | ❌ ні | — | — | Швидкий health-check |
| `cure --dry-run` | ❌ ні | `'dry-run'` | 0 | Cron Wiki Doctor (безпечно) |
| `cure` | ✅ так | `'live'` | N | Тижневий maintenance |

**Тести:** 42/42 PASS (36 live + 6 dry-run).

## Залежності

- `wiki_app/services/utils.py` — `split_frontmatter`, `parse_simple_yaml`, `APPROVED_TAGS`, `compute_sha256`, `check_raw_integrity`, `fix_file_hash`, `append_to_log`, `slugify`
- Жодних зовнішніх бібліотек — тільки Python stdlib

## Типові сценарії використання

1. **Щоденний health-check** — `llmwiki doctor` перед початком роботи
2. **Тижневий maintenance** — `llmwiki doctor --cure` для автоматичного виправлення накопичених проблем
3. **Перед інгестацією** — діагностика перед `llmwiki ingest` для виявлення конфліктів
4. **Після інгестації** — `llmwiki doctor --cure` для виправлення проблем, створених інтегратором

## Різниця з `wiki_lint.py`

| | `wiki_lint.py` | `wiki_doctor.py` |
|---|---|---|
| **Мета** | Лінтинг структури | Діагностика + лікування |
| **Вивід** | Текстовий звіт | Console + JSON + log.md |
| **Auto-fix** | ❌ ні | ✅ 7 функцій лікування |
| **Шари** | wiki_pages + raw_sources | 6 шарів (додає index, infra, integrator, config) |
| **Priority** | Flat | Priority-based (P1-P7) |
| **Re-scan** | ❌ | ✅ після лікування |

## Збереження як skill

Для повторного використання цього інструменту в майбутніх сесіях, збережіть як skill:

```
skill_manage(action='create', name='wiki-doctor', content='''
---
name: wiki-doctor
description: >
  Wiki Doctor — багаторівнева діагностика та автоматичне лікування LLM Wiki.
  6 diagnostic layers, 7 cure functions, structured reports.
version: 1.0.0
author: Archivist
tags: [wiki-doctor, diagnostics, automated-fix, wiki-maintenance]
---

# Wiki Doctor

## When This Skill Activates
Use when: wiki health check needed, before/after integrator run, weekly maintenance,
pre-ingestion validation, or when user asks about wiki system health.

## Quick Start
```bash
llmwiki doctor              # diagnosis only
llmwiki doctor --cure       # diagnosis + auto-fix
```

## Key Functions
- `diagnose()` → DoctorReport with 6-layer analysis
- `diagnose_and_cure()` → full cycle: diagnose → cure → re-diagnose → report
- `DoctorReport.severity_summary()` → "ERROR: N | WARN: N | INFO: N | Auto-fixable: N"

## 6 Diagnostic Layers
1. wiki_pages — frontmatter, wikilinks, tags, index, size, confidence
2. raw_sources — frontmatter, SHA256 integrity
3. index — duplicates, stale links, metadata
4. infrastructure — root files, _N duplicates, APPROVED_TAGS drift, Astro truncation
5. integrator — critical bug detection (dict iteration, regex escaping)
6. config — SCHEMA.md existence, tag taxonomy completeness

## 7 Cure Functions (Priority Order)
P1: cure_broken_wikilinks() — replace orphaned wikilinks with existing slugs
P2: cure_missing_frontmatter() — add default frontmatter
P3: cure_sha256_drift() — recompute & update SHA256 hashes
P4: cure_missing_fields() — add missing required frontmatter fields
P5: cure_missing_sources() — remove non-existent source paths
P6: cure_missing_index_entries() — add pages to index.md
P7: cure_approved_tags_drift() — sync APPROVED_TAGS with SCHEMA.md

## Output
- Console: status report with before/after comparison
- JSON: outputs/doctor-report.json (structured data)
- Log: appended to log.md
''')
```
