from pathlib import Path
import re
from oslw.config.settings import Settings
from oslw.application import SourceService
from oslw.infrastructure.database import FileManager, PageMeta
from datetime import datetime, timezone

def sanitize_slug(slug):
    # Replace problematic characters
    slug = slug.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special chars except word, space, hyphen
    slug = re.sub(r'[-\s]+', '-', slug)  # Replace spaces and multiple hyphens with single hyphen
    slug = slug.strip('-')[:100]
    return slug or 'untitled'

wiki_root = Path('/workspace/llm-wiki')
settings = Settings(wiki_root=wiki_root)
source_service = SourceService(wiki_root=settings.wiki_root)

raw_articles = source_service.get_raw_articles()
print(f'Raw articles found: {len(raw_articles)}')

# Fast existing slugs via filesystem
existing_slugs = set()
wiki_path = settings.wiki_root / "wiki"
for md_file in wiki_path.rglob("*.md"):
    if md_file.name not in ('index.md', 'SCHEMA.md'):
        existing_slugs.add(md_file.stem)
print(f'Existing wiki pages: {len(existing_slugs)}')

# Find articles that are truly new
new_articles = []
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
        
        if slug not in existing_slugs:
            new_articles.append((article_path, title, slug, content))
    except Exception:
        pass

print(f'New articles to sync: {len(new_articles)}')

# Now sync them
fm = FileManager(wiki_root=wiki_root)
synced = 0
skipped = 0
errors = 0
error_details = []

for article_path, title, slug, content in new_articles:
    try:
        if not slug:
            slug = 'untitled-' + str(synced)
        
        # Check again
        if slug in existing_slugs:
            skipped += 1
            continue
        
        # Create page meta
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
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
        
        # Write page
        fm.write_page(page_meta)
        existing_slugs.add(slug)
        synced += 1
        print(f'✅ Synced: {title} -> {slug}')
    except Exception as e:
        errors += 1
        error_details.append(f'{title}: {str(e)}')
        print(f'❌ Error: {title} - {str(e)}')

print(f'\n📊 Sync Results:')
print(f'   Synced: {synced}')
print(f'   Skipped: {skipped}')
print(f'   Errors: {errors}')
if error_details:
    print('\nErrors:')
    for err in error_details[:10]:
        print(f'  - {err}')
