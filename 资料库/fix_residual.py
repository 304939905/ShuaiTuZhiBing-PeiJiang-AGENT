import os, shutil, glob
from docx import Document
REP = "D:/Desktop/shandou/学习汇报"
APPLY = True  # 直接执行
def rr(doc, mp):
    n=0
    def do(ps):
        nonlocal n
        for p in ps:
            for r in p.runs:
                for o,nv in mp.items():
                    if o in r.text:
                        n+=r.text.count(o); r.text=r.text.replace(o,nv)
    do(doc.paragraphs)
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                do(c.paragraphs)
    return n

# 补漏映射
JOBS = [
 ("玉符*", {"薄浪":"博浪"}),
 ("纯刀*", {"驱逻":"屈卢"}),
 ("从零*", {"伯朗":"博浪","同素":"彤素"}),
]
for pat, mp in JOBS:
    for f in sorted(glob.glob(REP + "/" + pat)):
        doc = Document(f)
        n = rr(doc, mp)
        if n:
            print("%-40s +%d 处: %s" % (f[-40:], n, ", ".join(mp.keys())))
            if APPLY: doc.save(f)
print("补漏完成")
