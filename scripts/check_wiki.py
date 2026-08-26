#!/usr/bin/env python3
"""Check wiki health after fixes."""

import os
import re

WIKI_DIR = '/workspace/llm-wiki/wiki'

def check_wiki():
    stats = {
        'total_files': 0,
        'missing_slug': 0,
        'missing_created': 0,
        'missing_updated': 0,
        'missing_sha256': 0,
        'heading_skips': 0,
        'degenerate_files': 0,
    }
    
    for root, dirs, files in os.walk(WIKI_DIR):
        for filename in files:
            if not filename.endswith('.md'):
                continue
            
            # Check degenerate filenames
            if filename == '.md' or not filename.strip():
                stats['degenerate_files'] += 1
                continue
            
            filepath = os.path.join(root, filename)
            stats['total_files'] += 1
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check frontmatter
            if content.startswith('---'):
                end = content.find('---', 3)
                if end > 3:
                    fm_text = content[3:end]
                    fm = {}
                    for line in fm_text.split('\n'):
                        if ':' in line:
                            key, _, value = line.partition(':')
                            fm[key.strip().lower()] = value.strip()
                    
                    if 'slug' not in fm:
                        stats['missing_slug'] += 1
                    if 'created' not in fm:
                        stats['missing_created'] += 1
                    if 'updated' not in fm:
                        stats['missing_updated'] += 1
                    if 'sha256' not in fm:
                        stats['missing_sha256'] += 1
            
            # Check heading skips
            body_start = 0
            if content.startswith('---'):
                end = content.find('---', 3)
                if end > 3:
                    body_start = end + 4
            
            body = content[body_start:]
            lines = body.split('\n')
            prev_level = 1
            for line in lines:
                if line.startswith('#'):
                    level = len(line) - len(line.lstrip('#'))
                    if level > prev_level + 1:
                        stats['heading_skips'] += 1
                    prev_level = level
    
    return stats

if __name__ == '__main__':
    print('Checking wiki health...')
    stats = check_wiki()
    print('\nResults:')
    for k, v in stats.items():
        print(f'  {k}: {v}')
    
    if stats['missing_slug'] == 0 and stats['missing_created'] == 0 and stats['missing_updated'] == 0 and stats['missing_sha256'] == 0 and stats['degenerate_files'] == 0:
        print('\n✅ All critical issues resolved!')
    else:
        print('\n❌ Some issues remain.')
