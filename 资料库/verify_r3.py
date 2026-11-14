import glob, os
from docx import Document
REP = "D:/Desktop/shandou/学习汇报"
WORDS = ["伯朗","同素","仇算","巨熟","龙林","薄浪","别名","大桐琴","腾蛇","勞駮","大补","驱逻","驱驰","崩溪驱逻"]
for f in sorted(glob.glob(REP + "/*.docx")):
    base = os.path.basename(f)
    doc = Document(f)
    texts = [p.text for p in doc.paragraphs]
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    texts.append(p.text)
    body = "\n".join(texts)
    hits = [(w, body.count(w)) for w in WORDS if w in body]
    if hits:
        print("%-40s  %s" % (base[:38], " | ".join("%s=%d"%h for h in hits)))
print("=== 验证结束 ===")
