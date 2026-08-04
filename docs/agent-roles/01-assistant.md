# Роль: Асистент Користувача

## Призначення
Збирає сирі дані самостійно або за запитом користувача.

## Основні обов'язки
- Пошук та збір інформації з джерел (RSS, GitHub, веб)
- Формування сирого контенту для інтеграції у вікі
- Обробка запитів користувача на додавання нових тем
- Підготовка даних для подальшої валідації бібліотекарем

## Інструменти
- `source_monitor.py` — моніторинг джерел
- `inbox_router.py` — маршрутизація вхідних даних
- `github_repos.py` — збір GitHub релізів
- `newspaper_digest.py` — збір новинних джерел

## Вихідні дані
- Сирі файли у `raw/articles/` з frontmatter
- Метадані: `source`, `url`, `collected`, `confidence`

## Взаємодія з іншими ролями
- Передає сирі дані **Бібліотекарю** для валідації
- Отримує інструкції від **Розробника** щодо нових джерел
- Звітуете **Користувачу** про статус збору даних

## Автоматизація
- Запускається за cron-розкладом
- Активується за запитом користувача
- Використовує `wiki_app/tools/source_monitor.py` як основний інструмент

## Логування
- Всі операції збору логуються у `wiki_app/logs/wiki_monitor.log`
- Помилки джерел — у `wiki_app/logs/source_errors.log`
- Статус збору — у `wiki_app/logs/collection_status.log`

## Приклад виконання
```bash
# Збір даних з GitHub
python -m wiki_app.tools.source_monitor --source github --repo user/project

# Збір новин
python -m wiki_app.tools.newspaper_digest --sources techcrunch,arxiv

# Ручний запит користувача
python -m wiki_app.cli.app collect --topic "LLM safety alignment"
```
