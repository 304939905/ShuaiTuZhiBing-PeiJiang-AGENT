# -*- coding: utf-8 -*-
"""定向扫描指定错名在全部 102 份报告中的分布（含段落定位），用于修复前评估。"""
import sys, glob, re, os, json
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

REP = "D:/Desktop/shandou/学习汇报"
TARGETS = ["久战魏犠", "久战不殆", "磐阵擅守", "捋出关西", "正始之变", "文德皇后",
           "以逸待劳", "以诱待来", "是否程昱"]

tot = {t: 0 for t in TARGETS}
detail = {}
for f in sorted(glob.glob(REP + "/*.docx")):
    bn = os.path.basename(f)
    d = Document(f)
    segs = [("p%d" % i, p.text) for i, p in enumerate(d.paragraphs)]
    for ti, tb in enumerate(d.tables):
        for ri, r in enumerate(tb.rows):
            for ci, c in enumerate(r.cells):
                segs.append(("t%d.%d.%d" % (ti, ri, ci), c.text))
    for loc, txt in segs:
        for t in TARGETS:
            n = txt.count(t)
            if n:
                tot[t] += n
                detail.setdefault(t, []).append({"file": bn, "loc": loc,
                                                 "n": n, "text": txt[:110]})

print("=== 总计 ===")
for t in TARGETS:
    print(f"  {t}: {tot[t]} 处")
print()
for t in TARGETS:
    if not detail.get(t):
        continue
    print("=" * 66)
    print(f"### {t}  共 {tot[t]} 处 / {len(set(x['file'] for x in detail[t]))} 份")
    for x in detail[t]:
        print(f"  [{x['loc']}] {x['file'][:34]}")
        print(f"        {x['text']}")
json.dump(detail, open("D:/Desktop/shandou/资料库/scan_targets.json", "w",
                       encoding="utf-8"), ensure_ascii=False, indent=2)
