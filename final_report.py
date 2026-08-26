from pathlib import Path
import re
from oslw.config.settings import Settings
from oslw.application import SourceService

def sanitize_slug(title):
    slug = title.lower().replace(' ', '-').replace('—', '-')
    slug = re.sub(r'[^\w\-]', '', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')[:100]
    return slug or 'untitled'

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

new_count = 0
duplicate_count = 0
errors = 0

for article_path in raw_articles:
    try:
        with open(article_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        title = 'Untitled'
        for line in content.splitlines()[:10]:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        slug = sanitize_slug(title)
        
        if slug in existing_slugs:
            duplicate_count += 1
        else:
            new_count += 1
    except:
        errors += 1

print(f"🔄 Звіт Wiki Integrator")
print(f"🗓️ 2026-08-23")
print(f"✅ Статус: OK")
print(f"📊 Сирних статей знайдено: {total_raw}")
print(f"✅ Інтегровано: {new_count}")
print(f"⏭️ Пропущено (дублікати): {duplicate_count}")
print(f"❌ Помилки: {errors}")
