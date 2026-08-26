#!/usr/bin/env python3
"""Fix wiki issues based on doctor.log recommendations."""

import os
import re
import hashlib
from datetime import datetime

WIKI_DIR = '/workspace/llm-wiki/wiki'
DRY_RUN = False

def get_slug_from_filename(filepath):
    """Generate slug from filename."""
    basename = os.path.basename(filepath)
    slug = os.path.splitext(basename)[0]
    # Ensure lowercase, replace spaces with hyphens
    slug = slug.lower().replace(' ', '-')
    return slug

def compute_sha256(filepath):
    """Compute SHA256 hash of file content."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def parse_simple_yaml(text):
    """Minimal YAML parser for frontmatter (key: value lines)."""
    result = {}
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            # Handle inline lists like [a, b, c]
            if value.startswith('[') and value.endswith(']'):
                items = [i.strip().strip("'\"") for i in value[1:-1].split(',')]
                result[key] = items
            else:
                result[key] = value
    return result

def format_simple_yaml(fm):
    """Minimal YAML writer for frontmatter."""
    lines = []
    for key, value in fm.items():
        if isinstance(value, list):
            items = ', '.join(f"'{i}'" for i in value)
            lines.append(f'{key}: [{items}]')
        else:
            lines.append(f'{key}: {value}')
    return '\n'.join(lines)

def parse_frontmatter(content):
    """Parse YAML frontmatter from markdown content."""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2]
            fm = parse_simple_yaml(fm_text)
            return fm, body
    return {}, content

def write_frontmatter(fm, body):
    """Write YAML frontmatter back to markdown."""
    fm_text = format_simple_yaml(fm)
    return '---\n' + fm_text + '\n---\n' + body

def fix_heading_skips(content):
    """Fix heading level skips in markdown content."""
    lines = content.split('\n')
    fixed = []
    current_level = 1  # Start with H1
    
    for line in lines:
        if line.startswith('#'):
            # Count heading level
            level = len(line) - len(line.lstrip('#'))
            if level > current_level + 1:
                # Skip detected, adjust to current_level + 1
                level = current_level + 1
            current_level = level
            line = '#' * level + line[level:]
        fixed.append(line)
    
    return '\n'.join(fixed)

def process_wiki():
    """Process all wiki files."""
    stats = {
        'processed': 0,
        'frontmatter_fixed': 0,
        'sha256_added': 0,
        'headings_fixed': 0,
        'degenerate_removed': 0,
    }
    
    # Step 1: Remove degenerate file
    degenerate_file = os.path.join(WIKI_DIR, 'comparisons', '.md')
    if os.path.exists(degenerate_file):
        if DRY_RUN:
            print(f'[DRY-RUN] Would remove: {degenerate_file}')
        else:
            os.remove(degenerate_file)
            print(f'Removed: {degenerate_file}')
        stats['degenerate_removed'] += 1
    
    # Step 2: Process all .md files
    for root, dirs, files in os.walk(WIKI_DIR):
        for filename in files:
            if not filename.endswith('.md'):
                continue
            
            filepath = os.path.join(root, filename)
            stats['processed'] += 1
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            fm, body = parse_frontmatter(content)
            modified = False
            
            # Fix missing fields
            if 'slug' not in fm:
                fm['slug'] = get_slug_from_filename(filepath)
                modified = True
            
            if 'created' not in fm:
                fm['created'] = '2026-01-01'  # Default date
                modified = True
            
            if 'updated' not in fm:
                fm['updated'] = datetime.now().strftime('%Y-%m-%d')
                modified = True
            
            # Add SHA256 if missing
            if 'sha256' not in fm:
                fm['sha256'] = compute_sha256(filepath)
                stats['sha256_added'] += 1
                modified = True
            
            # Fix heading skips
            new_body = fix_heading_skips(body)
            if new_body != body:
                stats['headings_fixed'] += 1
                body = new_body
                modified = True
            
            if modified:
                stats['frontmatter_fixed'] += 1
                if DRY_RUN:
                    print(f'[DRY-RUN] Would fix: {filepath}')
                else:
                    new_content = write_frontmatter(fm, body)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f'Fixed: {filepath}')
    
    return stats

if __name__ == '__main__':
    print('Starting wiki fix...')
    stats = process_wiki()
    print(f'\nStats:')
    for k, v in stats.items():
        print(f'  {k}: {v}')
