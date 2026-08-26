#!/usr/bin/env python3
"""Clean up wiki files: merge multiple frontmatter blocks into one."""

import os
import re
import hashlib
from datetime import datetime

WIKI_DIR = '/workspace/llm-wiki/wiki'

def clean_frontmatter(content):
    """
    Clean up content with multiple frontmatter blocks.
    Strategy: find all --- blocks, merge their fields into one.
    """
    # Split by --- markers
    parts = content.split('---')
    
    # Find all frontmatter-like sections (between --- markers)
    fm_sections = []
    body_start_idx = None
    
    for i, part in enumerate(parts):
        stripped = part.strip()
        if not stripped:
            continue
        
        # Check if this looks like frontmatter (has key: value patterns)
        has_fm_pattern = bool(re.search(r'^[a-z_]+:', stripped, re.MULTILINE))
        
        if has_fm_pattern and body_start_idx is None:
            fm_sections.append(stripped)
        else:
            # This is the body
            if body_start_idx is None:
                body_start_idx = i
    
    if body_start_idx is None:
        body_start_idx = len(parts)
    
    if not fm_sections:
        return content
    
    # Merge all frontmatter sections
    merged_fm = {}
    for section in fm_sections:
        for line in section.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if ':' in line:
                key, _, value = line.partition(':')
                key = key.strip().lower()
                value = value.strip()
                # Only add if not already present (first occurrence wins)
                if key not in merged_fm:
                    # Handle inline lists
                    if value.startswith('[') and value.endswith(']'):
                        items = [i.strip().strip("'\"") for i in value[1:-1].split(',') if i.strip()]
                        merged_fm[key] = items
                    else:
                        merged_fm[key] = value
    
    # Build new content with single frontmatter
    fm_lines = []
    for key, value in merged_fm.items():
        if isinstance(value, list):
            items = ', '.join(f"'{i}'" for i in value)
            fm_lines.append(f'{key}: [{items}]')
        else:
            fm_lines.append(f'{key}: {value}')
    
    fm_text = '\n'.join(fm_lines)
    
    # Get body content (everything after last frontmatter section)
    body_parts = parts[body_start_idx:]
    body = '---'.join(body_parts)
    body = body.lstrip('\n')
    
    return '---\n' + fm_text + '\n---\n\n' + body

def process_wiki():
    """Process all wiki files."""
    stats = {
        'processed': 0,
        'cleaned': 0,
    }
    
    for root, dirs, files in os.walk(WIKI_DIR):
        for filename in files:
            if not filename.endswith('.md'):
                continue
            
            filepath = os.path.join(root, filename)
            stats['processed'] += 1
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if file has multiple --- blocks
            dash_count = content.count('---')
            if dash_count <= 2:
                continue  # Normal frontmatter
            
            new_content = clean_frontmatter(content)
            if new_content != content:
                stats['cleaned'] += 1
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f'Cleaned: {filepath}')
    
    return stats

if __name__ == '__main__':
    print('Cleaning wiki frontmatter...')
    stats = process_wiki()
    print(f'\nStats:')
    for k, v in stats.items():
        print(f'  {k}: {v}')
