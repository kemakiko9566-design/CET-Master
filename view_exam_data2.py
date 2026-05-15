import re, json

with open('exam_data.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Find first text field
match = re.search(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', content, re.DOTALL)
if match:
    text = match.group(1)
    print(text[:300])  # Print beginning
    print("\n\n===========\n")
    
    # Show Part III
    part3 = text.find('Part III')
    if part3 >= 0:
        print(text[part3:part3+2000])
        print("\n\n===========\n")
    
    # Find question markers
    questions = re.findall(r'Questions (\d+) to (\d+)', text)
    print("Question ranges found:", questions)
    
    # Find individual question lines
    qlines = re.findall(r'^(\d+\.\s*[A-D].*)$', text, re.MULTILINE)
    print(f"\nTotal individual question options: {len(qlines)}")
    for q in qlines[:20]:
        print(q)
else:
    print("Could not find text field")
