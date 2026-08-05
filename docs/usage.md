# OSLW Usage Guide

> Практичний посібник з використання OSLW — CLI, API, та автоматизація.

## 📋 Зміст

1. [Швидкий старт](#швидкий-старт)
2. [CLI Commands](#cli-commands)
3. [API Usage](#api-usage)
4. [Configuration](#configuration)
5. [Workflows](#workflows)
6. [Troubleshooting](#troubleshooting)

---

## Швидкий старт

### Встановлення

```bash
# Клонувати репозиторій
git clone https://github.com/kandr-kiev/oslw.git
cd oslw

# Встановити залежності
pip install -e .

# Перевірити встановлення
oslw --help
```

### Запуск сервера

```bash
# Запустити FastAPI сервер
python -m uvicorn oslw.api.app:app --reload --port 8000

# API доступний на http://localhost:8000
# Swagger docs: http://localhost:8000/docs
```

### Перевірка стану wiki

```bash
# Базова перевірка
oslw status -r /workspace/llm-wiki

# Детальна перевірка
oslw status -r /workspace/llm-wiki -v
```

---

## CLI Commands

### 📊 `oslw status`

Перевірити стан wiki бази.

```bash
# Базова інформація
oslw status -r /workspace/llm-wiki

# Детальний режим
oslw status -r /workspace/llm-wiki -v
```

**Output:**
```
✅ Wiki root: /workspace/llm-wiki
   Wiki pages: 142
   Raw articles: 23
   Index.md: ✅ exists
   Schema.md: ✅ exists
```

---

### 🏥 `oslw doctor`

Аудит якості wiki з автоматичним виправленням.

```bash
# Тільки діагностика (dry-run)
oslw doctor -r /workspace/llm-wiki --dry-run

# З виправленням
oslw doctor -r /workspace/llm-wiki --apply

# Конкретний шар
oslw doctor -r /workspace/llm-wiki --layer wiki_pages

# Комбінація
oslw doctor -r /workspace/llm-wiki --dry-run --layer index
```

**Output:**
```
🔍 Running WikiDoctor diagnosis...
   Wiki root: /workspace/llm-wiki
   Dry run: True

📊 Diagnosis Results:
   Critical: 0
   Warnings: 5
   Info: 12

📈 Quality Statistics:
   Total pages: 142
   With frontmatter: 142
   With SHA256: 140
   Orphan pages: 3
   Duplicate groups: 2
```

---

### 🔄 `oslw sync`

Синхронізація raw статей у wiki сторінки.

```bash
# Dry-run (тільки перевірка)
oslw sync -r /workspace/llm-wiki --dry-run

# Повна синхронізація
oslw sync -r /workspace/llm-wiki --dry-run=False --force

# Перезаписати існуючі
oslw sync -r /workspace/llm-wiki --force
```

**Output:**
```
🔄 Running sync...
   Wiki root: /workspace/llm-wiki
   Dry run: False
   Raw articles found: 23

✅ Synced: Transformer Architecture
✅ Synced: Attention Mechanism
⏭️  Skip: Encoder-Decoder Architecture (exists)
...

📊 Sync Results:
   Synced: 18
   Skipped: 5
   Errors: 0
```

---

### 📊 `oslw graph`

Управління графом знань.

```bash
# Показати статистику
oslw graph -r /workspace/llm-wiki

# Згенерувати новий граф
oslw graph -r /workspace/llm-wiki --generate

# Згенерувати та експортувати
oslw graph -r /workspace/llm-wiki --generate --export
```

**Output:**
```
📊 Graph status:
   Wiki root: /workspace/llm-wiki
   Nodes: 142
   Edges: 487
   Categories: 6
   Density: 0.0242
```

---

### 📰 `oslw digest`

Генерація щоденних дайджестів.

```bash
# Стандартний (24 години, markdown)
oslw digest -r /workspace/llm-wiki

# Кастомний timeframe
oslw digest -r /workspace/llm-wiki --hours 12

# JSON формат
oslw digest -r /workspace/llm-wiki --format json

# Зберегти у файл
oslw digest -r /workspace/llm-wiki --output /tmp/digest.md
```

**Output:**
```
📰 Generating digest...
   Wiki root: /workspace/llm-wiki
   Hours: 24
   Format: markdown

# Daily Digest — 2026-08-05

## New Articles (3)

### 1. Mixture of Experts
- Category: concept
- Tags: mixture, experts, routing
- Summary: MoE architecture for efficient scaling...

📊 Digest Summary:
   Total entries: 3
   By type: {'concept': 2, 'comparison': 1}
   By source: {'rss': 2, 'github': 1}
```

---

### 📡 `oslw monitor`

Моніторинг джерел контенту.

```bash
# Перевірити всі джерела
oslw monitor -r /workspace/llm-wiki

# Конкретне джерело
oslw monitor -r /workspace/llm-wiki --source rss

# GitHub моніторинг
oslw monitor -r /workspace/llm-wiki --source github
```

**Output:**
```
📡 Checking sources...
   Wiki root: /workspace/llm-wiki

📋 Configured Sources:
   ✅ arxiv-sanity (rss) - 15 articles
   ✅ github-updates (github) - 8 repos
   ✅ hf-new-models (huggingface) - 12 models
   ✅ youtube-ml (youtube) - 5 channels

🔍 Checking sources...
   ✅ arxiv-sanity: 2 new articles
   ⏭️  github-updates: no updates
   ✅ hf-new-models: 1 new model
   ⏭️  youtube-ml: no updates

📊 Monitor Results:
   Sources checked: 4
   Sources updated: 2
```

---

### 📄 `oslw page`

Управління wiki сторінками.

```bash
# Список всіх сторінок
oslw page -r /workspace/llm-wiki --list

# Кількість сторінок
oslw page -r /workspace/llm-wiki --count

# Деталі конкретної сторінки
oslw page -r /workspace/llm-wiki --slug transformer-architecture
```

**Output:**
```
📄 Page: Transformer Architecture
   Slug: transformer-architecture
   Type: concept
   Tags: transformer, attention, architecture
   Created: 2026-08-01T10:00:00Z
   Updated: 2026-08-04T15:30:00Z
   Word count: 4523
   Line count: 187
```

---

## API Usage

### Запуск сервера

```bash
# Dev mode (auto-reload)
python -m uvicorn oslw.api.app:app --reload --port 8000

# Production
python -m uvicorn oslw.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Python клієнт

```python
import httpx

BASE = "http://localhost:8000/api/v1"

# Список сторінок
resp = httpx.get(f"{BASE}/wiki/pages", params={"limit": 10, "type": "concept"})
pages = resp.json()["pages"]

# Пошук
resp = httpx.post(f"{BASE}/search", json={
    "query": "attention mechanism",
    "limit": 5,
    "type": "concept"
})
results = resp.json()["hits"]

# Діагностика
resp = httpx.get(f"{BASE}/doctor/diagnose")
report = resp.json()
print(f"Health score: {report['summary']['health_score']}")

# Створити сторінку
resp = httpx.post(f"{BASE}/wiki/pages", json={
    "title": "New Page",
    "content": "# Hello\n\nContent here...",
    "page_type": "concept",
    "tags": ["test"]
})
new_page = resp.json()
```

### cURL приклади

```bash
# Список сторінок
curl "http://localhost:8000/api/v1/wiki/pages?limit=20&type=concept"

# Пошук
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "transformer", "limit": 5}'

# Діагностика
curl "http://localhost:8000/api/v1/doctor/diagnose"

# Створити сторінку
curl -X POST "http://localhost:8000/api/v1/wiki/pages" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Attention Mechanism",
    "content": "# Attention\n\nSelf-attention details...",
    "page_type": "concept",
    "tags": ["attention", "transformer"]
  }'

# Згенерувати граф
curl -X POST "http://localhost:8000/api/v1/graph/generate"
```

---

## Configuration

### Settings

Налаштування через `pyproject.toml` або змінні середовища:

```python
from oslw.config import settings

# Базові шляхи
print(settings.wiki_root)   # /workspace/llm-wiki
print(settings.wiki_path)   # /workspace/llm-wiki/wiki
print(settings.raw_path)    # /workspace/llm-wiki/raw
print(settings.index_path)  # /workspace/llm-wiki/index.md
print(settings.graph_path)  # /workspace/llm-wiki/graph-from-wiki.json
```

### Змінні середовища

| Variable | Default | Description |
|----------|---------|-------------|
| `OSLW_WIKI_ROOT` | `./wiki` | Шлях до wiki кореня |
| `OSLW_LOG_LEVEL` | `INFO` | Рівень логування |
| `OSLW_LOG_DIR` | `./logs` | Шлях до логів |

### Логування

```python
from oslw.config.logging import get_logger

logger = get_logger("my.module")

logger.info("Processing page: %s", slug)
logger.warning("Broken link: %s", link)
logger.error("Failed to save: %s", error)
```

Логи зберігаються у `logs/` директорії.

---

## Workflows

### Щоденний аудит wiki

```bash
#!/bin/bash
# daily-audit.sh

OSLW_ROOT=/workspace/llm-wiki

# Діагностика
oslw doctor -r $OSLW_ROOT --dry-run > /tmp/diagnosis.json

# Дайджест
oslw digest -r $OSLW_ROOT --hours 24 --output /tmp/digest.md

# Моніторинг
oslw monitor -r $OSLW_ROOT

# Відправка результатів
echo "Audit complete. Check /tmp/diagnosis.json and /tmp/digest.md"
```

### Інтеграція з cron

```bash
# Кожні 6 годин — моніторинг
0 */6 * * * oslw monitor -r /workspace/llm-wiki --source rss >> /workspace/llm-wiki/logs/monitor.log 2>&1

# Щодня о 9:00 — дайджест
0 9 * * * oslw digest -r /workspace/llm-wiki --hours 24 --output /workspace/llm-wiki/digest-$(date +\%Y-\%m-\%d).md

# Щотижня — повний аудит
0 0 * * 0 oslw doctor -r /workspace/llm-wiki --apply
```

### Синхронізація raw → wiki

```bash
#!/bin/bash
# sync-raw.sh

OSLW_ROOT=/workspace/llm-wiki

# Знайти нові raw файли
NEW_FILES=$(find $OSLW_ROOT/raw -name "*.md" -mtime -1 2>/dev/null)

if [ -z "$NEW_FILES" ]; then
    echo "No new raw files to sync"
    exit 0
fi

# Синхронізувати
oslw sync -r $OSLW_ROOT --dry-run=False --force

# Оновити граф
oslw graph -r $OSLW_ROOT --generate
```

---

## Troubleshooting

### Поширені проблеми

#### ❌ Wiki root не існує

```bash
# Перевірити шлях
ls -la /workspace/llm-wiki

# Створити структуру
mkdir -p /workspace/llm-wiki/{wiki,raw,schema}
touch /workspace/llm-wiki/index.md
touch /workspace/llm-wiki/schema.md
```

#### ❌ Помилки імпорту

```bash
# Перевірити встановлення
pip list | grep oslw

# Переінсталювати
pip install -e .

# Перевірити PYTHONPATH
echo $PYTHONPATH
# Повинно містити: /workspace/projects/oslw/src
```

#### ❌ API не запускається

```bash
# Перевірити порт
lsof -i :8000

# Запустити з debug
python -m uvicorn oslw.api.app:app --reload --port 8000 --log-level debug

# Перевірити логи
cat /workspace/llm-wiki/logs/*.log
```

#### ❌ Граф не генерується

```bash
# Перевірити wiki сторінки
oslw page -r /workspace/llm-wiki --count

# Згенерувати з debug
python -c "
from oslw.config import settings
from oslw.application import GraphService
gs = GraphService(wiki_root=settings.wiki_root)
graph = gs.generate_graph()
print(f'Nodes: {len(graph.get(\"nodes\", {}))}')
print(f'Edges: {len(graph.get(\"edges\", []))}')
"
```

### Отримання допомоги

```bash
# Довідка CLI
oslw --help
oslw doctor --help

# API документація
# http://localhost:8000/docs

# Логи
tail -f /workspace/llm-wiki/logs/*.log
```
