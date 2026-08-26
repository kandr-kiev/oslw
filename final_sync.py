from pathlib import Path
import re
from datetime import datetime, timezone
from oslw.config.settings import Settings
from oslw.application import SourceService
from oslw.infrastructure.database import FileManager, PageMeta

def sanitize_slug(slug):
    slug = slug.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')[:100]
    return slug or 'untitled'

wiki_root = Path('/workspace/llm-wiki')
settings = Settings(wiki_root=wiki_root)
source_service = SourceService(wiki_root=settings.wiki_root)

raw_articles = source_service.get_raw_articles()

# Existing slugs
existing_slugs = set()
wiki_path = settings.wiki_root / "wiki"
for md_file in wiki_path.rglob("*.md"):
    if md_file.name not in ('index.md', 'SCHEMA.md'):
        existing_slugs.add(md_file.stem)

synced = 0
skipped = 0
errors = 0
error_log = []

fm = FileManager(wiki_root=wiki_root)
now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

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
        if not slug:
            slug = 'untitled-' + str(synced)
        
        if slug in existing_slugs:
            skipped += 1
            continue
        
        page_meta = PageMeta(
            slug=slug,
            title=title,
            description='',
            type='concept',
            tags=['synced'],
            sources=[],
            sha256='',
            created=now,
            updated=now,
            path=None,
            content=content,
            raw_content=''
        )
        
        fm.write_page(page_meta)
        existing_slugs.add(slug)
        synced += 1
        
    except Exception as e:
        errors += 1
        error_log.append(f"{article_path}: {str(e)}")

print(f"Raw articles found: {len(raw_articles)}")
print(f"Synced: {synced}")
print(f"Skipped: {skipped}")
print(f"Errors: {errors}")

if error_log:
    print("\nErrors:")
    for err in error_log[:20]:
        print(f"  {err}")
