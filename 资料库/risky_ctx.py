# -*- coding: utf-8 -*-
import glob, os
from docx import Document
REP = "D:/Desktop/shandou/学习汇报"
RISKY = ["别名", "坚韧", "大补", "薄浪"]
for f in sorted(glob.glob(REP + "/*_完整学习报告.docx")):
    base = os.path.basename(f).replace("_完整学习报告.docx", "")
    doc = Document(f)
    texts = [p.text for p in doc.paragraphs]
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    texts.append("[表]" + p.text)
    found = []
    for t in texts:
        for w in RISKY:
            if w in t:
                found.append((w, t.strip()))
    if found:
        print("\n" + "#" * 6 + " " + base[:40])
        for w, t in found:
            print("  [%s] %s" % (w, t[:150]))
