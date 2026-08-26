import re

def sanitize_slug(title):
    slug = title.lower().replace(' ', '-').replace('—', '-')[:100]
    # Remove invalid filename chars
    slug = re.sub(r'[^\w\-]', '', slug)
    return slug

titles = [
    "Issue #8329: fix: replace list/List with Sequence in function parameter annotations",
    "Release @moonshot-ai/kimi-code@0.27.0",
    "Model: deepseek-ai/deepseek-r1"
]

for t in titles:
    slug = sanitize_slug(t)
    print(f"Original: {t[:60]}")
    print(f"Slug: {slug}")
    print()
