#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量更新报告内帧引用: 旧格式 frame_XXXX_MM-SS.jpg -> 新格式 frame_000001_00h00m00s000ms.jpg
处理: 精编(71) + 1秒版(74) 所有 docx 段落。
用法: update_frame_refs.py [--apply]
"""
import sys, re
from pathlib import Path
import docx

ROOT = Path("D:/Desktop/shandou/报告库")
APPLY = "--apply" in sys.argv

OLD = re.compile(r"frame_(\d{4})_(\d{2})-(\d{2})(?:\.jpg)?")


def new_name(sec):
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"frame_{sec+1:06d}_{h:02d}h{m:02d}m{s:02d}s000ms.jpg"


def repl(m):
    sec = int(m.group(2)) * 60 + int(m.group(3))
    return new_name(sec) + ".jpg"


def replace_in_para(p):
    new_text = OLD.sub(repl, p.text)
    if new_text == p.text:
        return False
    if p.runs:
        p.runs[0].text = new_text
        for r in p.runs[1:]:
            r.text = ""
    else:
        p.add_run(new_text)
    return True


files_changed = 0
total_refs = 0
for sub in ["旧56项目", "开荒", "海之呼唤", "赛季"]:
    for layer in ["精编", "逐帧1秒版"]:
        d = ROOT / sub / layer
        if not d.exists():
            continue
        for f in sorted(d.glob("*.docx")):
            doc = docx.Document(str(f))
            changed = 0
            for p in doc.paragraphs:
                n = len(OLD.findall(p.text))
                if n and replace_in_para(p):
                    changed += n
            # 表格内也可能有引用(1秒版插图说明等)
            for tb in doc.tables:
                for row in tb.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            n = len(OLD.findall(p.text))
                            if n and replace_in_para(p):
                                changed += n
            if changed:
                files_changed += 1
                total_refs += changed
                print(f"  [{sub}/{layer}] {f.name[:36]} 替换 {changed} 处")
                if APPLY:
                    doc.save(str(f))
print(f"\n文件: {files_changed} 处引用: {total_refs}")
print("[干跑] 未保存" if not APPLY else "[已保存]")
