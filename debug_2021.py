import json, re

with open(r'D:\SynologyDrive\SynologyDrive\wzq\Language\CET\CET project\exam_data.js', 'r', encoding='utf-8') as f:
    js = f.read()

start = js.index('[')
end = js.rindex(']') + 1
data = json.loads(js[start:end])

# Check 2021_06_1 - find Reading and Translation parts
for fname in ['cet4_2021_06_1', 'cet4_2021_06_2']:
    for e in data:
        if e['file'].replace('.pdf', '') == fname:
            text = e['text']
            print(f"\n=== {fname} ===")
            
            # Find Reading section
            reading_idx = text.find('Reading Comprehension')
            if reading_idx >= 0:
                print(f"Reading Comprehension at index {reading_idx}")
                print(f"Context: {repr(text[max(0,reading_idx-30):reading_idx+50])}")
                
                # Find what's before Reading
                before = text[max(0,reading_idx-200):reading_idx]
                print(f"Before Reading: {repr(before[-100:])}")
                
                # Is there a Part III?
                p3 = re.search(r'Part\s*(?:III|I{3}|l{3}|1{3})', text[max(0,reading_idx-200):reading_idx])
                print(f"Part III before Reading: {p3 is not None}")
            
            # Find Translation
            trans_idx = text.find('Translation')
            if trans_idx >= 0:
                print(f"\nTranslation at index {trans_idx}")
                print(f"Context: {repr(text[max(0,trans_idx-30):trans_idx+50])}")
            
            # Show Part markers with more flexibility
            print("\nSearching for Part markers (flexible):")
            # Find any "Part" occurrences
            for m in re.finditer(r'.{0,10}Part.{0,30}', text):
                print(f"  [{m.start()}] {repr(m.group())}")
            
            # Check if "Part III Reading" appears in any form
            # Look for "III" or "lll" near "Reading"
            near_reading = text[max(0,reading_idx-300):reading_idx+100] if reading_idx >= 0 else ""
            roman_near_reading = re.findall(r'(?:Part\s*)?(?:III|II I|I II|I I I|lll|III)\s*(?:Reading|Listening)', near_reading)
            print(f"\nRoman numerals near Reading: {roman_near_reading}")
            
            # Show all text from a point after Part II
            # Try to find Part II Listening or Part Il Listening
            p2_match = re.search(r'Part\s+(?:II|Il|]I|II)\s+Listening', text)
            if p2_match:
                after_p2 = text[p2_match.end():]
                # Show the next 2000 chars
                # Find "Section" markers
                sections = re.findall(r'(?:Section\s+[ABC]|Part\s)', after_p2[:3000])
                print(f"\nAfter Part II listening: sections found = {sections}")
                
                # Look for part III
                # Maybe it says "Part III Reading Comprehension"
                p3_alt = re.search(r'Part\s+\S+\s+Reading', text[p2_match.start():])
                if p3_alt:
                    print(f"Alternative Part III: {repr(p3_alt.group())} at {p3_alt.start()}")
            break
