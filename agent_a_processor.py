import re
import json
from typing import Dict, Any, List, Optional


class ListeningProcessor:
    """
    Agent A 核心引擎：负责英语四级听力文本的强力清洗与三级状态机切分
    """

    def __init__(self):
        self.sec_pattern = re.compile(r'^Section\s+([A-C])', re.IGNORECASE)
        self.item_pattern = re.compile(
            r'^(News Report\s+\d+|Conversation\s+\d+|Passage\s+\d+|Recording\s+\d+|Questions\s+\d+\s+(?:and|to)\s+\d+)',
            re.IGNORECASE
        )
        self.q_number_pattern = re.compile(r'^(\d+)\s*[\.\:]?\s*(.*)', re.DOTALL)
        self.single_opt_pattern = re.compile(r'([A-D])[\s-]*[\)\]7]\s*')
        self.direction_pattern = re.compile(r'^Directions?\s*:?', re.IGNORECASE)

    def clean_text(self, raw_text: str) -> str:
        """第一步：强力去噪与标准化"""
        text = raw_text
        # 1. 移除网页常见页眉页脚与广告噪声
        noise_patterns = [
            r'沪江网校', r'Page\s+\d+\s+of\s+\d+', r'微信公众号',
            r'版权所有', r'学习交流', r'书书书', r'[—\-]{3,}',
            r'特别说明[^。]*。', r'由于多题多卷[^。]*。',
            r'说明：[^。]*。', r'Part\s+\w+\s*\[?',
        ]
        for pat in noise_patterns:
            text = re.sub(pat, '', text)
        # 1b. 修复 OCR 选项标记脏数据: "A7 " → "A) "
        text = re.sub(r'(?<=[A-D])7(?=\s)', r')', text)
        # 2. 统一连续空白符（保留换行）
        text = re.sub(r'[ \t]+', ' ', text)
        # 2b. 修复题号前因 OCR 产生的连续短横线: "- - - - 24" → "24"
        text = re.sub(r'(?m)^[-\s]{2,}(\d+)', r'\1', text)
        # 3. 标准化 Section 锚点
        text = re.sub(r'^Section\s*([A-C])', r'Section \1', text, flags=re.IGNORECASE | re.MULTILINE)
        # 4. 去除孤立空行（保留结构所需）
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _extract_options_from_text(self, text_segment: str) -> Dict[str, str]:
        """从文本段中提取 A) B) C) D) 选项，返回 {letter: text} 字典"""
        parts = self.single_opt_pattern.split(text_segment)
        options = {}
        if len(parts) >= 3:
            for i in range(1, len(parts) - 1, 2):
                letter = parts[i]
                text = parts[i + 1].strip()
                # 去掉结尾的选项干扰
                text = re.sub(r'\s+[A-D][\)\]7]\s*$', '', text).strip()
                if letter in ['A', 'B', 'C', 'D']:
                    options[letter] = text
        return options

    def parse_to_json(self, paper_id: str, title: str, cleaned_text: str) -> Dict[str, Any]:
        """第二步：状态机三级切分，构建严格的树状 Dict"""
        result = {
            "paper_id": paper_id,
            "title": title,
            "sections": []
        }

        lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]
        current_section = None
        current_item = None
        in_questions_zone = False

        for raw_line in lines:
            line = raw_line

            # === 一级切分：Section 边界 ===
            sec_match = self.sec_pattern.match(line)
            if sec_match:
                current_section = {
                    "section_name": f"Section {sec_match.group(1).upper()}",
                    "items": []
                }
                result["sections"].append(current_section)
                current_item = None
                in_questions_zone = False
                continue

            if not current_section:
                continue

            # 跳过 Directions 行（单独成行时才跳过）
            if self.direction_pattern.match(line) and len(line) < 120:
                continue

            # === 检测 Item 边界（包括 Questions 行）===
            item_match = self.item_pattern.match(line)
            if item_match:
                current_item = {
                    "item_id": f"{paper_id}_{len(current_section['items']) + 1}",
                    "type": item_match.group(1).strip(),
                    "paragraphs": [],
                    "question_group_title": "",
                    "questions": []
                }
                current_section["items"].append(current_item)

                if "Questions" in line:
                    current_item["question_group_title"] = line
                    in_questions_zone = True
                else:
                    in_questions_zone = False
                continue

            if not current_item:
                continue

            # === 三级切分：Question 题干与选项 ===
            q_match = self.q_number_pattern.match(line)
            if q_match:
                q_num = int(q_match.group(1))
                rest_text = q_match.group(2).strip()

                options = self._extract_options_from_text(rest_text)
                q_text = self.single_opt_pattern.split(rest_text)[0].strip() if options else rest_text

                current_item["questions"].append({
                    "question_number": q_num,
                    "question_text": q_text,
                    "options": {}
                })

                if options:
                    current_item["questions"][-1]["options"] = options
                in_questions_zone = True
                continue

            # === 检测是否是无题号的选项延续行 ===
            if in_questions_zone and current_item["questions"]:
                opt_only = self._extract_options_from_text(line)
                if opt_only:
                    merged = dict(current_item["questions"][-1]["options"])
                    merged.update(opt_only)
                    current_item["questions"][-1]["options"] = merged
                    continue

                no_question_start = re.match(r'^[A-D]\s*[\)\]7-]', line)
                if no_question_start:
                    opt_only = self._extract_options_from_text(line)
                    if opt_only:
                        merged = dict(current_item["questions"][-1]["options"])
                        merged.update(opt_only)
                        current_item["questions"][-1]["options"] = merged
                        continue

                current_item["questions"][-1]["question_text"] += " " + line
                continue

            current_item["paragraphs"].append(line)

        return result

    def process_pipeline(self, paper_id: str, title: str, raw_text: str) -> str:
        """一键流式处理：清洗 + 切分 + 返回标准 JSON 字符串"""
        cleaned = self.clean_text(raw_text)
        data_dict = self.parse_to_json(paper_id, title, cleaned)
        return json.dumps(data_dict, ensure_ascii=False, indent=2)
