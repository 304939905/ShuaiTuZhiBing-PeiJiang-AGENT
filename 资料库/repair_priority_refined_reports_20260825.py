#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""仅修复 5×5 抽检中已由原帧和官方库定案的成品报告错误。

不处理截断、历史数值条件、姜维消歧等待办项；每份 DOCX 首次修改前
备份到资料库/audit_backups/20260825_priority_refined_reports/。
"""
from __future__ import annotations

import shutil
from pathlib import Path

from docx import Document

ROOT = Path(r"D:/Desktop/shandou")
REPORTS = ROOT / "报告库" / "旧56项目" / "精编"
BACKUP = ROOT / "资料库" / "audit_backups" / "20260825_priority_refined_reports"

FIXES = {
    "程昱魏智最强搭配—所有细节一篇看懂 魏智的宝物你真的带对了吗？_精修学习报告.docx": [
        ("荀彧（汉-步-5星）", "荀彧（魏-骑-5星）", 1),
    ],
    "全率土最细最强攻略合集 神赏体系粉丝投稿解析，来了_精修学习报告.docx": [
        ("荀彧（汉-步-5星）", "荀彧（魏-骑-5星）", 1),
    ],
    "率土武将志—贾诩 使用手册来了!一篇全看懂!_精修学习报告.docx": [
        ("荀彧（汉-步-5星）", "荀彧（魏-骑-5星）", 1),
    ],
    "低红大张鲁前期实战 ，队伍咋样，实战来看！_精修学习报告.docx": [
        ("张鲁（群-弓-4星）", "鲁肃（吴-步-5星）", 1),
        ("鲁肃0伤亡", "鲁肃剩余兵力7278、损失845", 1),
        ("兵力7278→845", "剩余兵力7278、损失845", 1),
    ],
}


def paragraphs(doc: Document):
    yield from doc.paragraphs
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                yield from cell.paragraphs


def replace_in_paragraph(paragraph, old: str, new: str) -> int:
    """优先保留原 run 样式；若文本跨 run，则只在该段落中做最小回退。"""
    count = 0
    for run in paragraph.runs:
        if old in run.text:
            count += run.text.count(old)
            run.text = run.text.replace(old, new)
    if count:
        return count
    if old not in paragraph.text:
        return 0
    # 目标文本跨 run 时，保留段落样式并将替换结果写入第一个 run。
    count = paragraph.text.count(old)
    text = paragraph.text.replace(old, new)
    if paragraph.runs:
        paragraph.runs[0].text = text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(text)
    return count


def main() -> None:
    BACKUP.mkdir(parents=True, exist_ok=True)
    for filename, fixes in FIXES.items():
        path = REPORTS / filename
        if not path.exists():
            raise FileNotFoundError(path)
        backup = BACKUP / filename
        if not backup.exists():
            shutil.copy2(path, backup)

        doc = Document(path)
        all_paras = list(paragraphs(doc))
        for old, new, expected in fixes:
            changed = sum(replace_in_paragraph(p, old, new) for p in all_paras)
            if changed != expected:
                raise RuntimeError(
                    f"{filename}: expected {expected} replacement(s) for {old!r}, got {changed}"
                )
        doc.save(path)
        print(f"OK {filename}")


if __name__ == "__main__":
    main()
