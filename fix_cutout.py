c = open(r'D:\obsidian\note\lulu-note-publisher\build.py', 'r', encoding='utf-8').read()
c = c.replace("cutout: '75%'", "cutout: '40%'")
open(r'D:\obsidian\note\lulu-note-publisher\build.py', 'w', encoding='utf-8').write(c)
print('OK')
