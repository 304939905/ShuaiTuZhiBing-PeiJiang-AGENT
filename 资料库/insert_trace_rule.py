#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量在 71 份精编溯源索引节插入溯源规则说明(紧跟索引标题后)。"""
import sys
from pathlib import Path
import docx

ROOT = Path("D:/Desktop/shandou/报告库")
APPLY = "--apply" in sys.argv
RULE = "溯源规则：时间锚存在 ±4 秒判读容差；若某时间段首帧画面与描述不符，请核验相邻 ±2~4 秒帧，取画面匹配者。"

done = 0
already = 0
for sub in ["旧56项目", "开荒", "海之呼唤", "赛季"]:
    d = ROOT / sub / "精编"
    if not d.exists():
        continue
    for f in sorted(d.glob("*.docx")):
        doc = docx.Document(str(f))
        paras = doc.paragraphs
        idx = None
        for i, p in enumerate(paras):
            if p.text.strip().startswith("四、溯源索引"):
                idx = i
                break
        if idx is None:
            continue  # 标杆等无索引节
        # 检查是否已插入
        if any(RULE[:8] in p.text for p in paras):
            already += 1
            continue
        # 在索引标题后插入(标题后是说明段, 规则插在标题与说明段之间)
        new_p = paras[idx].insert_paragraph_before(RULE)
        done += 1
        if APPLY:
            doc.save(str(f))
print(f"插入: {done}  已存在跳过: {already}" + (" [已保存]" if APPLY else " [干跑]"))
