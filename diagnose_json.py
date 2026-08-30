"""Diagnose the structure of a cleaned JSON file to understand where text lives."""
import json
import sys
from pathlib import Path

TEXT_DIR = Path(__file__).parent / "data" / "text"

def diagnose(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"File: {Path(filepath).name}")
    print(f"  paper_id: {data.get('paper_id', 'N/A')}")
    print(f"  title: {data.get('title', 'N/A')[:60]}")

    print(f"\n  Top-level keys: {list(data.keys())}")
    for k, v in data.items():
        if isinstance(v, list):
            print(f"    {k}: list[{len(v)}]")
        elif isinstance(v, dict):
            print(f"    {k}: dict({list(v.keys())})")
        elif isinstance(v, str):
            print(f"    {k}: str({len(v)} chars) = {v[:80]}")
        else:
            print(f"    {k}: {type(v).__name__} = {v}")

    sections = data.get("sections", [])
    print(f"\n  sections[{len(sections)}]:")
    for sec_idx, sec in enumerate(sections):
        sec_name = sec.get("section_name", f"sec_{sec_idx}")
        items = sec.get("items", [])
        print(f"\n  [{sec_name}] items[{len(items)}]:")
        for item_idx, item in enumerate(items):
            item_id = item.get("item_id", f"item_{item_idx}")
            item_type = item.get("type", "")
            paras = item.get("paragraphs", [])
            questions = item.get("questions", [])
            print(f"    [{item_id}] type={item_type}")
            print(f"      paragraphs[{len(paras)}]: {paras[:2]}")
            print(f"      questions[{len(questions)}]:")
            for q in questions:
                qn = q.get("question_number", "?")
                qt = q.get("question_text", "")
                opts = q.get("options", {})
                print(f"        Q{qn}: text=[{qt[:40]}] options={list(opts.keys())}")
                for ok, ov in opts.items():
                    print(f"          {ok}) {ov[:60]}")

if __name__ == "__main__":
    files = sorted(TEXT_DIR.glob("*_cleaned.json"))
    if not files:
        print("No cleaned JSON files found!")
        sys.exit(1)
    diagnose(str(files[0]))
