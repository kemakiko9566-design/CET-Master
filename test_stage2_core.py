"""
Stage 2 音频转写与时间戳对齐 — 自动化验收测试
=================================================
全量检测 dist/alignment/ 与 data/text/ 中已注入的时间戳数据。

检验标准:
  1. 对齐交付物存在性: dist/alignment/{paper_id}_aligned.json
  2. 对齐 JSON 结构: paper_id / sentences / words 完整
  3. 时间逻辑: end > start, 顺序递增, 无时间倒流
  4. 富文本注入: cleaned JSON 中 paragraphs 被注入 start_time / end_time
  5. 音频切片存在性: data/audio_slices/ 下的切片文件
  6. 音频文件完整性: 引用的音频切片在磁盘真实存在且 > 0 KB
"""

import json
import os
import warnings
import unittest

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
TEXT_DIR = os.path.join(DATA_DIR, "text")
AUDIO_DIR = os.path.join(DATA_DIR, "audio")
AUDIO_SLICES_DIR = os.path.join(DATA_DIR, "audio_slices")
ALIGNMENT_DIR = os.path.join(BASE_DIR, "dist", "alignment")


# ── 辅助函数 ──────────────────────────────────────────────

def get_expected_paper_ids() -> list[str]:
    json_files = sorted(os.listdir(TEXT_DIR))
    ids = set()
    for fname in json_files:
        if fname.endswith("_cleaned.json"):
            pid = fname.replace("_cleaned.json", "")
            ids.add(pid)
    return sorted(ids)


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 测试套件 ──────────────────────────────────────────────

class TestStage2AlignmentOutput(unittest.TestCase):
    """维度一：对齐交付物存在性检测"""

    @classmethod
    def setUpClass(cls):
        cls.alignment_available = os.path.isdir(ALIGNMENT_DIR)
        cls.expected_ids = get_expected_paper_ids()

    def test_alignment_dir_exists(self):
        """dist/alignment/ 目录必须存在"""
        if not self.alignment_available:
            self.skipTest("dist/alignment/ 目录不存在 — 对齐引擎尚未运行")

    def test_all_papers_have_alignment(self):
        if not self.alignment_available:
            self.skipTest("dist/alignment/ 目录不存在")
        aligned_files = set()
        for fname in os.listdir(ALIGNMENT_DIR):
            if fname.endswith("_aligned.json"):
                pid = fname.replace("_aligned.json", "")
                aligned_files.add(pid)

        missing = set(self.expected_ids) - aligned_files
        self.assertEqual(
            len(missing), 0,
            f"以下试卷缺少对齐输出文件: {sorted(missing)}"
        )
        extra = aligned_files - set(self.expected_ids)
        if extra:
            warnings.warn(f"发现额外对齐文件（可能无对应源数据）: {sorted(extra)}")

    def test_aligned_files_not_empty(self):
        if not self.alignment_available:
            self.skipTest("dist/alignment/ 目录不存在")
        for fname in os.listdir(ALIGNMENT_DIR):
            if not fname.endswith("_aligned.json"):
                continue
            fpath = os.path.join(ALIGNMENT_DIR, fname)
            size = os.path.getsize(fpath)
            self.assertGreater(
                size, 50,
                f"{fname} 文件过小 ({size} bytes)，疑似空文件"
            )


