import os
import json
import uuid
import asyncio
import threading
import logging
from pathlib import Path
from typing import Optional, AsyncGenerator
from datetime import timedelta

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from agent_b_alignment import AudioAlignmentEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("workbench")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
AUDIO_DIR = DATA_DIR / "audio"
TEXT_DIR = DATA_DIR / "text"
ALIGNMENT_DIR = BASE_DIR / "dist" / "alignment"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALIGNMENT_DIR.mkdir(parents=True, exist_ok=True)

task_statuses: dict[str, dict] = {}
task_events: dict[str, asyncio.Event] = {}

app = FastAPI(
    title="CET-4 Transcription Workbench",
    description="AI audio alignment & transcription workbench with Apple-minimalist UI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMPLATE_FILE = BASE_DIR / "templates" / "index.html"


@app.get("/", include_in_schema=False)
async def serve_workbench():
    if TEMPLATE_FILE.exists():
        html_content = TEMPLATE_FILE.read_text(encoding="utf-8")
        return HTMLResponse(content=html_content)
    return HTMLResponse(content="<h1>Transcription Workbench</h1><p>templates/index.html not found</p>")


def format_timestamp(seconds: float) -> str:
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_timestamp_short(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def generate_srt(aligned_data: dict) -> str:
    lines = []
    for idx, seg in enumerate(aligned_data.get("sentences", []), 1):
        start = format_timestamp(seg["start"])
        end = format_timestamp(seg["end"])
        text = seg["text"]
        lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)


def get_available_exams() -> list[dict]:
    exams = []
    if not AUDIO_DIR.exists():
        return exams

    mp3_files = set(f.stem for f in AUDIO_DIR.glob("*.mp3"))
    for stem in sorted(mp3_files):
        json_path = TEXT_DIR / f"{stem}_cleaned.json"
        mp3_path = AUDIO_DIR / f"{stem}.mp3"
        aligned_path = ALIGNMENT_DIR / f"{stem}_aligned.json"

        has_text = json_path.exists()
        has_alignment = aligned_path.exists()

        if has_text:
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                title = data.get("title", stem)
                sections = len(data.get("sections", []))
                items = sum(len(s.get("items", [])) for s in data.get("sections", []))
            except Exception:
                title = stem
                sections = 0
                items = 0
        else:
            title = stem
            sections = 0
            items = 0

        mp3_size = mp3_path.stat().st_size if mp3_path.exists() else 0

        exams.append({
            "paper_id": stem,
            "title": title,
            "has_text": has_text,
            "has_alignment": has_alignment,
            "audio_size_mb": round(mp3_size / (1024 * 1024), 1),
            "sections": sections,
            "items": items,
        })
    return exams


def update_task_status(task_id: str, status: str, progress: int, message: str, result: dict = None):
    if task_id in task_statuses:
        task_statuses[task_id].update({
            "status": status,
            "progress": progress,
            "message": message,
        })
        if result is not None:
            task_statuses[task_id]["result"] = result
        if status in ("completed", "failed"):
            if task_id in task_events:
                task_events[task_id].set()


def run_alignment_task(task_id: str, audio_path: str, text_path: str, paper_id: str):
    try:
        update_task_status(task_id, "processing", 5, "Initializing alignment engine...")
        engine = AudioAlignmentEngine()

        update_task_status(task_id, "processing", 15, f"Loading text from {Path(text_path).name}...")
        sentences = engine.load_agent_a_text(text_path)

        update_task_status(task_id, "processing", 25, f"Loading audio file ({round(os.path.getsize(audio_path)/(1024*1024),1)} MB)...")
        audio = whisperx_import().load_audio(audio_path)

        update_task_status(task_id, "processing", 35, "Loading alignment model...")
        align_model, metadata = engine.align_model, engine.metadata

        update_task_status(task_id, "processing", 45, f"Aligning {len(sentences)} sentences...")

        raw_text_segments = [{"text": s} for s in sentences]
        align_result = whisperx_import().align(
            raw_text_segments,
            align_model,
            metadata,
            audio,
            engine.device,
            return_char_alignments=False,
            print_progress=True,
        )

        update_task_status(task_id, "processing", 75, "Formatting alignment results...")

        formatted_sentences = []
        for idx, seg in enumerate(align_result.get("segments", [])):
            sentence_text = seg.get("text", "").strip()
            if not sentence_text:
                continue

            sentence_data = {
                "id": f"s_{idx + 1}",
                "start": round(seg.get("start", 0.0), 2),
                "end": round(seg.get("end", 0.0), 2),
                "text": sentence_text,
                "words": [],
            }

            for word in seg.get("words", []):
                if "start" in word and "end" in word:
                    sentence_data["words"].append({
                        "w": word.get("word", ""),
                        "start": round(word["start"], 2),
                        "end": round(word["end"], 2),
                    })

            if sentence_data["words"]:
                sentence_data["start"] = sentence_data["words"][0]["start"]
                sentence_data["end"] = sentence_data["words"][-1]["end"]

            formatted_sentences.append(sentence_data)

        update_task_status(task_id, "processing", 90, "Exporting results...")

        final_payload = {
            "paper_id": paper_id,
            "total_segments": len(formatted_sentences),
            "sentences": formatted_sentences,
        }

        output_file = ALIGNMENT_DIR / f"{paper_id}_aligned.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_payload, f, ensure_ascii=False, indent=2)

        update_task_status(
            task_id, "completed", 100, "Alignment complete!",
            result=final_payload,
        )

    except Exception as e:
        logger.error(f"Alignment task {task_id} failed: {e}", exc_info=True)
        update_task_status(task_id, "failed", 0, f"Error: {str(e)}")


def whisperx_import():
    import whisperx
    return whisperx


@app.get("/api/exams")
async def list_exams():
    return {"exams": get_available_exams()}


@app.post("/api/alignment/start")
async def start_alignment(
    paper_id: str = Form(...),
    audio_path: str = Form(None),
    text_path: str = Form(None),
):
    if audio_path and not os.path.exists(audio_path):
        audio_path = None
    if text_path and not os.path.exists(text_path):
        text_path = None

    if not audio_path:
        default_audio = AUDIO_DIR / f"{paper_id}.mp3"
        if default_audio.exists():
            audio_path = str(default_audio)
        else:
            raise HTTPException(404, f"Audio file not found for {paper_id}")

    if not text_path:
        default_text = TEXT_DIR / f"{paper_id}_cleaned.json"
        if default_text.exists():
            text_path = str(default_text)
        else:
            raise HTTPException(404, f"Text JSON not found for {paper_id}")

    task_id = str(uuid.uuid4())
    task_statuses[task_id] = {
        "task_id": task_id,
        "paper_id": paper_id,
        "status": "queued",
        "progress": 0,
        "message": "Task queued...",
    }
    task_events[task_id] = asyncio.Event()

    thread = threading.Thread(
        target=run_alignment_task,
        args=(task_id, audio_path, text_path, paper_id),
        daemon=True,
    )
    thread.start()

    return {
        "task_id": task_id,
        "paper_id": paper_id,
        "status": "queued",
    }


@app.get("/api/alignment/{task_id}/progress")
async def stream_progress(task_id: str):
    if task_id not in task_statuses:
        raise HTTPException(404, "Task not found")

    async def event_generator() -> AsyncGenerator[str, None]:
        while True:
            status = task_statuses.get(task_id, {})
            yield f"data: {json.dumps(status)}\n\n"

            if status.get("status") in ("completed", "failed"):
                break

            await asyncio.sleep(0.3)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/alignment/{task_id}/result")
async def get_result(task_id: str):
    if task_id not in task_statuses:
        raise HTTPException(404, "Task not found")

    status = task_statuses[task_id]
    if status["status"] == "completed" and "result" in status:
        return status["result"]
    elif status["status"] == "failed":
        raise HTTPException(500, status.get("message", "Unknown error"))
    else:
        raise HTTPException(202, {"status": status["status"], "progress": status["progress"]})


@app.get("/api/alignment/{task_id}/export")
async def export_alignment(task_id: str, format: str = Query("json")):
    if task_id not in task_statuses:
        raise HTTPException(404, "Task not found")

    status = task_statuses[task_id]
    if status["status"] != "completed" or "result" not in status:
        raise HTTPException(400, "Alignment not yet complete")

    result = status["result"]
    paper_id = result.get("paper_id", "output")

    if format == "srt":
        srt_content = generate_srt(result)
        return StreamingResponse(
            iter([srt_content]),
            media_type="text/plain",
            headers={
                "Content-Disposition": f'attachment; filename="{paper_id}.srt"',
            },
        )
    elif format == "json":
        return JSONResponse(
            content=result,
            headers={
                "Content-Disposition": f'attachment; filename="{paper_id}_aligned.json"',
            },
        )
    else:
        raise HTTPException(400, f"Unsupported format: {format}")


@app.get("/api/alignment/{task_id}/aligned-file")
async def get_aligned_file(task_id: str):
    if task_id not in task_statuses:
        raise HTTPException(404, "Task not found")

    status = task_statuses[task_id]
    if status["status"] != "completed":
        raise HTTPException(400, "Alignment not yet complete")

    paper_id = status.get("paper_id", status.get("result", {}).get("paper_id", "unknown"))
    aligned_path = ALIGNMENT_DIR / f"{paper_id}_aligned.json"

    if not aligned_path.exists():
        raise HTTPException(404, "Aligned file not found on disk")

    return FileResponse(
        str(aligned_path),
        media_type="application/json",
        filename=f"{paper_id}_aligned.json",
    )


@app.post("/api/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
    if not file.filename.endswith(".mp3"):
        raise HTTPException(400, "Only MP3 files are supported")

    file_path = UPLOAD_DIR / file.filename
    content = await file.read()
    file_path.write_bytes(content)

    return {
        "filename": file.filename,
        "path": str(file_path),
        "size_mb": round(len(content) / (1024 * 1024), 1),
    }


@app.post("/api/upload/text")
async def upload_text(file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        raise HTTPException(400, "Only JSON files are supported")

    file_path = UPLOAD_DIR / file.filename
    content = await file.read()

    try:
        data = json.loads(content)
        if "sections" not in data:
            raise HTTPException(400, "JSON must contain 'sections' field")
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON file")

    file_path.write_bytes(content)

    return {
        "filename": file.filename,
        "path": str(file_path),
        "size_kb": round(len(content) / 1024, 1),
    }


@app.get("/api/audio/{paper_id}/waveform")
async def get_waveform_data(paper_id: str):
    mp3_path = AUDIO_DIR / f"{paper_id}.mp3"
    if not mp3_path.exists():
        mp3_path = UPLOAD_DIR / f"{paper_id}.mp3"
    if not mp3_path.exists():
        raise HTTPException(404, "Audio file not found")

    import struct
    import subprocess
    import tempfile

    try:
        import numpy as np
    except ImportError:
        np = None

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name

    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(mp3_path),
             "-ac", "1", "-ar", "16000",
             "-f", "wav", wav_path],
            capture_output=True, timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr.decode(errors='replace')[:200]}")

        with open(wav_path, "rb") as f:
            raw_data = f.read()

        sample_rate = 16000
        data_start = raw_data.find(b"data") + 8
        samples = struct.unpack(f"<{len(raw_data[data_start:]) // 2}h",
                                raw_data[data_start:data_start + (len(raw_data[data_start:]) // 4) * 4])

        samples_per_pixel = max(1, len(samples) // 1000)
        waveform = []
        for i in range(0, len(samples), samples_per_pixel):
            chunk = samples[i:i + samples_per_pixel]
            if chunk:
                peak = max(abs(s) for s in chunk) / 32768.0
                waveform.append(round(peak, 4))

        duration = len(samples) / sample_rate

        return {
            "waveform": waveform,
            "duration": round(duration, 2),
            "sample_rate": sample_rate,
        }

    except FileNotFoundError:
        return {
            "waveform": [],
            "duration": 0,
            "sample_rate": 16000,
            "error": "ffmpeg not found — install ffmpeg or use client-side waveform",
        }
    except Exception as e:
        logger.warning(f"Waveform extraction failed: {e}")
        return {"waveform": [], "duration": 0, "error": str(e)}
    finally:
        try:
            os.unlink(wav_path)
        except Exception:
            pass


@app.get("/api/exams/{paper_id}/result")
async def get_exam_alignment_result(paper_id: str):
    aligned_path = ALIGNMENT_DIR / f"{paper_id}_aligned.json"
    if not aligned_path.exists():
        raise HTTPException(404, f"Alignment result not found for {paper_id}")

    with open(aligned_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


@app.get("/api/audio/{paper_id}/stream")
async def stream_audio(paper_id: str):
    mp3_path = AUDIO_DIR / f"{paper_id}.mp3"
    if not mp3_path.exists():
        mp3_path = UPLOAD_DIR / f"{paper_id}.mp3"
    if not mp3_path.exists():
        raise HTTPException(404, f"Audio file not found for {paper_id}")

    file_size = mp3_path.stat().st_size

    async def audio_iterator():
        with open(mp3_path, "rb") as f:
            chunk_size = 256 * 1024
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    return StreamingResponse(
        audio_iterator(),
        media_type="audio/mpeg",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Cache-Control": "no-cache",
        },
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting Transcription Workbench on http://localhost:{port}")
    logger.info(f"  Upload dir: {UPLOAD_DIR}")
    logger.info(f"  Audio dir:  {AUDIO_DIR}")
    logger.info(f"  Text dir:   {TEXT_DIR}")
    logger.info(f"  Output dir: {ALIGNMENT_DIR}")
    uvicorn.run(app, host="0.0.0.0", port=port)
