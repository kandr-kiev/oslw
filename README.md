# OSLW - Modular Wiki Management System

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**OSLW** (Open Source Lightweight Wiki) — модульна система для управління wiki-базами знань.

## 🎯 Можливості

- **Integratіon** — автоматична інтеграція контенту з raw → wiki
- **WikiDoctor** — аудит якості wiki-сторінок з автоматичним виправленням
- **Graph** — генерація графа знань з wiki-посилань
- **Monitor** — моніторинг джерел (RSS, GitHub, HuggingFace, YouTube)
- **Digest** — щоденні дайджести нових статей
- **Search** — пошук по wiki з концептуальним ранжуванням

## 🏗️ Архітектура

```
src/oslw/
├── config/          # Settings, logging
├── core/            # Domain primitives, exceptions
├── domain/          # Business logic (framework-agnostic)
│   ├── wiki/        # Wiki pages, index, integrity
│   ├── sources/     # Source monitoring, ingestion
│   ├── graph/       # Graph generation, query
│   ├── quality/     # Doctor, lint, cleanup
│   └── digest/      # Newspaper digest
├── infrastructure/  # External integrations
├── application/     # Use-case services
├── api/             # FastAPI endpoints
└── cli/             # Typer CLI
```

## 🚀 Швидкий старт

### 1. Встановлення

```bash
# Клонувати репозиторій
git clone https://github.com/kandr-kiev/oslw.git
cd oslw

# Встановити залежності
make dev

# Налаштувати середовище
cp .env.example .env
# Відредагуй .env (WIKI_ROOT, DATABASE_URL, тощо)
```

### 2. Запуск

```bash
# Запустити API сервер
make run

# API буде доступний на http://localhost:8000
# Документація: http://localhost:8000/api/docs
```

### 3. CLI

```bash
# Перевірка стану wiki
oslw doctor diagnose

# Інтеграція нових статей
oslw sync

# Генерація графа
oslw graph generate

# Щоденний дайджест
oslw digest today
```

## 📁 Структура проекту

```
oslw/
├── src/oslw/          # Python package
│   ├── main.py        # FastAPI app
│   ├── config/        # Configuration
│   ├── core/          # Domain primitives
│   ├── domain/        # Business logic
│   ├── infrastructure/# External integrations
│   ├── application/   # Use-case services
│   ├── api/           # REST API
│   └── cli/           # CLI commands
├── frontend/          # Next.js 15 (App Router)
├── tests/             # Pytest tests
├── docs/              # MkDocs documentation
└── scripts/           # Deployment scripts
```

## 🧪 Тести

```bash
# Запустити всі тести
make test

# Швидкі тести (без coverage)
make test-fast
```

## 📚 Документація

- **API**: `http://localhost:8000/api/docs`
- **Project docs**: `make docs` (генерує в `site/`)

## 🛠️ Розробка

```bash
# Лінтинг
make lint

# Форматування
make format

# Очистка
make clean
```

## 📝 Ліцензія

MIT License
