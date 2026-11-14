import glob, os
from docx import Document
REP = "D:/Desktop/shandou/学习汇报"
FILES = [
 "从零开始，宝物养成焚决，来了！ 刚进征服看见宝物系统，摸不着头脑？老北带你从零开始上手宝物系统！_完整学习报告.docx",
 "玉符分配焚决， 来了！好刚花在刀刃上！_完整学习报告.docx",
 "纯刀居然还有上升空间？ 一个改动，拉高强度_完整学习报告.docx",
]
WORDS = {"从零":["伯朗","同素"],"玉符":["薄浪"],"纯刀":["驱逻"]}
for fn in FILES:
    key = fn[:2]
    doc = Document(os.path.join(REP, fn))
    for w in WORDS.get(key, []):
        # 检查段落
        for i, p in enumerate(doc.paragraphs):
            full = p.text
            if w in full:
                # 找出哪个 run 包含这个词
                for j, r in enumerate(p.runs):
                    if w in r.text:
                        print("[%s] P%d R%d: text='%s...'" % (w, i, j, r.text[:60]))
        # 检查表格
        for ti, tbl in enumerate(doc.tables):
            for ri, row in enumerate(tbl.rows):
                for ci, cell in enumerate(row.cells):
                    for pi, p in enumerate(cell.paragraphs):
                        if w in p.text:
                            for j, r in enumerate(p.runs):
                                if w in r.text:
                                    print("[%s] T%dR%dC%dP%d R%d: '%s...'" % (w, ti, ri, ci, pi, j, r.text[:60]))
