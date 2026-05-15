import json

with open(r'D:\SynologyDrive\SynologyDrive\wzq\Language\CET\CET project\exam_data.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Parse JSON from var declaration
start = js.index('[')
end = js.rindex(']') + 1
data = json.loads(js[start:end])

e = data[0]
title = e["title"]
print("=== %s ===" % title)
print("Text start:")
print(e["text"][:600])
print("\n---")
print("Keys:", e["keys"][:300])
print("\nText length:", len(e["text"]))

# Test regex matching
import re
text = e["text"]
for r in [r'^Part\s+(I{1,3}|IV|V|VI?)\b']:
    matches = re.findall(r, text, re.MULTILINE)
    print("\nMatched Parts:", matches)
