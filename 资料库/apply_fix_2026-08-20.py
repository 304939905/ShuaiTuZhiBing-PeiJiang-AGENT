"""Apply confirmed fixes to 1秒版 reports and update verifier docs.
Run: 资料库/apply_2026-08-20_fix.py
"""
import re
from pathlib import Path
import docx
from docx.oxml.ns import qn

ROOT = Path("D:/Desktop/shandou/报告库")
fixes_applied = []

def replace_in_paragraphs(paragraphs, old, new):
    """Replace text across runs (word by word, not char by char) without losing formatting."""
    n = 0
    for p in paragraphs:
        full = "".join(r.text for r in p.runs)
        if old in full:
            # find positions of all runs; do per-run replacement if run contains old
            for r in p.runs:
                if old in r.text:
                    r.text = r.text.replace(old, new)
                    n += 1
            # if not in any single run (split across runs), concat & resplit
            if n == 0 and old in full:
                new_full = full.replace(old, new)
                # write all to first run, clear others
                if p.runs:
                    p.runs[0].text = new_full
                    for r in p.runs[1:]:
                        r.text = ""
                    n += 1
    return n

def replace_in_doc(doc, old, new):
    n = replace_in_paragraphs(doc.paragraphs, old, new)
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                n += replace_in_paragraphs(cell.paragraphs, old, new)
    return n

# === 1. 孟获篇 1秒版: 机势（愈战愈勇）→ 愈战击势 ===
f = ROOT/"旧56项目"/"逐帧1秒版"
cand = [c for c in f.glob("*.docx") if "孟获就是南蛮" in c.name]
if cand:
    doc = docx.Document(str(cand[0]))
    n1 = replace_in_doc(doc, "机势（愈战愈勇）", "愈战击势")
    n2 = replace_in_doc(doc, "机势/愈战愈勇", "愈战击势")
    if n1 or n2:
        doc.save(str(cand[0]))
        fixes_applied.append(f"孟获1秒版: 机势（愈战愈勇）→愈战击势 ×{n1}, 机势/愈战愈勇→愈战击势 ×{n2}")
    else:
        fixes_applied.append("孟获1秒版: 文本无匹配，未修改（可能已先期改正）")

print("\n".join(fixes_applied))
