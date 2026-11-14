#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修正精编溯源索引末端越界引用: 引用的帧不存在时, 替换为该目录实际存在的最大帧。
用法: fix_overflow_refs.py [--apply]
"""
import sys, re
from pathlib import Path
import docx

ROOT = Path("D:/Desktop/shandou/报告库")
APPLY = "--apply" in sys.argv
NEW = re.compile(r"(frame_(\d{6})_(\d{2})h(\d{2})m(\d{2})s000ms\.jpg)")


def frame_at(dp, sec):
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return dp / f"frame_{sec+1:06d}_{h:02d}h{m:02d}m{s:02d}s000ms.jpg"


def max_existing(dp, sec):
    """返回 <= sec 的最大存在帧文件名, 无则 None。"""
    for s in range(sec, -1, -1):
        f = frame_at(dp, s)
        if f.exists():
            return f.name
        # 开荒合并: 子目录
        for sd in dp.iterdir():
            if sd.is_dir() and (sd / f.name).exists():
                return f.name
    return None


def fix_para(p, dp):
    """替换段落内所有不落地引用。返回替换次数。"""
    new_text = p.text
    cnt = 0
    for m in NEW.finditer(p.text):
        name, idx, hh, mm, ss = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        sec = int(hh) * 3600 + int(mm) * 60 + int(ss)
        if dp and not frame_at(dp, sec).exists():
            repl = max_existing(dp, sec)
            if repl and repl != name:
                new_text = new_text.replace(name, repl)
                cnt += 1
    if cnt == 0:
        return 0
    if p.runs:
        p.runs[0].text = new_text
        for r in p.runs[1:]:
            r.text = ""
    else:
        p.add_run(new_text)
    return cnt


total_fix = 0
for sub in ["旧56项目", "开荒", "海之呼唤", "赛季"]:
    d = ROOT / sub / "精编"
    if not d.exists():
        continue
    for f in sorted(d.glob("*.docx")):
        doc = docx.Document(str(f))
        full = "\n".join(p.text for p in doc.paragraphs)
        dm = re.search(r"源静帧目录[:：]\s*(.+)", full)
        dp = Path(dm.group(1).strip().rstrip("/")) if dm else None
        fixed = 0
        for p in doc.paragraphs:
            fixed += fix_para(p, dp)
        if fixed:
            total_fix += fixed
            print(f"  [{sub}] {f.name[:34]} 修正 {fixed} 处")
            if APPLY:
                doc.save(str(f))
print(f"\n总修正: {total_fix} 处" + (" [已保存]" if APPLY else " [干跑]"))
