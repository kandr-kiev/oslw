from pathlib import Path
from oslw.config.settings import Settings
from oslw.application import SourceService

wiki_root = Path('/workspace/llm-wiki')
settings = Settings(wiki_root=wiki_root)
source_service = SourceService(wiki_root=settings.wiki_root)

raw_articles = source_service.get_raw_articles()

existing_slugs = set()
wiki_path = settings.wiki_root / "wiki"
for md_file in wiki_path.rglob("*.md"):
    if md_file.name not in ('index.md', 'SCHEMA.md'):
        existing_slugs.add(md_file.stem)

new_count = 0
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
            new_count += 1
            if new_count <= 10:
                print(f"New: {title[:80]}")
    except:
        pass

print(f"\nTotal new: {new_count}")
