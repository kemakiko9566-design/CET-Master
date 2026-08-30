import json, re, os

EXAM_DATA_PATH = r'D:\SynologyDrive\SynologyDrive\wzq\Language\CET\CET project\exam_data.js'

with open(EXAM_DATA_PATH, 'r', encoding='utf-8') as f:
    js_content = f.read()

start = js_content.index('[')
end = js_content.rindex(']') + 1
exam_data_list = json.loads(js_content[start:end])

# Test with cet4_2024_06_1
target_file = 'cet4_2024_06_1'
entry = None
for e in exam_data_list:
    if e['file'].replace('.pdf', '') == target_file:
        entry = e
        break

if entry:
    text = entry['text']
    
    # Test Part I Writing
    p1_match = re.search(r'Part\s+I\s+Writing', text)
    p2_match = re.search(r'Part\s+II\s+Listening', text)
    if p1_match and p2_match:
        p1_text = text[p1_match.start():p2_match.start()]
        print("=== Part I Writing ===")
        print(p1_text[:500])
        print("...")
    
    # Test Part III reading
    p3_match = re.search(r'Part\s+III\s+Reading', text)
    p4_match = re.search(r'Part\s+IV', text[p3_match.start():]) if p3_match else None
    if p3_match:
        p3_end = p3_match.start() + p4_match.start() if p4_match else len(text)
        p3_text = text[p3_match.start():p3_end]
        
        # Test Section A
        sec_a = re.search(r'Section A\s*\n', p3_text)
        sec_b = re.search(r'Section B\s*\n', p3_text)
        if sec_a and sec_b:
            sec_a_text = p3_text[sec_a.end():sec_b.start()]
            # Find word bank lines
            bank_lines = []
            for line in sec_a_text.split('\n'):
                if re.match(r'^[A-O]\)\s+\w', line.strip()):
                    bank_lines.append(line.strip())
            print(f"\n=== Section A Word Bank ({len(bank_lines)} words) ===")
            for bl in bank_lines:
                print(f"  {bl}")
        
        # Test Section B
        sec_c = re.search(r'Section C\s*\n', p3_text)
        if sec_b and sec_c:
            sec_b_text = p3_text[sec_b.end():sec_c.start()]
            # Count paragraphs (A), B), etc.)
            para_count = len(re.findall(r'^([A-K]\))\s+', sec_b_text, re.MULTILINE))
            stmt_count = len(re.findall(r'^(\d+)\.\s+', sec_b_text, re.MULTILINE))
            print(f"\n=== Section B: {para_count} paragraphs, {stmt_count} statements ===")
        
        # Test Section C
        if sec_c:
            sec_c_text = p3_text[sec_c.end():]
            passage_count = len(re.findall(r'Passage\s+(?:One|Two)', sec_c_text))
            print(f"\n=== Section C: {passage_count} passages ===")
    
    # Test Part IV Translation
    if p4_match:
        p4_start = p3_match.start() + p4_match.start()
        p4_text = text[p4_start:]
        dir_m = re.search(r'Directions:\s*(.*?)(?=\n\s*\n)', p4_text, re.DOTALL)
        if dir_m:
            after_dir = p4_text[dir_m.end():].strip()
            print(f"\n=== Part IV Translation ===")
            print(f"  Chinese text: {after_dir[:200]}...")
else:
    print(f"Entry {target_file} not found")
