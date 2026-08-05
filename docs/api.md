# OSLW API Documentation

> REST API для управління wiki-базою знань. FastAPI, OpenAPI/Swagger.

## 📋 Зміст

1. [Базовий URL](#базовий-url)
2. [Аутентифікація](#аутентифікація)
3. [Endpoints](#endpoints)
4. [Схеми даних](#схеми-даних)
5. [Приклади використання](#приклади-використання)

---

## Базовий URL

```
http://localhost:8000/api/v1
```

Після запуску сервера:
```bash
cd /workspace/projects/oslw
python -m uvicorn oslw.api.app:app --reload --port 8000
```

Документація Swagger: `http://localhost:8000/docs`

---

## Аутентифікація

Наразі API не вимагає аутентифікації (local mode). Для production додати API keys або JWT.

---

## Endpoints

### 📄 Wiki Pages

#### GET `/wiki/pages` — Список сторінок

**Параметри:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 50 | Кількість сторінок |
| `offset` | int | 0 | Зсув для пагінації |
| `type` | str | null | Фільтр по типу (concept, comparison, playbook) |
| `tag` | str | null | Фільтр по тегу |

**Приклад:**
```bash
curl http://localhost:8000/api/v1/wiki/pages?limit=10&tag=transformer
```

**Response:**
```json
{
  "pages": [
    {
      "slug": "transformer-architecture",
      "title": "Transformer Architecture",
      "type": "concept",
      "tags": ["transformer", "attention", "architecture"],
      "word_count": 4523,
      "line_count": 187,
      "created": "2026-08-01T10:00:00Z",
      "updated": "2026-08-04T15:30:00Z"
    }
  ],
  "total": 142,
  "limit": 10,
  "offset": 0
}
```

---

#### GET `/wiki/pages/{slug}` — Отримати сторінку

**Параметри:**
| Param | Type | Description |
|-------|------|-------------|
| `slug` | path | Slug сторінки |
| `raw` | bool | Повернути сирі дані (frontmatter + content) |

**Приклад:**
```bash
curl http://localhost:8000/api/v1/wiki/pages/transformer-architecture?raw=true
```

**Response:**
```json
{
  "slug": "transformer-architecture",
  "title": "Transformer Architecture",
  "type": "concept",
  "tags": ["transformer", "attention", "architecture"],
  "content": "# Transformer Architecture\n\nThe transformer architecture...",
  "metadata": {
    "word_count": 4523,
    "line_count": 187,
    "sha256": "abc123...",
    "wikilinks": ["attention-mechanism", "encoder-decoder"],
    "created": "2026-08-01T10:00:00Z",
    "updated": "2026-08-04T15:30:00Z"
  }
}
```

---

#### POST `/wiki/pages` — Створити сторінку

**Body:**
```json
{
  "title": "New Page",
  "content": "# Content here\n\nSome text...",
  "page_type": "concept",
  "tags": ["new", "example"],
  "slug": "new-page"
}
```

**Response:**
```json
{
  "slug": "new-page",
  "title": "New Page",
  "message": "Page created successfully"
}
```

---

#### PUT `/wiki/pages/{slug}` — Оновити сторінку

**Body:**
```json
{
  "title": "Updated Title",
  "content": "# Updated content",
  "tags": ["updated"]
}
```

---

#### DELETE `/wiki/pages/{slug}` — Видалити сторінку

**Response:**
```json
{
  "slug": "old-page",
  "message": "Page deleted successfully"
}
```

---

### 🔍 Search

#### POST `/search` — Пошук по wiki

**Body:**
```json
{
  "query": "attention mechanism",
  "limit": 10,
  "type": "concept"
}
```

**Response:**
```json
{
  "query": "attention mechanism",
  "total": 5,
  "hits": [
    {
      "slug": "attention-mechanism",
      "title": "Attention Mechanism",
      "description": "Core component of transformers...",
      "score": 0.92,
      "type": "concept",
      "tags": ["attention", "transformer"]
    }
  ]
}
```

---

### 📊 Graph

#### GET `/graph` — Отримати граф знань

**Response:**
```json
{
  "nodes": [
    {"id": "transformer-architecture", "label": "Transformer Architecture", "type": "concept"},
    {"id": "attention-mechanism", "label": "Attention Mechanism", "type": "concept"}
  ],
  "edges": [
    {"source": "transformer-architecture", "target": "attention-mechanism", "label": "uses"},
    {"source": "attention-mechanism", "target": "encoder-decoder", "label": "part-of"}
  ],
  "total": 142
}
```

---

#### POST `/graph/generate` — Згенерувати граф

Перегенерує граф з усіх wiki сторінок.

**Response:**
```json
{
  "nodes": [...],
  "edges": [...],
  "total": 142
}
```

---

### 🏥 Doctor

#### GET `/doctor/diagnose` — Аудит wiki

**Параметри:**
| Param | Type | Description |
|-------|------|-------------|
| `layers` | str | Шари для перевірки (comma-separated) |

**Response:**
```json
{
  "total_pages": 142,
  "total_errors": 3,
  "total_warnings": 12,
  "steps": [
    {"step": "critical_issues", "status": "error", "message": "Found 3 critical issues", "count": 3},
    {"step": "frontmatter_coverage", "status": "ok", "message": "142/142 pages have frontmatter", "count": 142}
  ],
  "summary": {
    "health_score": 0.95,
    "orphan_pages": 5,
    "duplicates": 2
  }
}
```

---

#### POST `/doctor/cure` — Виправити проблеми

**Body:**
```json
{
  "dry_run": false,
  "apply_fixes": true
}
```

**Response:**
```json
{
  "success": true,
  "results": {
    "duplicates": {
      "removed": 2,
      "dry_run": false
    },
    "diagnosis_after": {
      "total_errors": 1,
      "total_warnings": 8,
      "total_pages": 142
    }
  }
}
```

---

### 📰 Digest

#### GET `/digest` — Отримати дайджест

**Параметри:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `hours` | int | 24 | Годин для перегляду |
| `format` | str | markdown | Формат (markdown, json, text) |

**Response:**
```markdown
# Daily Digest — 2026-08-05

## New Articles (3)

### 1. Mixture of Experts
- Category: concept
- Tags: mixture, experts, routing
- Summary: MoE architecture for efficient scaling...

### 2. Layer Normalization vs Batch Norm
- Category: comparison
- Tags: normalization, training
- Summary: Comparison of normalization techniques...

### 3. RLHF Training Pipeline
- Category: playbook
- Tags: rlhf, alignment, training
- Summary: Step-by-step RLHF guide...
```

---

### 📡 Sources

#### GET `/sources` — Список джерел

**Response:**
```json
{
  "sources": [
    {
      "name": "arxiv-sanity",
      "type": "rss",
      "last_checked": "2026-08-05T10:00:00Z",
      "status": "ok",
      "articles_count": 15
    }
  ],
  "total": 4
}
```

---

#### POST `/sources/check` — Перевірити джерела

**Body:**
```json
{
  "source_name": "arxiv-sanity"
}
```

**Response:**
```json
{
  "success": true,
  "results": {
    "arxiv-sanity": {
      "updated": 2,
      "errors": 0
    }
  }
}
```

---

## Схеми даних

### WikiPage

```json
{
  "slug": "string (required, unique)",
  "title": "string (required)",
  "type": "enum: concept|comparison|playbook|synthesis|entity|transcript",
  "tags": ["string"],
  "content": "string",
  "metadata": {
    "word_count": 1234,
    "line_count": 56,
    "sha256": "hex string",
    "wikilinks": ["slug1", "slug2"],
    "created": "ISO timestamp",
    "updated": "ISO timestamp"
  }
}
```

### SearchHit

```json
{
  "slug": "string",
  "title": "string",
  "description": "string",
  "score": 0.95,
  "type": "string",
  "tags": ["string"]
}
```

### DoctorReport

```json
{
  "total_pages": 142,
  "total_errors": 3,
  "total_warnings": 12,
  "steps": [
    {
      "step": "string",
      "status": "ok|warning|error",
      "message": "string",
      "count": 0
    }
  ],
  "summary": {
    "health_score": 0.95,
    "orphan_pages": 5,
    "duplicates": 2
  }
}
```

---

## Приклади використання

### Python (httpx)

```python
import httpx

BASE = "http://localhost:8000/api/v1"

# List pages
resp = httpx.get(f"{BASE}/wiki/pages", params={"limit": 10})
pages = resp.json()["pages"]

# Search
resp = httpx.post(f"{BASE}/search", json={
    "query": "transformer",
    "limit": 5
})
results = resp.json()["hits"]

# Diagnose
resp = httpx.get(f"{BASE}/doctor/diagnose")
report = resp.json()
print(f"Health: {report['summary']['health_score']}")

# Generate graph
resp = httpx.post(f"{BASE}/graph/generate")
graph = resp.json()
print(f"Nodes: {graph['total']}")
```

### cURL

```bash
# Get all pages
curl http://localhost:8000/api/v1/wiki/pages?limit=20

# Create a new page
curl -X POST http://localhost:8000/api/v1/wiki/pages \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Page",
    "content": "# Hello World\n\nThis is my first wiki page.",
    "page_type": "concept",
    "tags": ["test", "example"]
  }'

# Run diagnostics
curl http://localhost:8000/api/v1/doctor/diagnose
```

---

## Error Handling

API використовує стандартні HTTP статус-коди:

| Code | Description |
|------|-------------|
| 200 | OK |
| 201 | Created |
| 400 | Bad Request |
| 404 | Not Found |
| 409 | Conflict (page exists) |
| 500 | Internal Server Error |

**Error Response:**
```json
{
  "detail": "Page not found: non-existent-slug"
}
```
