from pathlib import Path
from oslw.config.settings import Settings
from oslw.application import SourceService, PageService
from oslw.infrastructure.database import FileManager, PageMeta
from datetime import datetime, timezone

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
        
        slug = title.lower().replace(' ', '-').replace('—', '-')[:100]
        
        if slug not in existing_slugs:
            new_articles.append((article_path, title, slug, content))
    except Exception:
        pass

print(f'New articles to sync: {len(new_articles)}')

# Now sync them
fm = FileManager(wiki_root=wiki_root)
synced = 0
errors = 0

for article_path, title, slug, content in new_articles:
    try:
        # Determine category
        category = 'concept'
        
        # Create page meta
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        page_meta = PageMeta(
            slug=slug,
            title=title,
            description='',
            type=category,
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
        print(f'✅ Synced: {title}')
    except Exception as e:
        errors += 1
        print(f'❌ Error: {article_path} - {str(e)}')

print(f'\n📊 Sync Results:')
print(f'   Synced: {synced}')
print(f'   Errors: {errors}')
