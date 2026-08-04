---
title: "Transcription Workflow — YouTube, Google Chat, Podcasts"
type: playbook
description: "Повний workflow для збору, обробки та інтеграції транскрипцій у LLM Wiki"
created: 2026-07-28
updated: 2026-07-28
tags: [transcripts, meeting-notes, team-chat, project-management, google-chat, youtube, podcast, workflow]
sources: [wiki_app/tools/transcribe_youtube.py, wiki_app/tools/transcribe_google_chat.py]
confidence: high
links: [[transcripts]]
---

# Transcription Workflow

> **Створено:** 2026-07-28
> **Версія:** 1.0.0
> **Статус:** Active

---

## 📋 Огляд

Workflow транскрипцій дозволяє автоматизувати збір та інтеграцію транскрипцій з різних джерел у LLM Wiki.

### Підтримувані джерела

| Джерело | Інструмент | Формат входу | Вихідний каталог |
|---------|------------|--------------|------------------|
| YouTube | `transcribe_youtube.py` | URL/ID відео | `raw/transcripts/youtube/` → `wiki/transcripts/youtube/` |
| Google Chat | `transcribe_google_chat.py` | JSON/TXT експорт | `raw/transcripts/chats/` → `wiki/transcripts/chats/` |
| Подкасти | `transcribe_podcast.py` (TODO) | Audio file/URL | `raw/transcripts/podcasts/` → `wiki/transcripts/podcasts/` |

---

## 🎙️ YouTube Транскрипції

### Інструмент

`wiki_app/tools/transcribe_youtube.py`

### Використання

```bash
# Базова транскрипція
python wiki_app/tools/transcribe_youtube.py "https://youtube.com/watch?v=VIDEO_ID"

# З підтримкою мов (українська → англійська fallback)
python wiki_app/tools/transcribe_youtube.py "VIDEO_ID" --lang uk,en

# Формат глав (chapters)
python wiki_app/tools/transcribe_youtube.py "VIDEO_ID" --format chapters

# JSON формат
python wiki_app/tools/transcribe_youtube.py "VIDEO_ID" --format json

# Dry run (тільки перевірка)
python wiki_app/tools/transcribe_youtube.py "VIDEO_ID" --dry-run
```

### Аргументи

| Аргумент | Тип | За замовчуванням | Опис |
|----------|-----|------------------|------|
| `url` | positional | REQUIRED | YouTube URL або 11-символьний ID |
| `--lang` | string | `uk,en` | Кома-розділені мови |
| `--format` | enum | `transcript` | `transcript`, `chapters`, `json` |
| `--dry-run` | flag | `False` | Тільки перевірка, без збереження |

### Вихідні дані

**Raw файл:**
```
raw/transcripts/youtube/<slug>.md
```

**Wiki сторінка:**
```
wiki/transcripts/youtube/<slug>.md
```

### Frontmatter

```yaml
---
title: "Video Title"
type: event
description: YouTube transcript — [title]
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [youtube, transcripts, video]
sources: [raw/transcripts/youtube/<slug>.md]
confidence: high
links: []
---
```

---

## 💬 Google Chat Транскрипції

### Інструмент

`wiki_app/tools/transcribe_google_chat.py`

### Підтримувані формати входу

1. **Google Takeout JSON** — експорт з Google Takeout (`messages` array)
2. **Plain Text** — формат `Author [timestamp]: message`

### Використання

```bash
# Google Takeout JSON
python wiki_app/tools/transcribe_google_chat.py "chat_export.json" --group "Integra Media Team" --date 2026-07-28

# Plain text файл
python wiki_app/tools/transcribe_google_chat.py "chat_export.txt" --group "Project Alpha"

# Dry run
python wiki_app/tools/transcribe_google_chat.py "chat_export.json" --dry-run
```

### Аргументи

| Аргумент | Тип | За замовчуванням | Опис |
|----------|-----|------------------|------|
| `input` | positional | REQUIRED | JSON/TXT файл експорту |
| `--group` | string | `Chat` | Назва чат-групи |
| `--date` | string | today | Дата чату (YYYY-MM-DD) |
| `--source` | string | `google-chat` | Тип джерела |
| `--dry-run` | flag | `False` | Тільки перевірка, без збереження |

### Вихідні дані

**Raw файл:**
```
raw/transcripts/chats/<group>-<date>.md
```

**Wiki сторінка:**
```
wiki/transcripts/chats/<group>-<date>.md
```

### Frontmatter

