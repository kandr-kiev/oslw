"""Test configuration and fixtures for OSLW."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_wiki_root():
    """Create a temporary wiki root directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        wiki_root = Path(tmpdir)

        # Create directory structure
        (wiki_root / "wiki").mkdir()
        (wiki_root / "wiki" / "concepts").mkdir()
        (wiki_root / "wiki" / "comparisons").mkdir()
        (wiki_root / "wiki" / "playbooks").mkdir()
        (wiki_root / "wiki" / "synthesis").mkdir()
        (wiki_root / "wiki" / "entities").mkdir()
        (wiki_root / "raw" / "articles").mkdir(parents=True)

        # Create index.md
        (wiki_root / "wiki" / "index.md").write_text("# LLM-Wiki Index\n\n")

        # Create SCHEMA.md
        (wiki_root / "wiki" / "SCHEMA.md").write_text("# Wiki Schema\n\n")

        yield wiki_root


@pytest.fixture
def sample_wiki_page(temp_wiki_root):
    """Create a sample wiki page for testing."""
    content = """---
title: Transformer Architecture
slug: transformer-architecture
type: concept
tags: [transformers, architecture, nlp]
created: 2024-01-01 00:00:00 UTC
updated: 2024-01-01 00:00:00 UTC
---

# Transformer Architecture

The Transformer is a neural network architecture that uses self-attention mechanisms.

## Overview

Transformers revolutionized natural language processing.

## Components

- Self-attention
- Feed-forward networks
- Layer normalization
"""
    page_path = temp_wiki_root / "wiki" / "concepts" / "transformer-architecture.md"
    page_path.write_text(content)
    return page_path


@pytest.fixture
def sample_wiki_pages(temp_wiki_root):
    """Create sample wiki pages for testing."""
    pages = [
        {
            "name": "transformer-architecture.md",
            "content": """---
title: Transformer Architecture
slug: transformer-architecture
type: concept
tags: [transformers, architecture]
created: 2024-01-01 00:00:00 UTC
updated: 2024-01-01 00:00:00 UTC
---

# Transformer Architecture

The Transformer is a neural network architecture that uses self-attention.

## Overview

Transformers revolutionized NLP.

[[attention-mechanism]]
[[encoder-decoder]]
""",
        },
        {
            "name": "attention-mechanism.md",
            "content": """---
title: Attention Mechanism
slug: attention-mechanism
type: concept
tags: [attention, transformers]
created: 2024-01-01 00:00:00 UTC
updated: 2024-01-01 00:00:00 UTC
---

# Attention Mechanism

Attention allows models to focus on relevant parts of input.

## Types

- Self-attention
- Cross-attention
""",
        },
        {
            "name": "encoder-decoder.md",
            "content": """---
title: Encoder-Decoder
slug: encoder-decoder
type: concept
tags: [architecture, seq2seq]
created: 2024-01-01 00:00:00 UTC
updated: 2024-01-01 00:00:00 UTC
---

# Encoder-Decoder

The encoder-decoder architecture processes input and generates output.

## Architecture

- Encoder processes input
- Decoder generates output
""",
        },
    ]

    for page in pages:
        page_path = temp_wiki_root / "wiki" / "concepts" / page["name"]
        page_path.write_text(page["content"])

    return pages
