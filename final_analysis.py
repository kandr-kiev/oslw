from pathlib import Path
from oslw.config.settings import Settings
from oslw.application import SourceService

wiki_root = Path('/workspace/llm-wiki')
settings = Settings(wiki_root=wiki_root)
source_service = SourceService(wiki_root=settings.wiki_root)

raw_articles = source_service.get_raw_articles()
total_raw = len(raw_articles)

existing_slugs = set()
wiki_path = settings.wiki_root / "wiki"
for md_file in wiki_path.rglob("*.md"):
    if md_file.name not in ('index.md', 'SCHEMA.md'):
        existing_slugs.add(md_file.stem)

new_articles = []
invalid_slugs = []

for article_path in raw_articles:
    try:
        with open(article_path, 'r', encoding='utf-8') as f:
            content = f.read()
        title = 'Untitled'
        for line in content.splitlines()[:10]:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        slug = title.lower().replace(' ', '-').replace('—', '-')[:100]
        
        if slug in existing_slugs:
            continue
        
        # Check if slug is valid filename
        import re
        if re.match(r'^[\w\-\.]+$', slug):
            new_articles.append((title, slug))
        else:
            invalid_slugs.append((title, slug))
    except:
        pass

print(f"🔄 Звіт Wiki Integrator")
print(f"🗓️ 2026-08-23")
print(f"✅ Статус: ⚠️ Помилки")
print(f"📊 Сирних статей знайдено: {total_raw}")
print(f"✅ Інтегровано: 0")
print(f"⏭️ Пропущено (дублікати): {total_raw - len(new_articles) - len(invalid_slugs)}")
print(f"❌ Помилки: {len(invalid_slugs)}")
print(f"\n📝 Деталі:")
print(f"   Валідних нових статей: {len(new_articles)}")
print(f"   Статей з недопустимими символами в slug: {len(invalid_slugs)}")

if invalid_slugs:
    print(f"\n   Приклади проблемних slug:")
    for title, slug in invalid_slugs[:5]:
        print(f"     - {title[:60]}")
        print(f"       slug: {slug[:80]}")
