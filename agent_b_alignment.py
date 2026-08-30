import os
import json
import torch
import requests
import logging
import warnings
from typing import Dict, Any, List, Optional
from pathlib import Path

from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, BackgroundTasks

import whisperx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("agent_b")


def resolve_device() -> str:
    if not torch.cuda.is_available():
        logger.info("[Device] CUDA not available — falling back to CPU")
        return "cpu"

    try:
        capability = torch.cuda.get_device_capability(0)
        gpu_name = torch.cuda.get_device_name(0)
        logger.info(f"[Device] GPU: {gpu_name}, capability: {capability}")

        return "cuda"
    except Exception as e:
        logger.warning(f"[Device] CUDA detection failed ({e}) — falling back to CPU")
        return "cpu"


class AudioAlignmentEngine:
    def __init__(self, device: str = None, batch_size: int = 8, compute_type: str = None):
        if device is None:
            self.device = resolve_device()
        else:
            self.device = device

        self.batch_size = batch_size

        if compute_type is None:
            self.compute_type = "int8" if self.device == "cpu" else "float16"
        else:
            self.compute_type = compute_type

        self.asr_model = None

        logger.info(f"[Engine] Initialized — device={self.device}, compute_type={self.compute_type}")

    def _ensure_align_model(self):
        if not hasattr(self, "_align_model"):
            logger.info(f"[Engine] Loading Wav2Vec2 alignment model on {self.device}...")
            self._align_model, self._metadata = whisperx.load_align_model(
                language_code="en",
                device=self.device,
            )
            logger.info("[Engine] Alignment model loaded")

    def _ensure_asr_model(self):
        if self.asr_model is None:
            logger.info(f"[Engine] Loading Whisper ASR model on {self.device}, compute={self.compute_type}...")
            self.asr_model = whisperx.load_model(
                "base",
                device=self.device,
                compute_type=self.compute_type,
            )
            logger.info("[Engine] Whisper ASR model loaded")

    def load_agent_a_text(self, json_path: str) -> List[str]:
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"Agent A text JSON not found: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sentences = []
        for section in data.get("sections", []):
            for item in section.get("items", []):
                for para in item.get("paragraphs", []):
                    cleaned = para.strip()
                    if cleaned:
                        sentences.append(cleaned)

        return sentences

    def _transcribe_audio(self, audio_path: str) -> List[Dict[str, Any]]:
        self._ensure_asr_model()
        audio = whisperx.load_audio(audio_path)
        logger.info(f"[Engine] Transcribing {audio_path} with Whisper...")
        result = self.asr_model.transcribe(audio, batch_size=self.batch_size)
        segments = result.get("segments", [])
        full_segments = [
            {"text": seg["text"].strip(), "start": seg.get("start", 0.0), "end": seg.get("end", 0.0)}
            for seg in segments if seg.get("text", "").strip()
        ]
        logger.info(f"[Engine] Transcription complete — {len(full_segments)} segments")
        return full_segments

    def align_pipeline(self, audio_path: str, text_sentences: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        self._ensure_align_model()
        audio = whisperx.load_audio(audio_path)

        if text_sentences and len(text_sentences) > 0:
            logger.info(f"[Engine] Using provided ground-truth text ({len(text_sentences)} sentences)")
            raw_text_segments = [{"text": s} for s in text_sentences]
        else:
            logger.info("[Engine] No ground-truth text — transcribing audio with Whisper first")
            raw_text_segments = self._transcribe_audio(audio_path)

        logger.info(f"[Engine] Running forced alignment on {len(raw_text_segments)} segments...")
        align_result = whisperx.align(
            raw_text_segments,
            self._align_model,
            self._metadata,
            audio,
            self.device,
            return_char_alignments=False,
            print_progress=True,
        )

        formatted_sentences = []
        for idx, seg in enumerate(align_result.get("segments", [])):
            sentence_text = seg.get("text", "").strip()
            sentence_start = seg.get("start", 0.0)
            sentence_end = seg.get("end", 0.0)

            if not sentence_text:
                continue

            sentence_data = {
                "id": f"s_{idx + 1}",
                "start": round(sentence_start, 2),
                "end": round(sentence_end, 2),
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

        return formatted_sentences

    def execute_and_export(
        self,
        paper_id: str,
        audio_path: str,
        agent_a_json_path: str,
        output_dir: str = "./dist/alignment",
    ) -> Dict[str, Any]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        sentences = self.load_agent_a_text(agent_a_json_path)

        if not sentences:
            logger.info(f"[Engine] paragraphs empty in {Path(agent_a_json_path).name} — will transcribe audio as fallback")

        aligned_data = self.align_pipeline(audio_path, sentences if sentences else None)

        final_payload = {
            "paper_id": paper_id,
            "total_segments": len(aligned_data),
            "sentences": aligned_data,
        }

        output_file = output_path / f"{paper_id}_aligned.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_payload, f, ensure_ascii=False, indent=2)

        logger.info(f"[Engine] Alignment complete — {len(aligned_data)} segments exported to {output_file}")
        return final_payload


app = FastAPI(
    title="CET-4 Audio Alignment API",
    description="Agent B — forced alignment microservice for CET-4 listening audio",
)

engine: Optional[AudioAlignmentEngine] = None


class AlignmentRequest(BaseModel):
    paper_id: str
    audio_path: str
    agent_a_json_path: str
    callback_url: Optional[str] = None


def get_engine() -> AudioAlignmentEngine:
    global engine
    if engine is None:
        engine = AudioAlignmentEngine()
    return engine


def background_alignment_task(payload: AlignmentRequest):
    try:
        eng = get_engine()
        logger.info(f"[Async Task] Processing paper_id={payload.paper_id}")

        result = eng.execute_and_export(
            paper_id=payload.paper_id,
            audio_path=payload.audio_path,
            agent_a_json_path=payload.agent_a_json_path,
        )

        if payload.callback_url:
            callback_data = {
                "status": "success",
                "paper_id": payload.paper_id,
                "total_segments": result.get("total_segments", 0),
                "output_json_path": str(
                    Path("./dist/alignment") / f"{payload.paper_id}_aligned.json"
                ),
            }
            logger.info(f"[Webhook] Posting success to {payload.callback_url}")
            try:
                requests.post(payload.callback_url, json=callback_data, timeout=10)
            except requests.RequestException as e:
                logger.error(f"[Webhook] POST failed: {e}")

    except Exception as e:
        logger.error(f"[Async Task] Failed for {payload.paper_id}: {e}", exc_info=True)
        if payload.callback_url:
            try:
                requests.post(
                    payload.callback_url,
                    json={
                        "status": "failed",
                        "paper_id": payload.paper_id,
                        "error": str(e),
                    },
                    timeout=10,
                )
            except requests.RequestException as cb_e:
                logger.error(f"[Webhook] Error callback failed: {cb_e}")


@app.post("/api/v1/start-alignment")
async def start_alignment(payload: AlignmentRequest, background_tasks: BackgroundTasks):
    if not os.path.exists(payload.audio_path):
        raise HTTPException(
            status_code=404,
            detail=f"Audio file not found: {payload.audio_path}",
        )
    if not os.path.exists(payload.agent_a_json_path):
        raise HTTPException(
            status_code=404,
            detail=f"Text JSON not found: {payload.agent_a_json_path}",
        )

    background_tasks.add_task(background_alignment_task, payload)

    return {
        "status": "queued",
        "message": f"Task for {payload.paper_id} accepted — processing in background",
        "paper_id": payload.paper_id,
    }


@app.get("/api/v1/health")
async def health_check():
    cuda_avail = torch.cuda.is_available()
    device = resolve_device()
    return {
        "status": "ok",
        "cuda_available": cuda_avail,
        "device": device,
        "engine_loaded": engine is not None,
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("AGENT_B_HOST", "0.0.0.0")
    port = int(os.getenv("AGENT_B_PORT", "8002"))

    logger.info(f"Starting Agent B alignment service on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
