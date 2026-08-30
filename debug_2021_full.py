import json, re

with open(r'D:\SynologyDrive\SynologyDrive\wzq\Language\CET\CET project\exam_data.js', 'r', encoding='utf-8') as f:
    js = f.read()

start = js.index('[')
end = js.rindex(']') + 1
data = json.loads(js[start:end])

for e in data:
    fname = e['file'].replace('.pdf', '')
    if fname == 'cet4_2021_06_1':
        text = e['text']
        
        # Find the actual Section A (after the garbled Part ][)
        # The real section starts with "( 40 minutes)"
        sec_a_real = text.find('( 40 minutes)')
        if sec_a_real >= 0:
            print(f"Found '( 40 minutes)' at index {sec_a_real}")
            after = text[sec_a_real:sec_a_real+3000]
            
            # Find Section B
            sec_b = text.find('Section B', sec_a_real)
            if sec_b >= 0:
                sec_a_text = text[sec_a_real:sec_b]
                print(f"Section A text from '( 40 minutes)' to Section B ({len(sec_a_text)} chars):")
                print(repr(sec_a_text[:2000]))
                print(f"\n... (total {len(sec_a_text)} chars)")
                
                # Show word bank
                bank = text[sec_b-800:sec_b]
                print(f"\n\nLast 800 chars before Section B:")
                print(repr(bank))
        break

print("\n\n=== 2021_06_2 ===")
for e in data:
    fname = e['file'].replace('.pdf', '')
    if fname == 'cet4_2021_06_2':
        text = e['text']
        
        # Find the actual Section A
        sec_a_real = text.find('( 40 minutes)')
        if sec_a_real >= 0:
            print(f"Found '( 40 minutes)' at index {sec_a_real}")
            sec_b = text.find('Section B', sec_a_real)
            if sec_b >= 0:
                sec_a_text = text[sec_a_real:sec_b]
                print(f"Section A text from '( 40 minutes)' to Section B ({len(sec_a_text)} chars):")
                bank = text[sec_b-800:sec_b]
                print(f"\nWord bank (last 800 chars before Section B):")
                print(repr(bank))
        break
