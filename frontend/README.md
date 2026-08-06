# OSLW Wiki Frontend

Перша версія фронтенду для перегляду wiki сторінок OSLW.

## Структура

```
frontend/
├── index.html      # Головна сторінка SPA
├── css/
│   └── style.css   # Стилі (темна тема)
├── js/
│   └── app.js      # JavaScript логіка
└── README.md       # Цей файл
```

## Можливості

- 📚 **Перегляд списку сторінок** — пагінація, фільтрація за категорією
- 🔍 **Пошук** — по всій wiki за ключовими словами
- 📊 **Статистика** — кількість сторінок, типи, категорії, теги
- 📄 **Детальний перегляд** — markdown рендеринг контенту
- 🎨 **Темна тема** — оптимізована для довгої роботи

## API Endpoints

| Endpoint | Метод | Опис |
|----------|-------|------|
| `/api/pages` | GET | Список сторінок (пагінація) |
| `/api/pages/{slug}` | GET | Детальна інформація про сторінку |
| `/api/stats` | GET | Статистика wiki |
| `/api/search` | GET | Пошук сторінок |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger UI (FastAPI) |

## Запуск

```bash
# Через CLI
python -m oslw.cli server --host 0.0.0.0 --port 8000

# Безпосередньо
cd /workspace/projects/oslw
uvicorn oslw.api.main:app --host 0.0.0.0 --port 8000
```

## Доступ

- **Frontend:** http://localhost:8000/
- **API Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

## Технічні деталі

- **Vanilla JavaScript** — без фреймворків
- **CSS Variables** — темна тема з CSS custom properties
- **SPA Routing** — клієнтська навігація
- **Async/Await** — асинхронні запити до API
- **Responsive Design** — адаптивний дизайн

## План розвитку

- [ ] Markdown рендеринг з підсвіткою синтаксису
- [ ] Історія перегляду
- [ ] Сповіщення про оновлення
- [ ] Експорт сторінок
- [ ] Редагування сторінок
- [ ] Категорії та теги з візуалізацією
- [ ] PWA підтримка
