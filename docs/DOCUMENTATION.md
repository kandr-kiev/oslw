# LLM Wiki — Documentation v2.0

> Повна документація архітектури, технологій, API та використання.

---

## 📋 Зміст

1. [Архітектура](#архітектура)
2. [Технологічний стек](#технологічний-стек)
3. [Backend API](#backend-api)
4. [Frontend UI](#frontend-ui)
5. [Структура проєкту](#структура-проєкту)
6. [Використання](#використання)
7. [QA Metrics](#qa-metrics)

---

## 🏗 Архітектура

```
┌─────────────────────────────────────────────────────────────┐
│                      LLM Wiki v2.0                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Frontend   │    │   Backend    │    │    Wiki DB   │  │
│  │  React+Vite  │◄──►│   FastAPI    │    │  Markdown    │  │
│  │  :3000       │    │   :8000      │    │  /wiki/      │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                   │          │
│         │                   │                   │          │
│    ┌────▼────┐         ┌───▼────┐         ┌────▼────┐     │
│    │Cytoscape│         │Pydantic│         │  Cron   │     │
│    │  .js    │         │ Models │         │  Jobs   │     │
│    └─────────┘         └────────┘         └─────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Шари системи

| Шар | Призначення | Технології |
|-----|-------------|------------|
| **UI** | Візуалізація, управління | React 19, Vite 8, Tailwind CSS 4 |
| **API** | REST endpoints | FastAPI, Uvicorn, CORS |
| **Business Logic** | Інструменти, сервіси | Python 3.11, OOP, Pydantic |
| **Data** | Зберігання, графи | Markdown, JSON, YAML |
| **Automation** | Моніторинг, інгест | Cron jobs, RSS, GitHub API |

---

## 🛠 Технологічний стек

### Backend

| Компонент | Версія | Призначення |
|-----------|--------|-------------|
| **Python** | 3.11+ | Мова програмування |
| **FastAPI** | latest | Web framework, REST API |
| **Uvicorn** | latest | ASGI server |
| **Pydantic** | 2.13+ | Data validation, models |
| **Typer** | 0.27+ | CLI framework |
| **Dependency Injector** | 4.49+ | DI Container |
| **Loguru** | latest | Structured logging |
| **Pytest** | 8+ | Testing framework |
| **Mypy** | latest | Static type checking |

### Frontend

| Компонент | Версія | Призначення |
|-----------|--------|-------------|
| **React** | 19 | UI framework |
| **Vite** | 8 | Build tool, dev server |
| **Tailwind CSS** | 4 | Utility-first CSS |
| **Cytoscape.js** | 3.34 | Graph visualization |
| **Recharts** | 3 | Charts & graphs |
| **Axios** | 1.19 | HTTP client |
| **Oxlint** | 1.75 | Linting |

---

## 🔌 Backend API

### Endpoints

| Endpoint | Method | Опис |
|----------|--------|------|
| `/api/health` | GET | System health check |
| `/api/dashboard` | GET | Dashboard statistics |
| `/api/tools` | GET | List available tools |
| `/api/tools/{name}/run` | POST | Execute a tool |
| `/api/search` | GET | Search wiki pages |
| `/api/graph` | GET | Graph data (nodes, edges) |

### Приклад запиту

```bash
# Health check
curl http://localhost:8000/api/health

# Dashboard stats
curl http://localhost:8000/api/dashboard

# Search
curl "http://localhost:8000/api/search?q=transformer"

# Run tool
curl -X POST http://localhost:8000/api/tools/doctor/run \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}'

# Graph data
curl http://localhost:8000/api/graph
```

### Frontend Proxy

Vite proxy налаштовано у `vite.config.js`:
```js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

---

## 🎨 Frontend UI

### Компоненти

| Компонент | Призначення |
|-----------|-------------|
| `Dashboard` | Головна панель з метриками |
| `GraphView` | Візуалізація графа знань (Cytoscape.js) |
| `SearchPanel` | Пошук wiki сторінок |
| `ToolsPanel` | Управління інструментами |
| `HealthMonitor` | Моніторинг стану системи |

### Стилізація

- Tailwind CSS 4 utility-first
- Dark theme (LLM Wiki branding)
- Responsive design

---

## 📁 Структура проєкту

```
llm-wiki/
├── wiki_app/
│   ├── backend/
│   │   ├── api/              # FastAPI routers
│   │   │   ├── app.py        # FastAPI application
│   │   │   ├── router_dashboard.py
│   │   │   ├── router_tools.py
│   │   │   ├── router_search.py
│   │   │   ├── router_graph.py
│   │   │   └── router_health.py
│   │   ├── cli/              # Typer CLI
│   │   │   └── app.py
│   │   ├── core/             # Core infrastructure
│   │   │   ├── config.py     # Config (Pydantic BaseSettings)
│   │   │   ├── container.py  # DI Container
│   │   │   ├── constants.py
│   │   │   ├── exceptions.py
│   │   │   └── logger.py
│   │   ├── models/           # Pydantic models
│   │   │   ├── wiki_page.py
│   │   │   ├── raw_article.py
│   │   │   ├── doctor_report.py
│   │   │   └── graph_node.py
│   │   ├── services/         # Business logic services
│   │   │   ├── file_service.py
│   │   │   ├── frontmatter_service.py
│   │   │   ├── config_service.py
│   │   │   ├── slug_service.py
│   │   │   └── report_formatter.py
│   │   ├── tests/            # Test suite
│   │   │   ├── api/          # API tests
│   │   │   └── unit/         # Unit tests
│   │   ├── tools/            # OOP tools (17 files)
│   │   │   ├── wiki_doctor.py
│   │   │   ├── integrator.py
│   │   │   ├── graphify_bridge.py
│   │   │   ├── graphify/     # Graphify tools
│   │   │   └── ...
│   │   └── utils.py          # Utility functions
│   ├── frontend/             # React SPA
│   │   ├── src/
│   │   │   ├── components/   # React components
│   │   │   ├── services/     # API client
│   │   │   └── styles/       # Tailwind CSS
│   │   ├── vite.config.js
│   │   └── tailwind.config.js
│   └── docs/                 # Documentation
│       ├── architecture/
│       ├── agent-roles/
│       └── workflows/
├── wiki/                     # Wiki knowledge base
│   ├── concepts/
│   ├── entities/
│   ├── playbooks/
│   └── ...
├── raw/                      # Raw sources
│   └── articles/
├── CHANGELOG.md              # Version history
├── DOCUMENTATION.md          # This file
├── pyproject.toml            # Python project config
├── mypy.ini                  # Type checking config
└── .flake8                   # Linting config
```

---

## 🚀 Використання

### Запуск Backend

```bash
cd /workspace/llm-wiki
PYTHONPATH=/workspace/llm-wiki python -m uvicorn wiki_app.backend.api.app:app \
  --host 0.0.0.0 --port 8000 --reload
```

### Запуск Frontend

```bash
cd /workspace/llm-wiki/wiki_app/frontend
npm install
npm run dev
# Opens at http://localhost:3000
```

### Запуск тестів

```bash
cd /workspace/llm-wiki
PYTHONPATH=/workspace/llm-wiki python -m pytest wiki_app/backend/tests/ -v
```

### CLI

```bash
cd /workspace/llm-wiki
PYTHONPATH=/workspace/llm-wiki python -m wiki_app.backend.cli.app --help
```

### Лінтинг

```bash
# Type checking
PYTHONPATH=/workspace/llm-wiki python -m mypy wiki_app/backend/ --config-file mypy.ini

# Linting (ruff)
ruff check wiki_app/backend/
```

---

## 📊 QA Metrics

### Тестування

| Метрика | Значення |
|---------|----------|
| Total tests | 485 |
| Passed | 485 |
| Failed | 0 |
| Warnings | 9 (minor) |

### Static Analysis

| Метрика | Значення |
|---------|----------|
| Mypy errors | 0 |
| Source files | 54 |
| Python files | 54 |
| Frontend files | 5 |

### Coverage

| Компонент | Статус |
|-----------|--------|
| Backend API | ✅ 13 API tests |
| Backend Tools | ✅ 236 unit tests |
| Frontend | ⏳ TODO |
| Integration | ✅ 18 integration tests |

---

## 📈 Метрики Wiki

| Метрика | Значення |
|---------|----------|
| Wiki pages | 3441 |
| Raw sources | 2581 |
| Graph nodes | 3437 |
| Graph edges | 6498 |
| Communities | 41 |
| Approved tags | 262 |

---

## 🔮 Roadmap

| Фаза | Статус | Опис |
|------|--------|------|
| **P1** | ✅ | Stabilization |
| **P2** | ✅ | Quality |
| **P2.5** | ✅ | OOP Refactor v2.0 |
| **P3** | 📋 | Intelligence |
| **P4** | ✅ | Graphify Integration |
| **P5** | ✅ | New UI/API/Docs |
| **P6** | 📋 | Ecosystem |

Детальний roadmap: `wiki_app/backend/roadmap/ROADMAP.md`

---

**Останнє оновлення:** 2026-08-01  
**Версія:** 2.0.0  
**Автор:** Archivist (Hermes Agent)
