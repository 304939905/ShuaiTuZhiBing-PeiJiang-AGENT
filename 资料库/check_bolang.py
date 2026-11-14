import glob, os
from docx import Document
REP = "D:/Desktop/shandou/学习汇报"
for pat in ["杜预*", "战法篇*"]:
    for f in sorted(glob.glob(REP + "/" + pat + "*.docx")):
        doc = Document(f)
        for i, p in enumerate(doc.paragraphs):
            if "伯朗" in p.text:
                print("<%s> P%d: %s" % (os.path.basename(f)[:25], i, p.text.strip()[:120]))
