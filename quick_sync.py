from pathlib import Path
from oslw.config.settings import Settings
from oslw.application import SourceService, PageService

wiki_root = Path('/workspace/llm-wiki')
settings = Settings(wiki_root=wiki_root)
source_service = SourceService(wiki_root=settings.wiki_root)
page_service = PageService(wiki_root=settings.wiki_root)

raw_articles = source_service.get_raw_articles()
print(f'Raw articles found: {len(raw_articles)}')

# Get existing slugs fast via filesystem
existing_slugs = set()
wiki_path = settings.wiki_root / "wiki"
for md_file in wiki_path.rglob("*.md"):
    existing_slugs.add(md_file.stem)
print(f'Existing wiki pages: {len(existing_slugs)}')

synced = 0
skipped = 0
errors = 0
error_list = []

# Process only new articles - limit to first 100 to test
count = 0
for article_path in raw_articles:
    if count >= 100:  # Test with first 100
        break
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
        
        # Create page directly via file manager to avoid slow validation
        from oslw.infrastructure.database import FileManager, PageMeta
        fm = FileManager(wiki_root=wiki_root)
        page_meta = PageMeta(
            slug=slug,
            title=title,
            description='',
            type='concept',
            tags=['synced'],
            sources=[]
        )
        fm.create_page(page_meta, content)
        existing_slugs.add(slug)
        synced += 1
        print(f'✅ Synced: {title}')
        
    except Exception as e:
        errors += 1
        error_list.append(str(e))
        print(f'❌ Error: {article_path} - {str(e)}')
    
    count += 1

print(f'\n📊 Sync Results (first 100):')
print(f'   Synced: {synced}')
print(f'   Skipped: {skipped}')
print(f'   Errors: {errors}')
