import json, re

with open(r'D:\SynologyDrive\SynologyDrive\wzq\Language\CET\CET project\exam_data.js', 'r', encoding='utf-8') as f:
    js = f.read()

start = js.index('[')
end = js.rindex(']') + 1
data = json.loads(js[start:end])

# Check 2021_06_1 format
for idx, e in enumerate(data):
    fname = e['file'].replace('.pdf', '')
    if fname in ['cet4_2021_06_1', 'cet4_2021_06_2']:
        text = e['text']
        print(f"\n=== {fname} (first 500 chars) ===")
        print(repr(text[:500]))
        print(f"\n=== Searching for 'Part' markers ===")
        parts = re.findall(r'.{0,20}Part\s+\w.{0,20}', text)
        for p in parts:
            print(f"  Found: {repr(p)}")
        
        # Check for Writing
        has_writing = 'Writing' in text or 'Writing' in text
        has_reading = 'Reading' in text
        has_translation = 'Translation' in text or 'Translation' in text
        print(f"  Has Writing: {has_writing}")
        print(f"  Has Reading: {has_reading}")
        print(f"  Has Translation: {has_translation}")
        
        # Check for Part III
        p3 = re.search(r'Part\s+III', text)
        print(f"  Part III found: {p3 is not None}")
        if p3:
            print(f"  Part III context: {repr(text[p3.start():p3.start()+100])}")

# Check 2019_06_1 Section B format
print("\n\n=== Checking 2019_06_1 Section B ===")
e2019 = data[0]
text = e2019['text']
p3_start = text.find('Part III')
p4_start = text.find('Part IV', p3_start)
p3 = text[p3_start:p4_start]

sec_b = re.search(r'Section B\s*\n', p3)
sec_c = re.search(r'Section C\s*\n', p3)
if sec_b and sec_c:
    sec_b_text = p3[sec_b.end():sec_c.start()]
    print(f"Section B text (first 1000 chars):")
    print(repr(sec_b_text[:1000]))
    
    # Check for paragraph markers
    para_matches = re.findall(r'^[A-K]\)', sec_b_text, re.MULTILINE)
    print(f"\nParagraph markers found: {para_matches}")
