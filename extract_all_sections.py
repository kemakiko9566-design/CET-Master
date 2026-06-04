#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从 exam_data.js 中提取 CET-4 考试的阅读、写作、翻译内容，
输出结构化 JSON 文件到 data/text/ 目录。

处理特殊情况：
- 2019年 Section B 段落标记为 [A] 格式
- 2021年 PDF提取乱码（Part III -> Part ][ / Part D[, Part IV -> Part N）
"""

import json
import re
import os

# ============ 配置 ============
EXAM_DATA_PATH = r'D:\SynologyDrive\SynologyDrive\wzq\Language\CET\CET project\exam_data.js'
OUTPUT_DIR = r'D:\SynologyDrive\SynologyDrive\wzq\Language\CET\CET project\data\text'

PAPER_IDS = [
    'cet4_2019_06_1', 'cet4_2019_06_2',
    'cet4_2019_12_1', 'cet4_2019_12_2',
    'cet4_2021_06_1', 'cet4_2021_06_2',
    'cet4_2024_06_1', 'cet4_2024_06_2',
    'cet4_2024_12_1', 'cet4_2024_12_2',
    'cet4_2025_06_1', 'cet4_2025_06_2',
    'cet4_2025_12_1', 'cet4_2025_12_2',
]

# ============ 加载数据 ============
with open(EXAM_DATA_PATH, 'r', encoding='utf-8') as f:
    js_content = f.read()

start = js_content.index('[')
end = js_content.rindex(']') + 1
exam_data_list = json.loads(js_content[start:end])

paper_id_to_entry = {}
for entry in exam_data_list:
    fname = entry.get('file', '').replace('.pdf', '')
    paper_id_to_entry[fname] = entry

# ============ 辅助函数 ============

def clean_text(text):
    if not text:
        return ''
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    return text.strip()


def parse_options_from_text(text, start_question_num, end_question_num):
    """
    从文本中解析选择题选项。
    返回 [{question_number, options: {A, B, C, D}}]
    """
    questions = []
    current_num = None
    current_options = {}
    lines = text.split('\n')

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # 检查是否以 "数字." 开头
        num_match = re.match(r'(\d+)\.\s*', stripped)
        if num_match:
            num = int(num_match.group(1))
            if start_question_num <= num <= end_question_num:
                if current_num is not None and current_options:
                    if start_question_num <= current_num <= end_question_num:
                        questions.append({
                            'question_number': current_num,
                            'options': dict(current_options)
                        })
                current_num = num
                current_options = {}
                rest = stripped[num_match.end():]
                opts = re.findall(r'([A-D]\))\s*([^\n]*?)(?=\s*(?:[A-D]\)|$))', rest)
                for opt_letter_full, opt_text in opts:
                    current_options[opt_letter_full[0]] = opt_text.strip()
        else:
            if current_num is not None:
                opts = re.findall(r'([A-D]\))\s*([^\n]*?)(?=\s*(?:[A-D]\)|$))', stripped)
                for opt_letter_full, opt_text in opts:
                    current_options[opt_letter_full[0]] = opt_text.strip()

    if current_num is not None and current_options:
        if start_question_num <= current_num <= end_question_num:
            questions.append({
                'question_number': current_num,
                'options': dict(current_options)
            })

    questions.sort(key=lambda x: x['question_number'])
    return questions


def find_part3_section(text):
    """
    查找 Part III (Reading Comprehension) 的起始位置。
    处理正常格式和2021年乱码格式。
    """
    # 正常格式
    patterns = [
        r'Part\s+III\s+Reading',
        r'Part\s+III\s*\n',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.start()
    
    # 2021年乱码格式: "Part ][ \nSection A \nReading Comprehension"
    m = re.search(r'Part\s+][^\n]*\n\s*Section\s+A\s*\n\s*Reading\s+Comprehension', text)
    if m:
        return m.start()
    
    # 2021年乱码格式: "Part D[ \nSection A \nReading Comprehension"
    m = re.search(r'Part\s+D\[[^\n]*\n\s*Section\s+A\s*\n\s*Reading\s+Comprehension', text)
    if m:
        return m.start()
    
    # 后备：直接找 Reading Comprehension，然后往前找 Section A
    rc = text.find('Reading Comprehension')
    if rc >= 0:
        before = text[max(0, rc-200):rc]
        # 找 Part 标记
        part_m = re.search(r'Part\s+\S+', before)
        if part_m:
            return max(0, rc - 200 + part_m.start())
    
    return None


def find_part4_section(text, p3_start):
    """
    查找 Part IV (Translation) 的起始位置。
    处理正常格式和2021年乱码格式。
    """
    search_from = p3_start if p3_start else 0
    
    # 正常格式
    patterns = [
        r'Part\s+IV\s+Translation',
        r'Part\s+IV\s',
    ]
    for pat in patterns:
        m = re.search(pat, text[search_from:])
        if m:
            return search_from + m.start()
    
    # 2021年乱码: "Part N Translation"
    m = re.search(r'Part\s+N\s+Translation', text[search_from:])
    if m:
        return search_from + m.start()
    
    return None


def extract_section_a(text):
    """提取 Section A（选词填空）"""
    sec_a_match = re.search(r'Section\s+A\s*\n', text)
    if not sec_a_match:
        return None
    
    sec_a_start = sec_a_match.end()
    sec_b_match = re.search(r'Section\s+B\s*\n', text)
    sec_a_end = sec_b_match.start() if sec_b_match else len(text)
    
    sec_a_text = text[sec_a_start:sec_a_end]
    lines = sec_a_text.split('\n')
    
    passage_lines = []
    bank_lines = []
    in_bank = False
    
    # 跳过Directions部分（从Section A到第一个非Direction行且有内容的行）
    start_collecting = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # 单词银行行: "A) word I) word" 或 "A) word"
        if re.match(r'^[A-O]\)\s+\w', stripped):
            in_bank = True
            bank_lines.append(stripped)
        elif not in_bank:
            # 跳过Directions和Question标记部分
            if not start_collecting:
                # 如果行包含 Direction/In this section/You are/Questions，跳过
                if any(x in line for x in ['Directions:', 'In this section', 'You are required', 'You may not', 'You should']):
                    continue
                if re.match(r'Questions\s+\d+', stripped):
                    continue
                # 首次遇到非Direction且有内容/字母的行，开始收集
                if len(stripped) > 20 or re.match(r'[A-Z]', stripped):
                    start_collecting = True
                    passage_lines.append(line)
            else:
                passage_lines.append(line)
    
    passage_text = clean_text('\n'.join(passage_lines))
    
    # 解析 Word Bank（两列或单列）
    word_bank = {}
    for wl in bank_lines:
        words = re.findall(r'([A-O]\))\s+(\w+(?:\s+\w+)*?)(?=\s*(?:[A-O]\)|$))', wl)
        if not words:
            words = re.findall(r'([A-O]\))\s+(\w+(?:\s+\w+)*)', wl)
        for l, w in words:
            word_bank[l[0]] = w.strip()
    
    sorted_bank = [{'letter': k, 'word': word_bank[k]} for k in sorted(word_bank.keys())]
    
    questions = [{'question_number': i, 'blank_context': ''} for i in range(26, 36)]
    
    return {
        'passage': passage_text,
        'word_bank': sorted_bank,
        'questions': questions
    }


def extract_section_b(text):
    """
    提取 Section B（长篇阅读匹配）
    段落标记支持 [A] 和 A) 两种格式
    """
    sec_b_match = re.search(r'Section\s+B\s*\n', text)
    if not sec_b_match:
        return None
    
    sec_b_start = sec_b_match.end()
    sec_c_match = re.search(r'Section\s+C\s*\n', text)
    sec_b_end = sec_c_match.start() if sec_c_match else len(text)
    
    sec_b_text = text[sec_b_start:sec_b_end]
    lines = sec_b_text.split('\n')
    
    paragraphs = []
    current_letter = None
    current_text = []
    in_statements = False
    statements = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_letter and current_text:
                paragraphs.append({
                    'letter': current_letter,
                    'text': clean_text(' '.join(current_text))
                })
                current_letter = None
                current_text = []
            continue
        
        # 跳过Directions行
        if 'Directions:' in stripped or 'In this section' in stripped:
            continue
        
        # 段落标记: [A] text 或 A) text
        bracket_match = re.match(r'^\[([A-K])\]\s*(.*)', stripped)
        paren_match = re.match(r'^([A-K])\)\s+(.*)', stripped)
        
        if bracket_match and not in_statements:
            if current_letter and current_text:
                paragraphs.append({
                    'letter': current_letter,
                    'text': clean_text(' '.join(current_text))
                })
            current_letter = bracket_match.group(1)
            current_text = [bracket_match.group(2)]
            continue
        elif paren_match and not in_statements:
            if current_letter and current_text:
                paragraphs.append({
                    'letter': current_letter,
                    'text': clean_text(' '.join(current_text))
                })
            current_letter = paren_match.group(1)
            current_text = [paren_match.group(2)]
            continue
        
        # 语句行（36-45题）
        stmt_match = re.match(r'^(\d+)\.\s*(.*)', stripped)
        if stmt_match:
            num = int(stmt_match.group(1))
            if 36 <= num <= 45:
                in_statements = True
                if current_letter and current_text:
                    paragraphs.append({
                        'letter': current_letter,
                        'text': clean_text(' '.join(current_text))
                    })
                    current_letter = None
                    current_text = []
                statements.append({
                    'number': num,
                    'text': stmt_match.group(2).strip()
                })
                continue
        
        if in_statements:
            continue
        
        if current_letter:
            current_text.append(stripped)
    
    if current_letter and current_text:
        paragraphs.append({
            'letter': current_letter,
            'text': clean_text(' '.join(current_text))
        })
    
    questions = parse_options_from_text(sec_b_text, 36, 45)
    
    return {
        'paragraphs': paragraphs,
        'statements': statements,
        'questions': questions
    }


def extract_section_c(text):
    """提取 Section C（仔细阅读）"""
    sec_c_match = re.search(r'Section\s+C\s*\n', text)
    if not sec_c_match:
        return None
    
    sec_c_start = sec_c_match.end()
    
    # 找 Section C 的结束（Part IV 或文件结尾）
    p4_match = re.search(r'(?:Part\s+(?:IV|N)\s|KEYS)', text[sec_c_start:])
    sec_c_end = sec_c_start + p4_match.start() if p4_match else len(text)
    
    sec_c_text = text[sec_c_start:sec_c_end]
    
    passages = []
    passage_splits = re.split(r'(Passage\s+(?:One|Two))', sec_c_text)
    
    current_passage = None
    current_text_lines = []
    
    for part in passage_splits:
        if 'Passage ' in part and ('One' in part or 'Two' in part):
            if current_passage is not None:
                pfull = clean_text('\n'.join(current_text_lines))
                q_start = 46 if current_passage == 1 else 51
                q_end = 50 if current_passage == 1 else 55
                questions = parse_options_from_text(pfull, q_start, q_end)
                passages.append({
                    'passage_number': current_passage,
                    'passage_text': pfull,
                    'questions': questions
                })
            current_passage = 1 if 'One' in part else 2
            current_text_lines = []
        elif current_passage is not None:
            current_text_lines.append(part)
    
    if current_passage is not None and current_text_lines:
        pfull = clean_text('\n'.join(current_text_lines))
        q_start = 46 if current_passage == 1 else 51
        q_end = 50 if current_passage == 1 else 55
        questions = parse_options_from_text(pfull, q_start, q_end)
        passages.append({
            'passage_number': current_passage,
            'passage_text': pfull,
            'questions': questions
        })
    
    return passages if passages else None


def extract_writing(text):
    """提取 Part I Writing"""
    # 找 Part I Writing (包括2021年 "Part I • Writing")
    p1_match = re.search(r'Part\s+I\s+[•\s]*Writing', text)
    if not p1_match:
        p1_match = re.search(r'^Part\s+I\s+Writing', text, re.MULTILINE)
    if not p1_match:
        return None
    
    p1_start = p1_match.start()
    
    # 找 Part II 作为结束
    p2_patterns = [
        r'Part\s+II\s+Listening',
        r'Part\s+Il\s+Listening',
        r'Part\s+]I\s+Listening',
    ]
    p1_end = len(text)
    for pat in p2_patterns:
        m = re.search(pat, text)
        if m:
            p1_end = m.start()
            break
    
    p1_text = text[p1_start:p1_end]
    
    dir_match = re.search(r'Directions:\s*(.*?)(?=\n\s*\n|Part\s+II|\Z)', p1_text, re.DOTALL)
    if dir_match:
        directions = re.sub(r'\s+', ' ', dir_match.group(1).strip())
    else:
        directions = clean_text(p1_text)
    
    return {'directions': directions, 'topic': ''}


def extract_translation(text):
    """提取 Part IV Translation"""
    patterns = [
        r'Part\s+IV\s+Translation',
        r'Part\s+N\s+Translation',  # 2021年乱码
    ]
    
    p4_match = None
    for pat in patterns:
        p4_match = re.search(pat, text)
        if p4_match:
            break
    
    if not p4_match:
        return None
    
    p4_start = p4_match.start()
    p4_text = text[p4_start:]
    
    # 找到 Directions: 的位置
    dir_start = p4_text.find('Directions:')
    if dir_start < 0:
        dir_start = p4_text.find('Direction')
    if dir_start < 0:
        dir_start = 0
    
    # 从 Directions: 之后找到第一个中文字符作为中文文本的开始
    text_after_dir = p4_text[dir_start:]
    
    # 找到第一个中文字符
    chinese_start = None
    for i, c in enumerate(text_after_dir):
        if '\u4e00' <= c <= '\u9fff':
            chinese_start = i
            break
    
    if chinese_start is None:
        return {'directions': '', 'chinese_text': ''}
    
    # Directions 是从 dir_start 到第一个中文字符之前的内容
    raw_directions = text_after_dir[:chinese_start].strip()
    # 移除 "Directions:" 前缀
    raw_directions = re.sub(r'^Directions?\s*:\s*', '', raw_directions, flags=re.IGNORECASE)
    directions = re.sub(r'\s+', ' ', raw_directions).strip()
    
    # 中文文本是从第一个中文字符到末尾（或到非中文标记之前）
    raw_chinese = text_after_dir[chinese_start:]
    
    # 找到最后一个中文字符/中文标点作为结束
    chinese_end = len(raw_chinese)
    for i in range(len(raw_chinese) - 1, -1, -1):
        c = raw_chinese[i]
        if '\u4e00' <= c <= '\u9fff' or c in '。，、；：？！""''（）【】《》':
            chinese_end = i + 1
            break
    
    chinese_text = raw_chinese[:chinese_end].strip()
    chinese_text = re.sub(r'\s+', ' ', chinese_text)
    
    return {'directions': directions, 'chinese_text': chinese_text}


def extract_reading(text):
    """提取完整的 Part III Reading Comprehension"""
    p3_start = find_part3_section(text)
    if p3_start is None:
        return None
    
    # 找 Part IV 作为结束
    p4_start = find_part4_section(text, p3_start)
    
    if p4_start:
        p3_end = p4_start
    else:
        # 可能没有 Part IV，找文件结尾或 KEYS
        keys_m = re.search(r'KEYS|\Z', text[p3_start:])
        p3_end = p3_start + keys_m.start() if keys_m else len(text)
    
    p3_text = text[p3_start:p3_end]
    
    result = {'paper_id': '', 'title': '', 'sections': []}
    
    sec_a = extract_section_a(p3_text)
    if sec_a:
        result['sections'].append({
            'section_name': 'Section A',
            'type': 'Banked Cloze',
            **sec_a
        })
    
    sec_b = extract_section_b(p3_text)
    if sec_b:
        result['sections'].append({
            'section_name': 'Section B',
            'type': 'Long Reading Matching',
            **sec_b
        })
    
    sec_c = extract_section_c(p3_text)
    if sec_c:
        result['sections'].append({
            'section_name': 'Section C',
            'type': 'Careful Reading',
            'passages': sec_c
        })
    
    return result


# ============ 主处理流程 ============

def process_paper_id(paper_id):
    """处理单个 paper_id"""
    if paper_id not in paper_id_to_entry:
        print(f'  [ERROR] {paper_id} not found in exam_data.js')
        return
    
    entry = paper_id_to_entry[paper_id]
    text = entry['text']
    title = entry.get('title', '')
    
    print(f'\n=== Processing {paper_id}: {title} ===')
    
    # 1. 提取写作
    print('  Extracting Writing...')
    writing_data = extract_writing(text)
    if writing_data:
        writing_output = {
            'paper_id': paper_id,
            'title': title,
            'writing': writing_data
        }
        writing_path = os.path.join(OUTPUT_DIR, f'{paper_id}_writing.json')
        with open(writing_path, 'w', encoding='utf-8') as f:
            json.dump(writing_output, f, ensure_ascii=False, indent=2)
        print(f'    -> Saved {writing_path}')
        print(f'      Directions: {writing_data["directions"][:80]}...')
    else:
        print('    [WARN] No Writing section found')
    
    # 2. 提取阅读
    print('  Extracting Reading...')
    reading_data = extract_reading(text)
    if reading_data:
        reading_data['paper_id'] = paper_id
        reading_data['title'] = title
        reading_path = os.path.join(OUTPUT_DIR, f'{paper_id}_reading.json')
        with open(reading_path, 'w', encoding='utf-8') as f:
            json.dump(reading_data, f, ensure_ascii=False, indent=2)
        print(f'    -> Saved {reading_path}')
        for sec in reading_data['sections']:
            if sec['section_name'] == 'Section A':
                print(f'      Section A: passage={len(sec["passage"])} chars, word_bank={len(sec["word_bank"])} words')
            elif sec['section_name'] == 'Section B':
                print(f'      Section B: {len(sec["paragraphs"])} paragraphs, {len(sec["statements"])} statements')
            elif sec['section_name'] == 'Section C':
                print(f'      Section C: {len(sec["passages"])} passages')
    else:
        print('    [WARN] No Reading section found')
    
    # 3. 提取翻译
    print('  Extracting Translation...')
    translation_data = extract_translation(text)
    if translation_data:
        translation_output = {
            'paper_id': paper_id,
            'title': title,
            'translation': translation_data
        }
        translation_path = os.path.join(OUTPUT_DIR, f'{paper_id}_translation.json')
        with open(translation_path, 'w', encoding='utf-8') as f:
            json.dump(translation_output, f, ensure_ascii=False, indent=2)
        print(f'    -> Saved {translation_path}')
        print(f'      Translation: {len(translation_data["chinese_text"])} chars')
    else:
        print('    [WARN] No Translation section found')


# ============ 执行 ============
if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for paper_id in PAPER_IDS:
        process_paper_id(paper_id)
    
    print('\n=== All done! ===')