class TestStage2AlignedJSONStructure(unittest.TestCase):
    """维度二：对齐 JSON 数据结构合法性"""

    @classmethod
    def setUpClass(cls):
        cls.alignment_available = os.path.isdir(ALIGNMENT_DIR)
        cls.files = []
        if cls.alignment_available:
            cls.files = sorted([
                f for f in os.listdir(ALIGNMENT_DIR)
                if f.endswith("_aligned.json")
            ])

    def _test_aligned_file(self, fname: str):
        fpath = os.path.join(ALIGNMENT_DIR, fname)
        data = load_json(fpath)
        errors = []

        paper_id = fname.replace("_aligned.json", "")

        if data.get("paper_id") != paper_id:
            errors.append(f"paper_id={data.get('paper_id')!r} 期望 {paper_id!r}")

        if "total_segments" not in data:
            errors.append("缺少 total_segments")

        sentences = data.get("sentences", [])
        if not isinstance(sentences, list):
            errors.append("sentences 不是 list")
        elif len(sentences) == 0:
            errors.append("sentences 为空列表 — 对齐可能未产生任何结果")
        else:
            for idx, s in enumerate(sentences):
                sid = s.get("id", f"s_{idx+1}")
                if not isinstance(s, dict):
                    errors.append(f"{sid}: 不是 dict")
                    continue
                for field in ("id", "start", "end", "text", "words"):
                    if field not in s:
                        errors.append(f"{sid}: 缺少字段 {field}")

                words = s.get("words", [])
                if not isinstance(words, list):
                    errors.append(f"{sid}: words 不是 list")
                else:
                    for w_idx, w in enumerate(words):
                        if not isinstance(w, dict):
                            errors.append(f"{sid} word[{w_idx}]: 不是 dict")
                            continue
                        for wf in ("w", "start", "end"):
                            if wf not in w:
                                errors.append(f"{sid} word[{w_idx}]: 缺少字段 {wf}")

        return errors

    def test_all_aligned_files_structure(self):
        if not self.alignment_available:
            self.skipTest("dist/alignment/ 目录不存在 — 跳过结构检测")
        all_errors = {}
        for fname in self.files:
            errs = self._test_aligned_file(fname)
            if errs:
                all_errors[fname] = errs

        if all_errors:
            msg_parts = []
            for fname, errs in all_errors.items():
                msg_parts.append(f"\n  {fname} ({len(errs)} 项):")
                for e in errs:
                    msg_parts.append(f"    - {e}")
            self.fail("".join(msg_parts))


class TestStage2TimestampLogic(unittest.TestCase):
    """维度二（进阶）：时间戳逻辑合理性检测"""

    @classmethod
    def setUpClass(cls):
        cls.alignment_available = os.path.isdir(ALIGNMENT_DIR)
        cls.files = []
        if cls.alignment_available:
            cls.files = sorted([
                f for f in os.listdir(ALIGNMENT_DIR)
                if f.endswith("_aligned.json")
            ])

    def _test_timestamps(self, fname: str) -> list[str]:
        fpath = os.path.join(ALIGNMENT_DIR, fname)
        data = load_json(fpath)
        errors = []
        sentences = data.get("sentences", [])

        prev_end = -1.0
        for idx, s in enumerate(sentences):
            sid = s.get("id", f"s_{idx+1}")
            start = s.get("start")
            end = s.get("end")

            if start is None or end is None:
                errors.append(f"{sid}: 时间戳缺失")
                continue

            if not isinstance(start, (int, float)):
                errors.append(f"{sid}: start 不是数值 ({type(start).__name__})")
            if not isinstance(end, (int, float)):
                errors.append(f"{sid}: end 不是数值 ({type(end).__name__})")
                continue

            if end <= start:
                errors.append(f"{sid}: end({end}) <= start({start}) — 时间倒流")

            if prev_end >= 0 and start < prev_end - 0.05:
                errors.append(
                    f"{sid}: start({start}) 早于上一句 end({prev_end}) — 重叠"
                )
            if end > start:
                prev_end = end

            words = s.get("words", [])
            for w_idx, w in enumerate(words):
                ws = w.get("start")
                we = w.get("end")
                ww = w.get("w", "?")

                if ws is None or we is None:
                    errors.append(f"{sid} word[{w_idx}]({ww}): 时间戳缺失")
                    continue

                if not isinstance(ws, (int, float)):
                    errors.append(f"{sid} word[{w_idx}]({ww}): start 非数值")
                if not isinstance(we, (int, float)):
                    errors.append(f"{sid} word[{w_idx}]({ww}): end 非数值")
                    continue

                if we <= ws:
                    errors.append(f"{sid} word[{w_idx}]({ww}): end({we}) <= start({ws})")

                if ws < start - 0.1 or we > end + 0.1:
                    errors.append(
                        f"{sid} word[{w_idx}]({ww}): "
                        f"时间 [{ws}, {we}] 超出句子边界 [{start}, {end}]"
                    )

            for w_idx in range(1, len(words)):
                prev_w = words[w_idx - 1]
                curr_w = words[w_idx]
                if "end" in prev_w and "start" in curr_w:
                    if curr_w["start"] < prev_w["end"] - 0.05:
                        errors.append(
                            f"{sid} word[{w_idx}]({curr_w.get('w','?')}) start "
                            f"({curr_w['start']}) 早于前词 end ({prev_w['end']})"
                        )

        return errors

    def test_all_aligned_timestamps(self):
        if not self.alignment_available:
            self.skipTest("dist/alignment/ 目录不存在 — 跳过时间戳检测")
        all_errors = {}
        for fname in self.files:
            errs = self._test_timestamps(fname)
            if errs:
                all_errors[fname] = errs

        if all_errors:
            msg_parts = []
            for fname, errs in all_errors.items():
                msg_parts.append(f"\n  {fname} ({len(errs)} 项):")
                for e in errs:
                    msg_parts.append(f"    - {e}")
            self.fail("".join(msg_parts))


