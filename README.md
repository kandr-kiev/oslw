# OSLW Wiki — Full Stack Web System

**OSLW** (Open Source Local Wiki) — модульна система керування wiki з повноцінним веб-інтерфейсом, побудована на FastAPI + React + Nginx.

## 🏗️ Архітектура

```
┌─────────────────────────────────────────────────────────────┐
│                    Windows Host                              │
│                                                              │
│  http://oslw.local    ──→  Nginx (Reverse Proxy, port 80)  │
│  http://localhost:8000 ──→  FastAPI (Backend API)          │
│  http://localhost:5173 ──→  Vite + React (Frontend Dev)   │
│                              │                               │
│                              ├─→ /workspace/llm-wiki (Wiki) │
│                              └─→ API Routes                  │
└─────────────────────────────────────────────────────────────┘
```

### Компоненти

| Компонент | Порт | Технологія | Призначення |
|-----------|------|------------|-------------|
| **Backend** | 8000 | FastAPI + Uvicorn | REST API + статичні файли |
| **Frontend** | 5173 | Vite + React + Tailwind | UI з hot-reload |
| **Nginx** | 80 | Nginx Alpine | Reverse proxy + CORS |

## 🚀 Швидкий старт

### Вимоги

- ✅ Docker Desktop (з WSL2 backend)
- ✅ PowerShell 5.1+ (Windows 10/11)
- ✅ 4GB+ RAM

### Запуск

```powershell
# 1. Перейдіть до папки проекту
cd C:\path\to\projects\oslw

# 2. Запустіть скрипт
.\run-oslw.ps1
```

> ⚠️ **Важливо:** Перший запуск вимагає прав адміністратора для налаштування `hosts` файлу (резолв `oslw.local`). Скрипт автоматично запитає UAC elevation.

Скрипт автоматично:
1. ✅ Перевіряє Docker Desktop
2. ✅ Налаштовує `hosts` файл (`127.0.0.1 oslw.local`)
3. ✅ Очищає DNS кеш
4. ✅ Перевіряє порти (8000, 5173, 80)
5. ✅ Будує Docker образи
6. ✅ Запускає 3 контейнери
7. ✅ Чекає на готовність backend
8. ✅ Пропонує відкрити браузер

### Аргументи запуску

| Команда | Опис |
|---------|------|
| `.\run-oslw.ps1` | Повний запуск (hostname + Docker) |
| `.\run-oslw.ps1 -NoHostname` | Запуск без налаштування hostname |
| `.\run-oslw.ps1 -Restart` | Перезапуск без rebuild |
| `.\run-oslw.ps1 -Stop` | Зупинити систему |

### Ручний запуск

```bash
# Зупинити попередні контейнери
docker compose down

# Зібрати та запустити
docker compose up --build -d

# Перевірити логи
docker compose logs -f

# Зупинити
docker compose down
```

## 🌐 Доступ

| Сервіс | URL | Опис |
|--------|-----|------|
| **Веб-інтерфейс** | http://oslw.local | Nginx (reverse proxy) |
| **API** | http://localhost:8000 | FastAPI (прямий доступ) |
| **Frontend (dev)** | http://localhost:5173 | Vite (hot-reload) |
| **API Docs** | http://localhost:8000/docs | Swagger UI (FastAPI) |

> **Примітка:** `http://oslw.local` працює після налаштування `hosts` файлу. Якщо hostname не налаштовано, використовуйте `http://localhost:80`.

## 📡 API Endpoints

| Method | Endpoint | Опис |
|--------|----------|------|
| `GET` | `/health` | Перевірка здоров'я |
| `GET` | `/api/pages` | Список усіх сторінок |
| `GET` | `/api/pages/{slug}` | Конкретна сторінка |
| `GET` | `/api/stats` | Статистика wiki |
| `GET` | `/api/search?q=...` | Пошук |

## 📁 Структура проекту