```yaml
---
title: "GroupName — Chat Transcript YYYY-MM-DD"
type: event
description: Chat transcript from GroupName — YYYY-MM-DD
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [transcripts, meeting-notes, team-chat, project-management]
sources: [raw/transcripts/chats/<slug>.md]
confidence: high
links: []
---
```

---

## 🔄 Workflow Process

### Фаза 1: Збір (Асистент)

```
1. Отримати джерело (YouTube URL, Google Chat експорт)
2. Зберегти сирі дані у raw/
3. Провести первинну валідацію
4. Передати Бібліотекареві
```

### Фаза 2: Інтеграція (Бібліотекар)

```
1. Запустити відповідний інструмент транскрипції
2. Валідувати вхідні дані (мова, формат, повнота)
3. Згенерувати wiki-сторінку з frontmatter
4. Додати посилання на entity (якщо застосовно)
5. Оновити індекс категорії
```

### Фаза 3: Підтримка (Розробник)

```
1. Підтримувати інструменти транскрипції
2. Налаштовувати cron-задачі
3. Моніторити помилки та продуктивність
4. Додавати нові джерела
```

---

## 📊 Entity Linking

Для зв'язування транскрипцій з entity (компанії, команди, проекти):

```yaml
# У wiki-сторінці транскрипції:
links: [[integra-media]]  # Посилання на entity

# У entity сторінці:
links: [[integra-media-team-2026-07-27]]  # Посилання на транскрипцію
```

---

## ⚠️ Обмеження

| Обмеження | Опис | Рішення |
|-----------|------|---------|
| YouTube без субтитрів | Відео без транскрипції | Повідомити користувача |
| Google Chat API | Немає прямого API доступу | Використовувати Google Takeout |
| Подкасти | Не реалізовано | Створити `transcribe_podcast.py` |
| Мова | Залежить від доступних субтитрів | Fallback chain: `uk,en` |

---

## 🔧 Налаштування

### Залежності

```bash
pip install youtube-transcript-api yt-dlp
```

### Cron-задачі (опціонально)

```bash
# Щоденний моніторинг YouTube каналів
hermes cron create "transcribe-youtube" \
  --schedule "0 9 * * *" \
  --prompt "Transcribe new videos from subscribed channels"

# Щотижневий збір Google Chat експортів
hermes cron create "transcribe-chats" \
  --schedule "0 0 * * 1" \
  --prompt "Process weekly Google Chat exports"
```

---

## 📈 Метрики

| Метрика | Формула | Ціль |
|---------|---------|------|
| Успішність транскрипції | `успішні / спроби × 100%` | >90% |
| Час обробки | `середній час на файл` | <30 сек |
| Якість frontmatter | `% файлів з валідним frontmatter` | 100% |
| Entity linking | `% транскрипцій з entity links` | >50% |

---

## 📝 Приклади

### Приклад 1: YouTube транскрипція

```bash
# Зберегти транскрипт українською/англійською
python wiki_app/tools/transcribe_youtube.py \
  "https://youtube.com/watch?v=dQw4w9WgXcQ" \
  --lang uk,en \
  --format transcript
```

**Вихід:**
```
✅ Raw saved: /workspace/llm-wiki/raw/transcripts/youtube/dQw4w9WgXcQ.md
✅ Wiki saved: /workspace/llm-wiki/wiki/transcripts/youtube/dQw4w9WgXcQ.md
```

### Приклад 2: Google Chat експорт

```bash
# Імпортувати експорт Integra Media Team
python wiki_app/tools/transcribe_google_chat.py \
  "integrat-chat-2026-07-27.json" \
  --group "Integra Media Team" \
  --date 2026-07-27
```

**Вихід:**
```
📥 Parsed 47 messages
📝 Transcript formatted: 8,234 chars
✅ Raw saved: /workspace/llm-wiki/raw/transcripts/chats/integra-media-team-2026-07-27.md
✅ Wiki saved: /workspace/llm-wiki/wiki/transcripts/chats/integra-media-team-2026-07-27.md
```

---

## 🔗 Пов'язані документи

- [SCHEMA.md](../../../SCHEMA.md) — Теги та типи
- [AGENTS.md](../../../AGENTS.md) — Ролі агентів
- [wiki/transcripts/README.md](../../../wiki/transcripts/README.md) — Документація категорії
- [transcribe_youtube.py](../../tools/transcribe_youtube.py) — YouTube інструмент
- [transcribe_google_chat.py](../../tools/transcribe_google_chat.py) — Google Chat інструмент

---

**Wiki — це compounding knowledge. Кожна транскрипція робить базу ціннішою.**
