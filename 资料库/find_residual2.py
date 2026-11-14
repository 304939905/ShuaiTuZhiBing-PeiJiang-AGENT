import glob, os
from docx import Document
REP = "D:/Desktop/shandou/学习汇报"
# 用 glob 匹配
targets = {
 "从零": ["伯朗","同素"],
 "玉符": ["薄浪"],
 "纯刀": ["驱逻"],
}
for pattern, words in targets.items():
    cands = sorted(glob.glob(REP + "/%s*_完整学习报告.docx" % pattern))
    if not cands: continue
    fn = cands[0]
    doc = Document(fn)
    base = os.path.basename(fn)[:30]
    for w in words:
        for i, p in enumerate(doc.paragraphs):
            if w in p.text:
                for j, r in enumerate(p.runs):
                    if w in r.text:
                        print("[%s] %s P%d R%d: '%s'" % (w, base, i, j, r.text[:80]))
        for ti, tbl in enumerate(doc.tables):
            for ri, row in enumerate(tbl.rows):
                for ci, cell in enumerate(row.cells):
                    for pi, p in enumerate(cell.paragraphs):
                        if w in p.text:
                            for j, r in enumerate(p.runs):
                                if w in r.text:
                                    print("[%s] %s T%dR%dC%dP%d R%d: '%s'" % (w, base, ti, ri, ci, pi, j, r.text[:80]))
