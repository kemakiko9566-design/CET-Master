import json, os, re
from pypdf import PdfReader

base = r"D:\SynologyDrive\SynologyDrive\wzq\Language\CET\CET project\CET-4 真题"
output_path = r"D:\SynologyDrive\SynologyDrive\wzq\Language\CET\CET project\exam_data.js"

exams = []

for year_dir in sorted(os.listdir(base)):
    year_path = os.path.join(base, year_dir)
    if not os.path.isdir(year_path):
        continue
    year = year_dir.replace("cet4_", "")

    for fname in sorted(os.listdir(year_path)):
        if not fname.endswith(".pdf") or fname.endswith("_ans.pdf"):
            continue
        if fname.endswith("-3.pdf") or fname.endswith("_3.pdf"):
            # skip set 3 for now (only include set 1 and set 2)
            # actually let's include all
            pass

        fpath = os.path.join(year_path, fname)
        try:
            reader = PdfReader(fpath)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            text = text.strip()
            if not text:
                print(f"  [SKIP] {fname} - no text extracted")
                continue

            # Extract title from text
            title_match = re.search(r'(大学英语四级考试[^\(]*?（[^）]*?）)', text)
            if title_match:
                title = title_match.group(1).strip()
            else:
                # Generate a readable title from filename
                date_part = fname.replace("cet4_", "").replace(".pdf", "")
                parts = date_part.split("_")
                if len(parts) >= 2:
                    title = f"{parts[0]}年{parts[1]}月四级真题（第{parts[2]}套）" if len(parts) >= 3 else f"{parts[0]}年{parts[1]}月四级真题"
                else:
                    title = fname.replace(".pdf", "")

            # Extract KEYS if present
            keys_match = re.search(r'KEYS\s*\n([\s\S]*)', text)
            keys = keys_match.group(1).strip() if keys_match else ""

            # Strip KEYS from main text
            main_text = re.sub(r'\n\s*KEYS\s*\n[\s\S]*', '', text).strip()

            exams.append({
                "title": title,
                "year": year,
                "file": fname,
                "text": main_text,
                "keys": keys
            })
            print(f"  [OK] {fname} -> {title} ({len(main_text)} chars)")
        except Exception as e:
            print(f"  [ERR] {fname}: {e}")

# Write JS file
with open(output_path, "w", encoding="utf-8") as f:
    f.write("// Auto-generated exam data from batch_extract.py\n")
    f.write("const EXAM_DATA = ")
    json.dump(exams, f, ensure_ascii=False, indent=2)
    f.write(";\n")

print(f"\nTotal: {len(exams)} exams extracted -> {output_path}")
