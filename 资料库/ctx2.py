import glob, os
from docx import Document
REP = "D:/Desktop/shandou/学习汇报"
WORDS = ["英务","奇策","奇袭","英勇","制策","至策","迅锋"]
hits = {w: [] for w in WORDS}
for f in sorted(glob.glob(REP + "/*.docx")):
    base = os.path.basename(f)
    doc = Document(f)
    texts = [p.text for p in doc.paragraphs]
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    texts.append("[表]" + p.text)
    for t in texts:
        for w in WORDS:
            if w in t:
                hits[w].append((base, t.strip()[:170]))
for w in WORDS:
    print("=" * 16, w, len(hits[w]))
    for b, t in hits[w][:8]:
        print("  <%s>" % b[:30], t)
