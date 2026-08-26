from pathlib import Path
from oslw.config.settings import Settings
from oslw.application import SourceService

wiki_root = Path('/workspace/llm-wiki')
settings = Settings(wiki_root=wiki_root)
source_service = SourceService(wiki_root=settings.wiki_root)

raw_articles = source_service.get_raw_articles()
print(f'Raw articles found: {len(raw_articles)}')

# Fast check - just count
existing_slugs = set()
wiki_path = settings.wiki_root / "wiki"
count = 0
if wiki_path.exists():
    for md_file in wiki_path.rglob("*.md"):
        existing_slugs.add(md_file.stem)
        count += 1
        if count % 1000 == 0:
            print(f'Counted {count} wiki pages...')
print(f'Existing wiki pages: {len(existing_slugs)}')

# Find new articles quickly
new_count = 0
sample_titles = []
for i, article_path in enumerate(raw_articles[:100]):
    try:
        with open(article_path, 'r', encoding='utf-8') as f:
            content = f.read()
        title = 'Untitled'
        for line in content.splitlines()[:5]:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        slug = title.lower().replace(' ', '-').replace('—', '-')[:100]
        if slug not in existing_slugs:
            new_count += 1
            if len(sample_titles) < 5:
                sample_titles.append((title, slug))
    except:
        pass

print(f'\nNew articles in first 100 samples: {new_count}')
print(f'Sample new titles: {sample_titles}')
