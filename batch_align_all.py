"""
Batch align all CET-4 papers that haven't been aligned yet.
"""
import sys, os, time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from agent_b_alignment import AudioAlignmentEngine, resolve_device

BASE_DIR = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "data" / "audio"
TEXT_DIR = BASE_DIR / "data" / "text"
ALIGNMENT_DIR = BASE_DIR / "dist" / "alignment"
ALIGNMENT_DIR.mkdir(parents=True, exist_ok=True)

device = resolve_device()
eng = AudioAlignmentEngine()
print(f"Device: {device}, Engine: {eng.device}")

existing = {f.stem.replace("_aligned", "") for f in ALIGNMENT_DIR.glob("*_aligned.json")}
mp3_files = sorted(AUDIO_DIR.glob("*.mp3"))

to_align = []
for mp3 in mp3_files:
    stem = mp3.stem
    text_path = TEXT_DIR / f"{stem}_cleaned.json"
    if stem in existing:
        print(f"  SKIP {stem} (already aligned)")
        continue
    if not text_path.exists():
        print(f"  SKIP {stem} (no cleaned JSON)")
        continue
    to_align.append(stem)

print(f"\nPapers to align: {len(to_align)}")
if not to_align:
    print("All done!")
    sys.exit(0)

for i, stem in enumerate(to_align, 1):
    mp3_path = AUDIO_DIR / f"{stem}.mp3"
    text_path = TEXT_DIR / f"{stem}_cleaned.json"
    print(f"\n[{i}/{len(to_align)}] Aligning {stem}...")
    start = time.time()
    try:
        result = eng.execute_and_export(
            paper_id=stem,
            audio_path=str(mp3_path),
            agent_a_json_path=str(text_path),
            output_dir=str(ALIGNMENT_DIR),
        )
        elapsed = time.time() - start
        print(f"  -> {result['total_segments']} segments in {elapsed:.0f}s")
    except Exception as e:
        print(f"  ERROR: {e}")

print(f"\n{'='*50}")
print("Batch alignment complete!")
print(f"{'='*50}")
