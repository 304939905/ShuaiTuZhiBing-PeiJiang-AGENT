#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修正溯源规则插入位置: 移除标题前错位段, 正确插入到「四、溯源索引」标题后、说明段前。"""
import sys
from pathlib import Path
import docx

ROOT = Path("D:/Desktop/shandou/报告库")
APPLY = "--apply" in sys.argv
RULE = "溯源规则：时间锚存在 ±4 秒判读容差；若某时间段首帧画面与描述不符，请核验相邻 ±2~4 秒帧，取画面匹配者。"

fixed = 0
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
            continue
        changed = False
        # 1) 移除标题前错位段
        if idx > 0 and paras[idx - 1].text.strip().startswith("溯源规则："):
            el = paras[idx - 1]._element
            el.getparent().remove(el)
            changed = True
            idx -= 1
        # 2) 标题后应紧跟 RULE(说明段之前); 若没有则插入
        paras = doc.paragraphs
        if not (idx + 1 < len(paras) and paras[idx + 1].text.strip().startswith("溯源规则：")):
            paras[idx + 1].insert_paragraph_before(RULE)
            changed = True
        if changed:
            fixed += 1
            if APPLY:
                doc.save(str(f))
print(f"修正: {fixed}" + (" [已保存]" if APPLY else " [干跑]"))
