#!/usr/bin/env python3
"""Fix heading level skips in wiki files."""

import os
import re

WIKI_DIR = '/workspace/llm-wiki/wiki'

def fix_headings(content):
    """
    Fix heading level skips.
    Rules:
    - First H1 stays H1
    - Subsequent H1 become H2 (they're section headers, not document titles)
    - If level > prev_level + 1, bump to prev_level + 1
    """
    lines = content.split('\n')
    fixed = []
    prev_level = 1
    first_h1 = True
    
    for line in lines:
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            
            # After first H1, all H1 become H2
            if level == 1 and not first_h1:
                level = 2
            
            if level > prev_level + 1:
                level = prev_level + 1
            
            if level == 1:
                first_h1 = False
            
            prev_level = level
            line = '#' * level + line[level:]
        
        fixed.append(line)
    
    return '\n'.join(fixed)

def process_wiki():
    """Process all wiki files."""
    stats = {
        'processed': 0,
        'fixed': 0,
    }
    
    for root, dirs, files in os.walk(WIKI_DIR):
        for filename in files:
            if not filename.endswith('.md'):
                continue
            
            filepath = os.path.join(root, filename)
            stats['processed'] += 1
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip frontmatter
            body_start = 0
            if content.startswith('---'):
                end = content.find('---', 3)
                if end > 3:
                    body_start = end + 4
            
            body = content[body_start:]
            fixed_body = fix_headings(body)
            
            if fixed_body != body:
                stats['fixed'] += 1
                new_content = content[:body_start] + fixed_body
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f'Fixed: {filepath}')
    
    return stats

if __name__ == '__main__':
    print('Fixing heading levels...')
    stats = process_wiki()
    print(f'\nStats:')
    for k, v in stats.items():
        print(f'  {k}: {v}')
