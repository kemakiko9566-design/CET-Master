"""
End-to-end test for AudioAlignmentEngine.
Tests: CUDA detection, model loading, Whisper transcription fallback, alignment output.
"""
import sys, os, json, time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from agent_b_alignment import AudioAlignmentEngine, resolve_device

BASE_DIR = Path(__file__).parent
AUDIO_PATH = BASE_DIR / "data" / "audio" / "cet4_2019_06_1.mp3"
TEXT_PATH = BASE_DIR / "data" / "text" / "cet4_2019_06_1_cleaned.json"
OUTPUT_PATH = BASE_DIR / "dist" / "alignment"

print("=" * 60)
print("Stage 2 Alignment Engine — End-to-End Test")
print("=" * 60)

device = resolve_device()
print(f"Device: {device}")

if not AUDIO_PATH.exists():
    print(f"ERROR: Audio not found at {AUDIO_PATH}")
    sys.exit(1)
if not TEXT_PATH.exists():
    print(f"ERROR: Text not found at {TEXT_PATH}")
    sys.exit(1)

print(f"Audio: {AUDIO_PATH.name} ({AUDIO_PATH.stat().st_size / 1024 / 1024:.1f} MB)")
print(f"Text:  {TEXT_PATH.name}")

eng = AudioAlignmentEngine()
print(f"Engine device: {eng.device}, compute: {eng.compute_type}")

print("\nLoading text from cleaned JSON...")
sentences = eng.load_agent_a_text(str(TEXT_PATH))
print(f"  paragraphs found: {len(sentences)}")
if len(sentences) == 0:
    print("  (empty — will use Whisper transcription fallback)")

start = time.time()
result = eng.execute_and_export(
    paper_id="cet4_2019_06_1",
    audio_path=str(AUDIO_PATH),
    agent_a_json_path=str(TEXT_PATH),
    output_dir=str(OUTPUT_PATH),
)
elapsed = time.time() - start

print(f"\n{'=' * 60}")
print(f"Alignment complete in {elapsed:.1f}s")
print(f"{'=' * 60}")
print(f"Total segments: {result['total_segments']}")
print(f"\nFirst 5 segments:")
for s in result["sentences"][:5]:
    words_info = ""
    if s.get("words"):
        words_info = f" ({len(s['words'])} words, first={s['words'][0]['w']})"
    print(f"  [{s['start']:.1f}s - {s['end']:.1f}s] {s['text'][:80]}...{words_info}")

rest = len(result["sentences"]) - 5
if rest > 0:
    print(f"  ... ({rest} more segments)")

output_file = OUTPUT_PATH / "cet4_2019_06_1_aligned.json"
if output_file.exists():
    size_kb = output_file.stat().st_size / 1024
    print(f"\nOutput file: {output_file} ({size_kb:.1f} KB)")

print(f"\n{'=' * 60}")
print(f"Test Summary:")
print(f"  paragraphs_empty -> transcription_fallback: {'YES' if len(sentences) == 0 else 'NO'}")
print(f"  segments produced: {result['total_segments']}")
print(f"  word-level timestamps: {'YES' if any(s.get('words') for s in result['sentences']) else 'NO'}")
print(f"  CUDA used: {eng.device == 'cuda'}")
print(f"{'=' * 60}")
