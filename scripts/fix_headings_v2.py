#!/usr/bin/env python3
"""Fix remaining heading skips."""

import os

WIKI_DIR = '/workspace/llm-wiki/wiki'

def fix_headings_v2(content):
    """
    More aggressive heading fix:
    - Track actual previous heading level
    - Never allow skip > 1 level
    """
    lines = content.split('\n')
    fixed = []
    prev_level = 1
    
    for line in lines:
        if line.startswith('#'):
            orig_level = len(line) - len(line.lstrip('#'))
            # Cap level to prev + 1
            if orig_level > prev_level + 1:
                orig_level = prev_level + 1
            prev_level = orig_level
            line = '#' * orig_level + line[orig_level:]
        fixed.append(line)
    
    return '\n'.join(fixed)

def process_wiki():
    stats = {'processed': 0, 'fixed': 0}
    
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
            fixed_body = fix_headings_v2(body)
            
            if fixed_body != body:
                stats['fixed'] += 1
                new_content = content[:body_start] + fixed_body
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
    
    return stats

if __name__ == '__main__':
    print('Fixing remaining heading skips...')
    stats = process_wiki()
    print(f'Fixed: {stats["fixed"]}/{stats["processed"]}')
