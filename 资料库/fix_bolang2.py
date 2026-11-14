import glob, os
from docx import Document
REP = "D:/Desktop/shandou/学习汇报"
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

for pat in ["杜预*", "战法篇*"]:
    for f in sorted(glob.glob(REP + "/" + pat + "*.docx")):
        doc = Document(f)
        n = rr(doc, {"伯朗":"博浪"})
        if n:
            print("%-42s 伯朗→博浪 %d 处" % (f[-42:], n))
            doc.save(f)
print("完成")
