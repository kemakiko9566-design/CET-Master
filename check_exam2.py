import json, re

with open(r'D:\SynologyDrive\SynologyDrive\wzq\Language\CET\CET project\exam_data.js', 'r', encoding='utf-8') as f:
    js = f.read()

start = js.index('[')
end = js.rindex(']') + 1
data = json.loads(js[start:end])

# Check multiple entries for all parts
for idx in [0, 1, 3, 4, 10, 12, 14, 16, 18, 20]:
    e = data[idx]
    fname = e["file"].replace(".pdf", "")
    text = e["text"]
    
    parts = re.findall(r'^Part\s+(I{1,3}|IV|V|VI?)\b', text, re.MULTILINE)
    has_translation = 'Part IV' in text
    
    # Find Part III start
    p3 = text.find('Part III')
    p4 = text.find('Part IV')
    
    print(f"\n=== {fname} ===")
    print(f"  Parts found: {parts}")
    print(f"  Has Part IV (Translation): {has_translation}")
    print(f"  Text length: {len(text)}")
    
    if p3 >= 0:
        p3_end = text.find('Part IV', p3) if p4 >= 0 else len(text)
        p3_text = text[p3:p3_end]
        # Check for Section A/B/C
        sec_a = 'Section A' in p3_text
        sec_b = 'Section B' in p3_text
        sec_c = 'Section C' in p3_text
        print(f"  Part III sections: A={sec_a}, B={sec_b}, C={sec_c}")
        print(f"  Part III text length: {len(p3_text)}")
        # Show last 200 chars of Part III
        print(f"  Part III ends with: ...{p3_text[-200:]}")
    
    if p4 >= 0:
        p4_text = text[p4:]
        print(f"  Part IV text: {p4_text[:300]}...")
