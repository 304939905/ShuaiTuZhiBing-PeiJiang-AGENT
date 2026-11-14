import glob, os, re
from docx import Document
REP = "D:/Desktop/shandou/学习汇报"
WORDS = ["仇算","同素","伯朗","巨熟","巨黍","炉素","薄浪","腾蛇","大桐琴","勞駮","日宁","像掠如火","游騎"]
hits = {w: [] for w in WORDS}
for f in sorted(glob.glob(REP + "/*.docx")):
    base = os.path.basename(f)
    try:
        doc = Document(f)
    except Exception as e:
        print("ERR", base, e); continue
    texts = [p.text for p in doc.paragraphs]
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    texts.append("[表]" + p.text)
    for t in texts:
        for w in WORDS:
            if w in t:
                hits[w].append((base, t.strip()[:200]))
for w in WORDS:
    print("=" * 20, w, len(hits[w]))
    for b, t in hits[w][:12]:
        print("  <%s>" % b[:34], t)
