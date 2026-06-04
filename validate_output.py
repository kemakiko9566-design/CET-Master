#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证所有生成的 JSON 文件的完整性。
"""

import json
import os
import glob

TEXT_DIR = r'D:\SynologyDrive\SynologyDrive\wzq\Language\CET\CET project\data\text'

PAPER_IDS = [
    'cet4_2019_06_1', 'cet4_2019_06_2',
    'cet4_2019_12_1', 'cet4_2019_12_2',
    'cet4_2021_06_1', 'cet4_2021_06_2',
    'cet4_2024_06_1', 'cet4_2024_06_2',
    'cet4_2024_12_1', 'cet4_2024_12_2',
    'cet4_2025_06_1', 'cet4_2025_06_2',
    'cet4_2025_12_1', 'cet4_2025_12_2',
]

types = ['reading', 'writing', 'translation']

all_ok = True

print("=" * 70)
print(f"{'FILE':40s} {'STATUS':10s} {'DETAILS':20s}")
print("=" * 70)

for pid in PAPER_IDS:
    for t in types:
        fpath = os.path.join(TEXT_DIR, f'{pid}_{t}.json')
        if not os.path.exists(fpath):
            print(f"{f'{pid}_{t}.json':40s} {'MISSING':10s}")
            all_ok = False
            continue
        
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate structure
            if t == 'reading':
                sections = data.get('sections', [])
                sec_names = [s.get('section_name') for s in sections]
                sec_a = any('Section A' in s.get('section_name', '') for s in sections)
                sec_b = any('Section B' in s.get('section_name', '') for s in sections)
                sec_c = any('Section C' in s.get('section_name', '') for s in sections)
                
                details = []
                if sec_a:
                    sa = next(s for s in sections if 'Section A' in s['section_name'])
                    wb = len(sa.get('word_bank', []))
                    details.append(f'A:{wb}w')
                if sec_b:
                    sb = next(s for s in sections if 'Section B' in s['section_name'])
                    paras = len(sb.get('paragraphs', []))
                    stmts = len(sb.get('statements', []))
                    details.append(f'B:{paras}p/{stmts}s')
                if sec_c:
                    sc = next(s for s in sections if 'Section C' in s['section_name'])
                    psgs = len(sc.get('passages', []))
                    details.append(f'C:{psgs}pass')
                
                detail_str = ', '.join(details)
                print(f"{f'{pid}_{t}.json':40s} {'OK':10s} {detail_str:20s}")
                
            elif t == 'writing':
                w = data.get('writing', {})
                directions = w.get('directions', '')
                detail = f'{len(directions)} chars'
                print(f"{f'{pid}_{t}.json':40s} {'OK':10s} {detail:20s}")
                
            elif t == 'translation':
                tr = data.get('translation', {})
                ch_text = tr.get('chinese_text', '')
                detail = f'{len(ch_text)} chars' if ch_text else 'EMPTY!'
                status = 'OK' if ch_text else 'WARN'
                if ch_text and len(ch_text) < 30:
                    status = 'SHORT'
                print(f"{f'{pid}_{t}.json':40s} {status:10s} {detail:20s}")
                if not ch_text:
                    all_ok = False
                    
        except json.JSONDecodeError as e:
            print(f"{f'{pid}_{t}.json':40s} {'INVALID JSON':10s} {str(e):20s}")
            all_ok = False
        except Exception as e:
            print(f"{f'{pid}_{t}.json':40s} {'ERROR':10s} {str(e):20s}")
            all_ok = False

print("=" * 70)
if all_ok:
    print("All files validated successfully!")
else:
    print("Some files have issues - see above.")

# 统计文件总数
total = sum(1 for f in os.listdir(TEXT_DIR) if f.endswith('.json'))
print(f"\nTotal JSON files in {TEXT_DIR}: {total}")
