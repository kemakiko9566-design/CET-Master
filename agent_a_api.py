import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from agent_a_processor import ListeningProcessor

DATA_DIR = Path(__file__).parent / "data"
AUDIO_DIR = DATA_DIR / "audio"
TEXT_DIR = DATA_DIR / "text"

processor = ListeningProcessor()

app = FastAPI(
    title="CET-4 Audio Corpus Cleaning API",
    description="四级听力语料库强力清洗与结构化 API — Agent A 核心服务",
    version="1.0.0",
)


class CleanRequest(BaseModel):
    paper_id: str
    title: str
    raw_text: str


class ProcessResponse(BaseModel):
    status: str
    data: Dict[str, Any]


class ExamSummary(BaseModel):
    paper_id: str
    title: str
    sections: int
    items: int
    questions: int
    has_audio: bool


class ErrorResponse(BaseModel):
    status: str
    detail: str


@app.get("/")
async def root():
    return {
        "service": "CET-4 Listening Corpus API",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/v1/process-listening": "处理原始听力文本并返回结构化 JSON",
            "GET /api/v1/list-exams": "列出所有已处理试卷",
            "GET /api/v1/exam/{paper_id}": "获取指定试卷的清洗后数据",
            "GET /api/v1/audio/{paper_id}": "获取指定试卷的音频路径信息",
            "GET /health": "健康检查",
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "agent-a-processor"}


@app.post("/api/v1/process-listening", response_model=ProcessResponse)
async def process_listening(payload: CleanRequest):
    """供 Agent B / Agent C 直接拉取结构化数据的标准微服务接口"""
    try:
        cleaned_text = processor.clean_text(payload.raw_text)
        structured_data = processor.parse_to_json(
            payload.paper_id, payload.title, cleaned_text
        )
        return {
            "status": "success",
            "data": structured_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parser Error: {str(e)}")


@app.get("/api/v1/list-exams", response_model=List[ExamSummary])
async def list_exams():
    """列出所有已处理的试卷"""
    json_files = sorted(TEXT_DIR.glob("*_cleaned.json"))
    if not json_files:
        return []

    result = []
    for f in json_files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            paper_id = data["paper_id"]
            secs = len(data.get("sections", []))
            items = sum(len(s.get("items", [])) for s in data.get("sections", []))
            qs = sum(
                len(q)
                for s in data.get("sections", [])
                for i in s.get("items", [])
                for q in [i.get("questions", [])]
            )
            has_audio = (AUDIO_DIR / f"{paper_id}.mp3").exists()
            result.append(ExamSummary(
                paper_id=paper_id,
                title=data.get("title", ""),
                sections=secs,
                items=items,
                questions=qs,
                has_audio=has_audio,
            ))
        except Exception:
            continue

    return result


@app.get("/api/v1/exam/{paper_id}", response_model=ProcessResponse)
async def get_exam(paper_id: str):
    """获取指定试卷的清洗后结构化数据"""
    json_path = TEXT_DIR / f"{paper_id}_cleaned.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail=f"试卷 {paper_id} 不存在")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取失败: {str(e)}")


@app.get("/api/v1/audio/{paper_id}")
async def get_audio_info(paper_id: str):
    """获取指定试卷的音频文件信息"""
    mp3_path = AUDIO_DIR / f"{paper_id}.mp3"
    if not mp3_path.exists():
        raise HTTPException(status_code=404, detail=f"音频文件 {paper_id}.mp3 不存在")

    try:
        file_size = mp3_path.stat().st_size
        return {
            "status": "success",
            "data": {
                "paper_id": paper_id,
                "file_name": f"{paper_id}.mp3",
                "file_path": str(mp3_path.absolute()),
                "file_size_bytes": file_size,
                "file_size_kb": round(file_size / 1024, 1),
                "file_size_mb": round(file_size / (1024 * 1024), 1),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("=" * 60)
    print("CET-4 Agent A API Server")
    print("=" * 60)
    print("可用端点:")
    print("  POST /api/v1/process-listening  处理原始听力文本")
    print("  GET  /api/v1/list-exams         列出所有已处理试卷")
    print("  GET  /api/v1/exam/{paper_id}    获取指定试卷数据")
    print("  GET  /api/v1/audio/{paper_id}   获取音频信息")
    print("  GET  /health                    健康检查")
    print("=" * 60)
    print("启动服务: http://0.0.0.0:8001")
    print("API 文档: http://0.0.0.0:8001/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8001)
