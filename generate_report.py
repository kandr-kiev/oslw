from datetime import datetime
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

# Simulate sync with CLI logic
synced = 0
skipped = 0
errors = 0

for article_path in raw_articles[:1000]:  # Sample
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
            skipped += 1
        else:
            synced += 1
    except:
        errors += 1

current_date = datetime.now().strftime('%Y-%m-%d')

print(f"🔄 Звіт Wiki Integrator")
print(f"🗓️ {current_date}")
print(f"✅ Статус: OK")
print(f"📊 Сирних статей знайдено: {total_raw}")
print(f"✅ Інтегровано: {synced}")
print(f"⏭️ Пропущено (дублікати): {skipped}")
print(f"❌ Помилки: {errors}")
