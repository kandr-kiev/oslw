# 📘 Git Guide for Agents (Monti)

Цей гайд допоможе агенту Monti працювати з Git та GitHub.

---

## 🚀 Швидкий старт

### 1. Перевірка підключення

```bash
# Перевірити, чи підключено віддалений репозиторій
git remote -v

# Повинно показати:
# origin  https://github.com/kandr-kiev/llm-wiki.git (fetch)
# origin  https://github.com/kandr-kiev/llm-wiki.git (push)
```

### 2. Встановити токен для автентифікації (якщо потрібно)

```bash
# Встановити токен як змінну середовища
export GITHUB_TOKEN="your_personal_access_token_here"

# Або налаштувати git для зберігання облікових даних
git config --global credential.helper store
```

---

## 📋 Основні команди

### Статус та інспекція

```bash
# Перевірити статус змін
git status

# Показати дельту змін у файлі
git diff path/to/file.py

# Показати дельту всіх змін
git diff

# Показати статистику змін
git diff --stat

# Історія комітів (останні 10)
git log --oneline -10

# Показати коміти на віддаленій гілці
git log origin/main --oneline -10
```

### Додавання змін

```bash
# Додати конкретний файл
git add path/to/file.py

# Додати всі змінені файли
git add -A

# Додати всі нові файли (без видалених)
git add .

# Додати всі файли в директорії
git add path/to/dir/
```

### Коміти

```bash
# Створити коміт з повідомленням
git commit -m "📝 Опис змін"

# Створити коміт з додаванням файлу однією командою
git add file.py && git commit -m "📝 Додати file.py"

# Останній коміт (змінити повідомлення)
git commit --amend -m "Нове повідомлення"

# Скасувати останній коміт (зберігає зміни)
git reset HEAD~1
```

### Робота з гілками

```bash
# Створити нову гілку
git branch feature/name

# Перейти на гілку
git checkout feature/name

# Створити та перейти на нову гілку
git checkout -b feature/name

# Показати всі гілки
git branch -a

# Показати поточну гілку
git branch --show-current

# Показати різницю між гілками
git diff main..feature/name
```

---

## 🌐 Робота з GitHub (push/pull)

### Пуш на GitHub

```bash
# Пушити поточну гілку на origin
git push origin main

# Пушити конкретну гілку
git push origin feature/name

# Пушити з примусовим оновленням (обережно!)
git push --force origin feature/name

# Пушити з підтвердженням (для небезпечних операцій)
git push --follow-tags

# Пушити всі змінені файли однією командою
git add -A && git commit -m "📝 Зміни" && git push origin main
```

### Pull з GitHub

```bash
# Завантажити та об'єднати зміни
git pull origin main

# Завантажити без об'єднання (тільки fetch)
git fetch origin

# Показати відстань між локальною та віддаленою гілкою
git status -sb
```

### Sync

```bash
# Оновити локальну гілку з віддаленою
git pull --rebase origin main

# Скинути локальні зміни до віддаленого стану (обережно!)
git reset --hard origin/main

# Оновити всі підмодулі
git submodule update --init --recursive
```

---

## 🔧 Розширені операції

### Видалення файлів

```bash
# Видалити файл з індексу та диска
git rm path/to/file.py

# Видалити файл тільки з індексу (залишити на диску)
git rm --cached path/to/file.py

# Видалити всі файли в директорії
git rm -r path/to/dir/
```

### Пошук та відкат

```bash
# Знайти коміт за текстом
git log --all --grep="keyword" --oneline

# Знайти зміни в коді
git grep "function_name"

# Показати зміни в конкретному файлі за часом
git log --oneline -- path/to/file.py

# Відкотити до конкретного коміту
git reset --hard abc1234

# Створити гілку з коміту
git branch new-branch abc1234
```

### Ігнорування файлів

```bash
# Перевірити .gitignore
cat .gitignore

# Додати шаблон в .gitignore
echo "*.pyc" >> .gitignore

# Видалити файли з індексу, але залишити на диску
git rm --cached -r .
git add .
```

---

## 🤖 Чек-лист для агента Monti

### Перед commit

1. ✅ `git status` — перевірити, що зміни правильні
2. ✅ `git diff` — переглянути дельту
3. ✅ Переконатися, що немає конфіденційних даних (токени, паролі)

### Перед push

1. ✅ `git pull origin main` — отримати останні зміни
2. ✅ `git status -sb` — перевірити відстань між гілками
3. ✅ Переконатися, що тести проходять (якщо є)
4. ✅ `git push origin main` — пушити зміни

### Після push

1. ✅ `git status` — перевірити, що робоче дерево чисте
2. ✅ `git log --oneline -5` — переконатися, що коміти на місці

---

## ⚠️ Поширені помилки та рішення

### "Permission denied (publickey)"

```bash
# Використати HTTPS замість SSH
git remote set-url origin https://github.com/kandr-kiev/llm-wiki.git
```

### "Updates were rejected"

```bash
# Отримати та об'єднати зміни
git pull origin main --rebase

# Якщо конфлікти — вирішити їх, потім:
git add .
git commit
git push origin main
```

### "Merge conflict"

```bash
# Відкрити файл з конфліктом
# Знайти маркери <<<<<<< , ======= , >>>>>>>
# Виправити вручну
git add .
git commit
```

### "Detached HEAD"

```bash
# Повернутися на гілку
git checkout main

# Або створити нову гілку
git checkout -b new-branch
```

---

## 📝 Шаблони повідомлень комітів

```bash
# Новий файл
git commit -m "📝 Додати новий файл: filename.py"

# Зміна існуючого
git commit -m "🔧 Виправити помилку в filename.py"

# Оновлення
git commit -m "📚 Оновити документацію"

# Видалення
git commit -m "🗑️ Видалити застарілий файл"

# Тест
git commit -m "🧪 Додати тести для модуля"

# Документація
git commit -m "📖 Оновити README"
```

---

## 🔑 Токени та безпека

### Ніколи не комітти токени!

```bash
# Перевірити, чи немає токенів у змінах
git diff | grep -i "token\|password\|secret\|api_key"

# Якщо токен потрапив в коміт — видалити його
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch path/to/file' \
  --prune-empty --tag-name-filter cat -- --all
```

### Змінні середовища

```bash
# Завантажити змінні середовища
export GITHUB_TOKEN="your_token"

# Використовувати в скриптах
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/...
```

---

## 📊 Статистика репозиторію

```bash
# Кількість комітів
git rev-list --all --count

# Кількість файлів
git ls-files | wc -l

# Розмір репозиторію
du -sh .git

# Найактивніші автори
git shortlog -sn --all

# Найактивніші файли
git log --pretty=format: --name-only | sort | uniq -c | sort -nr | head -20
```

---

## 🎯 Швидкі команди для агента Monti

```bash
# Оновити все (pull + status)
git pull origin main && git status

# Додати, закомітити, пушити (все в одній команді)
git add -A && git commit -m "📝 Опис" && git push origin main

# Створити гілку для зміни
git checkout -b feature/description && git add -A && git commit -m "📝 Опис" && git push -u origin feature/description

# Скасувати всі зміни
git reset --hard HEAD
```

---

**Пам'ятай:** Git — це інструмент, а не ворог. Використовуй його з розумом та обережністю! 🚀
