"""Quick validation: check listening word-level features are present."""
import urllib.request

r = urllib.request.urlopen("http://localhost:8080/")
html = r.read().decode()

checks = {
    "CSS .listen-word": ".listen-word" in html,
    "CSS .listen-word.active": ".listen-word.active" in html,
    "CSS .listen-sentence-wrap": ".listen-sentence-wrap" in html,
    "JS listenActiveWordIdx": "listenActiveWordIdx" in html,
    "JS render word spans": 'data-start="' in html and 'data-end="' in html,
    "JS classList.add(active)": "classList.add('active')" in html,
    "JS onListenTimeUpdate word loop": "words[w].start" in html,
    "Speed 0.75x": "0.75x" in html,
    "Speed 1.5x": "1.5x" in html,
}

all_pass = True
for name, ok in checks.items():
    status = "PASS" if ok else "FAIL"
    if not ok:
        all_pass = False
    print(f"  [{status}] {name}")

print(f"\nAll checks passed: {all_pass}")
print(f"HTML size: {len(html)} bytes")
