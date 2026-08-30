import os
import re
import json
import shutil
import concurrent.futures
from pathlib import Path
from typing import Optional, Tuple

from pypdf import PdfReader
from agent_a_processor import ListeningProcessor


PDF_BASE = Path(__file__).parent / "CET-4 真题"
DATA_DIR = Path(__file__).parent / "data"
AUDIO_DIR = DATA_DIR / "audio"
RAW_DIR = DATA_DIR / "raw"
TEXT_DIR = DATA_DIR / "text"

processor = ListeningProcessor()


def extract_paper_id(filename: str) -> Optional[str]:
    name = filename.replace(".pdf", "").replace("_ans", "")
    match = re.match(r'(cet4_\d{4}_\d{2}_\d+)', name)
    if match:
        return match.group(1)
    return None


def extract_title(pdf_text: str, paper_id: str) -> str:
    title_match = re.search(
        r'(大学英语四级考试[^（]*?（[^）]*?）)',
        pdf_text
    )
    if title_match:
        title = title_match.group(1).strip()
        title = re.sub(r'\s+', '', title)
        return title

    parts = paper_id.split('_')
    year, month, num = parts[1], parts[2], parts[3]
    month_names = {'06': '6月', '09': '9月', '12': '12月', '03': '3月', '07': '7月'}
    month_str = month_names.get(month, f'{month}月')
    return f'{year}年{month_str}大学英语四级考试听力真题（第{num}套）'


def extract_listening_text(full_text: str) -> str:
    start = full_text.find('Part II')
    if start < 0:
        start = full_text.find('Listening Comprehension')
    if start < 0:
        return ""

    end = full_text.find('Part III', start)
    if end < 0:
        end = full_text.find('Part IV', start)
    if end < 0:
        end = full_text.find('Part V', start)
    if end < 0:
        end = full_text.find('Reading Comprehension', start + 50)

    listening_text = full_text[start:end] if end >= 0 else full_text[start:]
    return listening_text.strip()


def has_listening_content(text: str) -> bool:
    if not text:
        return False
    skip_patterns = [
        r'不再提供听力部分',
        r'本套试卷不再提供',
        r'本套真题听力与第\d+套内容完全一样',
        r'听力试题与第二套真题的一致',
    ]
    for pat in skip_patterns:
        if re.search(pat, text):
            return False
    return 'Section' in text and 'Questions' in text


def find_mp3_path(pdf_path: Path) -> Optional[Path]:
    mp3_path = pdf_path.with_suffix('.mp3')
    if mp3_path.exists():
        return mp3_path
    return None


def copy_audio(pdf_path: Path, paper_id: str) -> bool:
    mp3_src = find_mp3_path(pdf_path)
    if mp3_src is None:
        return False

    mp3_dst = AUDIO_DIR / f"{paper_id}.mp3"
    if mp3_dst.exists():
        return True
    try:
        shutil.copy2(str(mp3_src), str(mp3_dst))
        return True
    except Exception as e:
        print(f"    [AUDIO ERR] {paper_id}: {e}")
        return False


def process_single_exam(pdf_path: Path) -> Tuple[bool, str, str]:
    filename = pdf_path.name
    paper_id = extract_paper_id(filename)
    if paper_id is None:
        return False, filename, "无法提取 paper_id"

    try:
        reader = PdfReader(str(pdf_path))
        full_text = ""
        for page in reader.pages:
            pt = page.extract_text()
            if pt:
                full_text += pt + "\n"
        full_text = full_text.strip()
        if not full_text:
            return False, paper_id, "PDF 无文本内容"
    except Exception as e:
        return False, paper_id, f"PDF 读取失败: {e}"

    title = extract_title(full_text, paper_id)
    listening_text = extract_listening_text(full_text)

    if not has_listening_content(listening_text):
        return False, paper_id, "无听力内容（第三套重复或已标注）"

    raw_path = RAW_DIR / f"{paper_id}.txt"
    try:
        raw_path.write_text(listening_text, encoding='utf-8')
    except Exception as e:
        return False, paper_id, f"原始文本写入失败: {e}"

    audio_ok = copy_audio(pdf_path, paper_id)
    audio_status = "有音频" if audio_ok else "无音频"

    try:
        json_str = processor.process_pipeline(paper_id, title, listening_text)
        text_path = TEXT_DIR / f"{paper_id}_cleaned.json"
        text_path.write_text(json_str, encoding='utf-8')
    except Exception as e:
        return False, paper_id, f"JSON 处理失败: {e}"

    data = json.loads(json_str)
    q_count = sum(
        len(q)
        for sec in data.get('sections', [])
        for item in sec.get('items', [])
        for q in [item.get('questions', [])]
    )
    return True, paper_id, f"{audio_status} | {q_count} 题 | {title}"


def run_pipeline(max_workers: int = 4):
    pdf_files = sorted(PDF_BASE.rglob("*.pdf"))
    pdf_files = [f for f in pdf_files if not f.name.endswith("_ans.pdf")]

    total = len(pdf_files)
    print(f"=" * 60)
    print(f"CET-4 听力语料库管道 | 共发现 {total} 个 PDF 文件")
    print(f"  音频输出: {AUDIO_DIR}")
    print(f"  原始文本: {RAW_DIR}")
    print(f"  清洗 JSON: {TEXT_DIR}")
    print(f"  并发线程: {max_workers}")
    print(f"=" * 60)

    success_count = 0
    skip_count = 0
    error_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(process_single_exam, pdf): pdf for pdf in pdf_files}

        for i, future in enumerate(concurrent.futures.as_completed(future_map), 1):
            pdf = future_map[future]
            try:
                ok, paper_id, msg = future.result()
                if ok:
                    success_count += 1
                    status = "OK"
                elif "无听力" in msg:
                    skip_count += 1
                    status = "SKIP"
                else:
                    error_count += 1
                    status = "ERR"
                print(f"  [{status}] [{i:2d}/{total}] {paper_id}: {msg}")
            except Exception as e:
                error_count += 1
                print(f"  [ERR] [{i:2d}/{total}] {pdf.name}: {e}")

    print(f"=" * 60)
    print(f"管道完成: {success_count} 成功 / {skip_count} 跳过 / {error_count} 错误")
    print(f"=" * 60)
    return success_count, skip_count, error_count


if __name__ == "__main__":
    run_pipeline()
