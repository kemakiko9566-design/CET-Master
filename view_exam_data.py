import re, json

with open('exam_data.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract first entry's text field
# Find "text": "..." pattern
match = re.search(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', content, re.DOTALL)
if match:
    text = match.group(1)
    # Find Part II
    part2_start = text.find('Part II')
    part3_start = text.find('Part III', part2_start)
    if part2_start >= 0:
        section = text[part2_start:part3_start] if part3_start >= 0 else text[part2_start:]
        print("=== Part II (Listening Comprehension) ===")
        print(section[:3000])
        print("\n\n=== Total Part II length:", len(section), "===")
else:
    print("No text field found with regex")
    # Try to find any text content
    idx = content.find('Part II')
    if idx >= 0:
        print("Found 'Part II' at index", idx)
        print(content[max(0,idx-200):idx+500])
