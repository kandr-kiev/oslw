from pathlib import Path

wiki_root = Path('/workspace/llm-wiki')
wiki_path = wiki_root / "wiki"

# Check some specific slugs
test_slugs = [
    'issue-8329-fix-replace-listlist-with-sequence-in-function-parameter-annotations',
    'issue-14169-remove-jax-flax',
    'release-moonshot-aikimi-code0270'
]

existing = set()
for md_file in wiki_path.rglob("*.md"):
    if md_file.name not in ('index.md', 'SCHEMA.md'):
        existing.add(md_file.stem)

for slug in test_slugs:
    print(f"{slug}: {'EXISTS' if slug in existing else 'MISSING'}")
