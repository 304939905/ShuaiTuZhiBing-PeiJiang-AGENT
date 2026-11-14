# -*- coding: utf-8 -*-
"""验证：修复后完整版中 原错名 残留计数 + 文件可打开性。"""
import sys, glob, os, json
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

REP = "D:/Desktop/shandou/学习汇报"
WRONG = ["重谋","夹许","三势","河内","风生火烧","顶足","当仰巧","壁瑞","鸟云山兵",
"成立","几封讯类","Boss","重整","操缠","垒实迎虚","唐童","豹文刀","机势",
"胜负先征","以逸待劳","奉移艇","极锋而适","成育","雷石"]

def count_in_doc(doc, tok):
    n = 0
    for p in doc.paragraphs:
        for r in p.runs:
            n += r.text.count(tok)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for r in p.runs:
                        n += r.text.count(tok)
    return n

total_remain = {t: 0 for t in WRONG}
broken = []
per_file = {}
for f in sorted(glob.glob(REP + "/*_完整学习报告.docx")):
    try:
        doc = Document(f)
    except Exception as e:
        broken.append((os.path.basename(f), str(e)))
        continue
    rem = {t: count_in_doc(doc, t) for t in WRONG if count_in_doc(doc, t) > 0}
    if rem:
        per_file[os.path.basename(f)] = rem
        for t, c in rem.items():
            total_remain[t] += c

print("=== 各原错名 修复后残留总数 ===")
for t, c in total_remain.items():
    if c:
        print(f"  {t}: {c}")
print("\n=== 残留>0 的文件 ===")
for f, rem in per_file.items():
    print(f"  {f}\n     {rem}")
print(f"\n文件可打开性: {'全部正常' if not broken else '有损坏:'+str(broken)}")
print(f"仍有残留的错名种类: {sum(1 for c in total_remain.values() if c)} / {len(WRONG)}")
json.dump({"per_file": per_file, "total_remain": total_remain, "broken": broken},
          open("D:/Desktop/shandou/资料库/verify_hj_fix.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