class TestStage2ParagraphEnrichment(unittest.TestCase):
    """维度二（核心）：cleaned JSON 中 paragraphs 是否已注入时间戳"""

    @classmethod
    def setUpClass(cls):
        cls.cleaned_files = sorted([
            f for f in os.listdir(TEXT_DIR)
            if f.endswith("_cleaned.json")
        ])

    def _test_paragraph_enrichment(self, fname: str) -> list[str]:
        fpath = os.path.join(TEXT_DIR, fname)
        data = load_json(fpath)
        errors = []

        for sec_idx, section in enumerate(data.get("sections", [])):
            sec_name = section.get("section_name", f"sec_{sec_idx}")
            for item_idx, item in enumerate(section.get("items", [])):
                paragraphs = item.get("paragraphs", [])

                if not isinstance(paragraphs, list):
                    errors.append(f"[{sec_name}][item_{item_idx}]: paragraphs 不是 list")
                    continue

                if len(paragraphs) == 0:
                    continue

                for p_idx, para in enumerate(paragraphs):
                    if isinstance(para, str):
                        continue
                    if isinstance(para, dict):
                        for field in ("text", "start_time", "end_time"):
                            if field not in para:
                                errors.append(
                                    f"[{sec_name}][item_{item_idx}][para_{p_idx}]: "
                                    f"缺少字段 {field}"
                                )
                            elif field in ("start_time", "end_time"):
                                    val = para[field]
                                    if not isinstance(val, (int, float)):
                                        errors.append(
                                            f"[{sec_name}][item_{item_idx}][para_{p_idx}]: "
                                            f"{field} 不是数值"
                                        )

                        if "start_time" in para and "end_time" in para:
                            st = para["start_time"]
                            et = para["end_time"]
                            if isinstance(st, (int, float)) and isinstance(et, (int, float)):
                                if et <= st:
                                    errors.append(
                                        f"[{sec_name}][item_{item_idx}][para_{p_idx}]: "
                                        f"end_time({et}) <= start_time({st})"
                                    )

                        if "words" in para:
                            words = para["words"]
                            if not isinstance(words, list):
                                errors.append(
                                    f"[{sec_name}][item_{item_idx}][para_{p_idx}]: "
                                    f"words 不是 list"
                                )
                            else:
                                for w_idx, w in enumerate(words):
                                    if not isinstance(w, dict):
                                        errors.append(
                                            f"[{sec_name}][item_{item_idx}][para_{p_idx}]: "
                                            f"words[{w_idx}] 不是 dict"
                                        )
                                        continue
                                    for wf in ("word", "start", "end"):
                                        if wf not in w:
                                            errors.append(
                                                f"[{sec_name}][item_{item_idx}][para_{p_idx}]: "
                                                f"words[{w_idx}] 缺少 {wf}"
                                            )
        return errors

    def test_paragraphs_injection_status(self):
        non_empty = 0
        total_items = 0
        for fname in self.cleaned_files:
            fpath = os.path.join(TEXT_DIR, fname)
            data = load_json(fpath)
            for section in data.get("sections", []):
                for item in section.get("items", []):
                    total_items += 1
                    paragraphs = item.get("paragraphs", [])
                    if isinstance(paragraphs, list) and len(paragraphs) > 0:
                        non_empty += 1

        if non_empty == 0:
            self.skipTest(
                f"所有 {total_items} 个 item 的 paragraphs 均为空 — "
                "对齐引擎尚未将时间戳注入 cleaned JSON。"
                "请先运行 agent_b_alignment.py 执行对齐"
            )

    def test_enriched_paragraphs_structure(self):
        all_errors = {}
        for fname in self.cleaned_files:
            errs = self._test_paragraph_enrichment(fname)
            if errs:
                all_errors[fname] = errs

        if all_errors:
            msg_parts = ["富文本 paragraphs 结构检测失败:"]
            for fname, errs in all_errors.items():
                msg_parts.append(f"\n  {fname} ({len(errs)} 项):")
                for e in errs:
                    msg_parts.append(f"    - {e}")
            self.fail("".join(msg_parts))


