import json, re

with open(r'D:\SynologyDrive\SynologyDrive\wzq\Language\CET\CET project\exam_data.js', 'r', encoding='utf-8') as f:
    js = f.read()

start = js.index('[')
end = js.rindex(']') + 1
data = json.loads(js[start:end])

# Look at cet4_2024_06_1 (index 10) Part III in detail
e = data[10]  # cet4_2024_06_1
text = e["text"]

p3_start = text.find('Part III')
p4_start = text.find('Part IV', p3_start)
p3_text = text[p3_start:p4_start]

print("=== Full Part III of cet4_2024_06_1 ===")
print(p3_text)
