"""
Stage 1 数据底座自动化测试
=============================
全量 14 套 JSON 试卷的一键批量巡检。
检验标准：
  1. 根级字段 paper_id / title / sections 存在性
  2. sections -> items -> questions 完整遍历，每卷精确 25 题
  3. options 字典键值合法性 (A/B/C/D, 非空字符串)
  4. 禁词检测：Page X / 扫码听音频 等
  5. 接口占位检查：每个 item 必须有 paragraphs(list)
"""

import json
import os
import re
import unittest
import traceback

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "text")

# ── 禁词正则 ──────────────────────────────────────────────
FORBIDDEN_PATTERNS = [
    re.compile(r"(?i)Page\s+\d+"),
    re.compile(r"扫码听音频"),
    re.compile(r"扫码.*音频"),
]


def check_forbidden(text: str) -> list[str]:
    matched = []
    for pat in FORBIDDEN_PATTERNS:
        if pat.search(text):
            matched.append(pat.pattern)
    return matched


class TestStage1Core(unittest.TestCase):
    """Stage 1 数据底座 —— 全卷批量体检"""

    # ── 类级容器：聚合所有失败记录 ─────────────────────────
    failed_list: list[dict] = []

    @classmethod
    def setUpClass(cls):
        cls.failed_list = []

    @classmethod
    def tearDownClass(cls):
        if cls.failed_list:
            print("\n" + "=" * 70)
            print("FAILED 汇总")
            print("=" * 70)
            for rec in cls.failed_list:
                print(f"  [{rec['file']}] 题号 {rec['question']}: {rec['reason']}")
            print("=" * 70)
            raise AssertionError(
                f"共 {len(cls.failed_list)} 项检测未通过，详情见上方 FAILED 汇总。"
            )
        else:
            print("\n🚀 STAGE 1 FOUNDATION LOCKED")

    # ── 动态生成单卷测试用例 ──────────────────────────────
    @staticmethod
    def _build_test(paper_path: str, filename: str):
        def test(self):
            paper_id_for_log = filename.replace("_cleaned.json", "")
            errors: list[str] = []

            def push(msg: str):
                errors.append(msg)

            try:
                with open(paper_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                self.__class__.failed_list.append(
                    {"file": filename, "question": "N/A", "reason": f"JSON 解析失败: {e}"}
                )
                self.fail(f"JSON 解析失败: {e}")

            # ── 1. 根级断言 ──────────────────────────────
            for field in ("paper_id", "title", "sections"):
                if field not in data:
                    push(f"缺少根字段: {field}")

            if errors:
                for e in errors:
                    self.__class__.failed_list.append(
                        {"file": filename, "question": "ROOT", "reason": e}
                    )
                self.fail("; ".join(errors))

            # ── 2. 全量遍历 ──────────────────────────────
            total_q = 0
            sections = data.get("sections", [])

            if not isinstance(sections, list):
                self.__class__.failed_list.append(
                    {"file": filename, "question": "ROOT", "reason": "sections 不是 list"}
                )
                self.fail("sections 不是 list")

            for sec_idx, section in enumerate(sections):
                section_name = section.get("section_name", f"index_{sec_idx}")
                items = section.get("items", [])

                if not isinstance(items, list):
                    msg = f"[{section_name}] items 不是 list"
                    push(msg)
                    continue

                for item_idx, item in enumerate(items):
                    # ── 2a. 接口占位：paragraphs ────────
                    if "paragraphs" not in item:
                        push(f"[{section_name}][item_{item_idx}] 缺少 paragraphs 字段")
                    elif not isinstance(item["paragraphs"], list):
                        push(f"[{section_name}][item_{item_idx}] paragraphs 不是 list")

                    questions = item.get("questions", [])
                    if not isinstance(questions, list):
                        push(f"[{section_name}][item_{item_idx}] questions 不是 list")
                        continue

                    for q_idx, q in enumerate(questions):
                        total_q += 1
                        q_num = q.get("question_number", f"{section_name}_q{q_idx}")

                        # ── 3. options 合法性 ──────────
                        options = q.get("options")
                        if not isinstance(options, dict):
                            push(f"[{section_name}][Q{q_num}] options 缺失或非 dict")
                            continue

                        for opt_key, opt_val in options.items():
                            if opt_key not in ("A", "B", "C", "D"):
                                push(
                                    f"[{section_name}][Q{q_num}] 非法选项键: {opt_key!r}"
                                )
                            if not isinstance(opt_val, str):
                                push(
                                    f"[{section_name}][Q{q_num}] 选项 {opt_key} 不是 str"
                                )
                            elif len(opt_val.strip()) == 0:
                                push(
                                    f"[{section_name}][Q{q_num}] 选项 {opt_key} 为空字符串"
                                )

                            # ── 4. 禁词检测 ──────────
                            if isinstance(opt_val, str):
                                forbidden = check_forbidden(opt_val)
                                if forbidden:
                                    push(
                                        f"[{section_name}][Q{q_num}] 选项 {opt_key} 含禁词 {forbidden}: {opt_val!r}"
                                    )

            # ── 5. 数量断言 ──────────────────────────────
            if total_q != 25:
                push(f"全卷题数={total_q}，期望 25")

            # ── 上报本卷所有错误 ─────────────────────────
            if errors:
                for e in errors:
                    # 尝试从错误消息中提取题号
                    q_match = re.search(r"\[Q?(\d+|[A-Za-z0-9_]+)\]", e)
                    q_tag = q_match.group(1) if q_match else "GENERAL"
                    self.__class__.failed_list.append(
                        {"file": filename, "question": q_tag, "reason": e}
                    )
                self.fail(f"{filename}: {'; '.join(errors)}")

        return test

    # ── 动态注册测试方法 ──────────────────────────────────


def _generate_tests():
    if not os.path.isdir(DATA_DIR):
        print(f"[WARN] data/text/ 目录不存在 ({DATA_DIR})")
        return

    for fname in sorted(os.listdir(DATA_DIR)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(DATA_DIR, fname)
        if not os.path.isfile(fpath):
            continue

        test_name = f"test_{fname.removesuffix('.json').replace('-', '_').replace('.', '_')}"
        test_method = TestStage1Core._build_test(fpath, fname)
        setattr(TestStage1Core, test_name, test_method)
        print(f"  [已注册] {fname}")


_generate_tests()


if __name__ == "__main__":
    unittest.main(verbosity=2)
