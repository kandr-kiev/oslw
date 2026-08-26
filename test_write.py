from oslw.infrastructure.database import FileManager, PageMeta
from pathlib import Path

wiki_root = Path('/workspace/llm-wiki')
fm = FileManager(wiki_root=wiki_root)

page_meta = PageMeta(
    slug='test-page',
    title='Test Page',
    description='',
    type='concept',
    tags=['test'],
    sources=[],
    sha256='',
    created='2026-01-01 00:00:00 UTC',
    updated='2026-01-01 00:00:00 UTC',
    path=None,
    content='# Test Content',
    raw_content=''
)

try:
    path = fm.write_page(page_meta)
    print(f'Wrote to: {path}')
    print(f'Exists: {path.exists()}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