```
oslw/
├── docker-compose.yml    # Оркестрація контейнерів
├── Dockerfile.backend    # Backend образ (FastAPI)
├── Dockerfile.frontend   # Frontend образ (Vite)
├── nginx/
│   └── nginx.conf        # Reverse proxy конфігурація
├── src/
│   └── oslw/             # FastAPI код
│       ├── api/
│       │   ├── main.py   # FastAPI app
│       │   └── routes.py # API routes
│       ├── config/       # Налаштування
│       └── cli/          # CLI команди
├── frontend/
│   ├── index.html        # HTML шаблон
│   ├── js/
│   │   ├── app.js        # React додаток
│   │   └── data.js       # Дані wiki
│   ├── css/
│   │   └── style.css     # Стилі
│   ├── package.json      # npm залежності
│   └── vite.config.js    # Vite конфігурація
├── tests/                # Тести
├── pyproject.toml        # Python залежності
├── .env.example          # Приклад env
├── run-oslw.ps1          # Єдиний скрипт запуску
└── README.md             # Цей файл
```

## 🔧 Налаштування

### Змінні середовища

Створіть `.env` файл з `.env.example`:

```bash
cp .env.example .env
```

Основні змінні:

```bash
# Wiki root
OSLW_WIKI_ROOT=/workspace/llm-wiki

# API
OSLW_API_HOST=0.0.0.0
OSLW_API_PORT=8000

# Frontend
VITE_API_URL=http://localhost:8000
```

### Port Mapping

Порти налаштовані в `docker-compose.yml`:

```yaml
ports:
  - "8000:8000"  # Windows:8000 → Container:8000
  - "5173:5173"  # Windows:5173 → Container:5173
  - "80:80"      # Windows:80 → Nginx:80
```

### Hostname Setup

Для доступу через `http://oslw.local` без порту:

1. Скрипт `run-oslw.ps1` автоматично додає `127.0.0.1 oslw.local` у `hosts`
2. Очищує DNS кеш (`ipconfig /flushdns`)
3. Nginx налаштований на `server_name localhost oslw oslw.local`

Якщо потрібно вручну:
```powershell
# PowerShell ВІД ІМЕНІ АДМІНІСТРАТОРА
Add-Content -Path "C:\Windows\System32\drivers\etc\hosts" -Value "`n127.0.0.1    oslw.local"
ipconfig /flushdns
```

## 🐛 Вирішення проблем

### Порт зайнятий

```powershell
# Знайти процес на порту
netstat -ano | findstr :8000

# Зупинити процес (замініть PID)
Stop-Process -Id <PID> -Force
```

### Контейнери не запускаються

```bash
# Перевірити логи
docker compose logs backend
docker compose logs frontend
docker compose logs nginx

# Видалити та перевстановити
docker compose down -v
docker compose up --build -d
```

### `oslw.local` не резолвиться

```powershell
# Перевірити hosts
Get-Content "C:\Windows\System32\drivers\etc\hosts" | Select-String "oslw"

# Очистити кеш
ipconfig /flushdns

# Перевірити DNS
Resolve-DnsName oslw.local
```

### Execution Policy error

```powershell
# Одноразовий обхід
powershell -ExecutionPolicy Bypass -File .\run-oslw.ps1

# Або налаштувати для поточного користувача
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Hot-reload не працює

```bash
# Перевірити монтирування
docker inspect oslw-backend | grep -A 10 Mounts
docker inspect oslw-frontend | grep -A 10 Mounts
```

## 📊 Моніторинг

```bash
# Статус контейнерів
docker ps --filter name=oslw

# Логи в реальному часі
docker compose logs -f

# Статистика ресурсів
docker stats oslw-backend oslw-frontend oslw-nginx

# Вхід в контейнер
docker exec -it oslw-backend /bin/bash
docker exec -it oslw-frontend /bin/sh
```

## 🔄 Розгортання

### Продакшен

```bash
# Зібрати фронтенд
cd frontend && npm run build && cd ..

# Запустити з nginx
docker compose up -d --build nginx
```

### Dev Mode

```bash
# З hot-reload для обох сервісів
docker compose up --build
```

## 📝 Ліцензія

MIT License

## 👥 Команда

OSLW Team — Modular Wiki Management System