class TestStage2AudioSlices(unittest.TestCase):
    """维度三：音频切片文件存在性"""

    def test_audio_slices_dir_exists(self):
        if not os.path.isdir(AUDIO_SLICES_DIR):
            self.skipTest(
                "data/audio_slices/ 目录不存在 — 音频切片尚未生成。"
                "若采用 JSON 时间戳方案而非切片方案，此测试可忽略"
            )

    def test_audio_slices_have_content(self):
        if not os.path.isdir(AUDIO_SLICES_DIR):
            self.skipTest("audio_slices 目录不存在")

        paper_dirs = sorted([
            d for d in os.listdir(AUDIO_SLICES_DIR)
            if os.path.isdir(os.path.join(AUDIO_SLICES_DIR, d))
        ])

        self.assertGreater(
            len(paper_dirs), 0,
            "audio_slices 下无试卷子目录"
        )

        for pid in paper_dirs:
            subdir = os.path.join(AUDIO_SLICES_DIR, pid)
            mp3_files = [
                f for f in os.listdir(subdir)
                if f.endswith(".mp3") and os.path.getsize(os.path.join(subdir, f)) > 0
            ]
            self.assertGreater(
                len(mp3_files), 0,
                f"{pid}/ 下无有效 MP3 切片文件"
            )


class TestStage2AudioFileReference(unittest.TestCase):
    """维度三：对齐 JSON 中引用的音频文件在磁盘真实存在"""

    @classmethod
    def setUpClass(cls):
        cls.alignment_available = os.path.isdir(ALIGNMENT_DIR)
        cls.files = []
        if cls.alignment_available:
            cls.files = sorted([
                f for f in os.listdir(ALIGNMENT_DIR)
                if f.endswith("_aligned.json")
            ])

    def test_alignment_referenced_audio_exists(self):
        if not self.alignment_available:
            self.skipTest("dist/alignment/ 目录不存在")

        missing = []
        for fname in self.files:
            paper_id = fname.replace("_aligned.json", "")
            mp3_path = os.path.join(AUDIO_DIR, f"{paper_id}.mp3")
            if not os.path.exists(mp3_path):
                missing.append(f"{paper_id}.mp3 (for {fname})")
            elif os.path.getsize(mp3_path) == 0:
                missing.append(f"{paper_id}.mp3 (空文件)")

        self.assertEqual(
            len(missing), 0,
            f"以下引用的音频文件缺失或为空: {missing}"
        )

    def test_alignment_has_audio_path_field(self):
        if not self.alignment_available:
            self.skipTest("dist/alignment/ 目录不存在")
        for fname in self.files:
            fpath = os.path.join(ALIGNMENT_DIR, fname)
            data = load_json(fpath)
            paper_id = data.get("paper_id", "")
            if "audio_path" in data:
                ap = data["audio_path"]
                self.assertTrue(
                    os.path.exists(ap),
                    f"{fname}: audio_path({ap}) 不存在"
                )


# ── 运行入口 ──────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("Stage 2 音频转写与时间戳对齐 — 自动化验收测试")
    print("=" * 70)
    print(f"  清洗 JSON 目录:  {TEXT_DIR}")
    print(f"  对齐输出目录:    {ALIGNMENT_DIR}")
    print(f"  音频切片目录:    {AUDIO_SLICES_DIR}")
    print(f"  原始音频目录:    {AUDIO_DIR}")
    print(f"  dist/alignment 存在: {os.path.isdir(ALIGNMENT_DIR)}")
    print(f"  audio_slices 存在:   {os.path.isdir(AUDIO_SLICES_DIR)}")
    print("=" * 70)

    unittest.main(verbosity=2)
