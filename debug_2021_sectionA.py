import json, re

with open(r'D:\SynologyDrive\SynologyDrive\wzq\Language\CET\CET project\exam_data.js', 'r', encoding='utf-8') as f:
    js = f.read()

start = js.index('[')
end = js.rindex(']') + 1
data = json.loads(js[start:end])

# Look at 2021_06_1 Part III Section A text
for e in data:
    fname = e['file'].replace('.pdf', '')
    if fname == 'cet4_2021_06_1':
        text = e['text']
        
        # Find part 3 using the garbled format
        m = re.search(r'Part\s+][^\n]*\n\s*Section\s+A\s*\n', text)
        if m:
            print(f"Found Part ][ at index {m.start()}")
            after = text[m.start():m.start()+2000]
            print("Text after Part ][:")
            print(repr(after[:1500]))
            
            # Find Section A and Section B
            sec_a = re.search(r'Section\s+A\s*\n', after)
            sec_b = re.search(r'Section\s+B\s*\n', after)
            if sec_a and sec_b:
                sec_a_text = after[sec_a.end():sec_b.start()]
                print(f"\n\nSection A text ({len(sec_a_text)} chars):")
                print(repr(sec_a_text[:500]))
                
                # Check for word bank
                bank_lines = []
                for line in sec_a_text.split('\n'):
                    if re.match(r'^\s*[A-O]\)', line.strip()):
                        bank_lines.append(line.strip())
                print(f"\nWord bank lines: {bank_lines}")
        break
