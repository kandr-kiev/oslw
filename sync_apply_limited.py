from pathlib import Path
from oslw.config.settings import Settings
from oslw.application import SourceService, PageService

wiki_root = Path('/workspace/llm-wiki')
settings = Settings(wiki_root=wiki_root)

source_service = SourceService(wiki_root=settings.wiki_root)
page_service = PageService(wiki_root=settings.wiki_root)

raw_articles = source_service.get_raw_articles()
print(f'Raw articles found: {len(raw_articles)}')

# Get existing wiki pages
existing_slugs = set()
all_pages = page_service.file_manager.list_wiki_pages()
for p in all_pages:
    existing_slugs.add(p.slug)
print(f'Existing wiki pages: {len(existing_slugs)}')

# Limit to first 200 to get quick results
limit = 200
raw_articles = raw_articles[:limit]
print(f'Processing limit: {limit}')

synced = 0
skipped = 0
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

        slug = title.lower().replace(' ', '-').replace('—', '-')[:100]

        if slug in existing_slugs:
            skipped += 1
            continue

        page_service.create_page(
            title=title,
            content=content,
            slug=slug,
            page_type='concept',
            tags=['synced'],
        )
        existing_slugs.add(slug)
        synced += 1
        print(f'✅ Synced: {title}')

    except Exception as e:
        print(f'❌ Error: {article_path} - {str(e)}')
        errors += 1

print(f'\n📊 Sync Results (limited to {limit}):')
print(f'   Synced: {synced}')
print(f'   Skipped: {skipped}')
print(f'   Errors: {errors}')
