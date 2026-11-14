# -*- coding: utf-8 -*-
"""导出 qc_gate 回归命中项的原文上下文，用于人工判定真错 or 误报。"""
import sys, glob, re, os, json
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

REP = "D:/Desktop/shandou/学习汇报"
rep = json.load(open("D:/Desktop/shandou/资料库/qc_gate_report.json", encoding="utf-8"))

def doc_text(f):
    d = Document(f)
    t = "\n".join(p.text for p in d.paragraphs)
    for tb in d.tables:
        for r in tb.rows:
            for c in r.cells:
                t += "\n" + c.text
    return t

EST = ["是否程昱", "不程昱", "才程昱", "都程昱", "仍程昱", "同时程昱", "能否程昱",
       "稳定程昱", "规律程昱", "程昱的前提", "不能同时程昱", "保护组合程昱",
       "保护程昱", "前提下程昱"]

for label in ("完整版", "一秒版"):
    regr = rep[label]["regression_residual"]
    print("#" * 70)
    print(f"### {label}  共 {len(regr)} 份")
    for bn, hits in regr.items():
        f = os.path.join(REP, bn)
        text = doc_text(f)
        print("-" * 70)
        print(f"[{bn}]")
        for w, n in hits.items():
            if w == "establish_程昱":
                for p in n:
                    for m in re.finditer(re.escape(p), text):
                        s = max(0, m.start() - 45); e = min(len(text), m.end() + 45)
                        print(f"   <程昱> ...{text[s:e]}...".replace("\n", "⏎"))
                continue
            cnt = 0
            for m in re.finditer(re.escape(w), text):
                s = max(0, m.start() - 40); e = min(len(text), m.end() + 40)
                print(f"   <{w}> ...{text[s:e]}...".replace("\n", "⏎"))
                cnt += 1
                if cnt >= 4:
                    break
