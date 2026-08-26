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

# Check which raw articles have new slugs
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
            new_articles.append((title, slug, article_path))
    except Exception as e:
        print(f'Error reading {article_path}: {e}')

print(f'\nNew articles that would be synced: {len(new_articles)}')
for title, slug, path in new_articles[:20]:
    print(f'  - {title} (slug: {slug})')

if len(new_articles) > 20:
    print(f'  ... and {len(new_articles) - 20} more')
