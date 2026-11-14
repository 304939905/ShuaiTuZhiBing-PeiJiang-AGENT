import glob, os, re, json
from docx import Document
REP = "D:/Desktop/shandou/学习汇报"
OFFICIAL = set(json.load(open("D:/Desktop/shandou/资料库/official_baowu_names.json", encoding="utf-8")))
# 从1秒版抽"纠错留痕"句：含 既有报告/音频转写/逐帧确认/误写 等关键词
KEYS = ["既有报告", "音频转写", "逐帧确认", "误写", "转写为", "应为", "实为"]
out = []
for f in sorted(glob.glob(REP + "/*_逐帧深度学习报告_1秒版.docx")):
    base = os.path.basename(f).replace("_逐帧深度学习报告_1秒版.docx", "")
    doc = Document(f)
    texts = [p.text for p in doc.paragraphs]
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    texts.append(p.text)
    for t in texts:
        t = t.strip()
        if not t or len(t) > 300:
            continue
        if sum(1 for k in KEYS if k in t) >= 1 and ("「" in t or "『" in t or "【" in t):
            out.append((base, t))
print("命中纠错留痕句 %d 条\n" % len(out))
cur = None
for b, t in out:
    if b != cur:
        print("\n" + "=" * 8 + " " + b)
        cur = b
    print("   " + t)
