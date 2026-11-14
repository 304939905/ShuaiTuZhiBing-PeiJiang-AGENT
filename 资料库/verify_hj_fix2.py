# -*- coding: utf-8 -*-
"""最终验证：子串感知计数，区分 假性子串 / 已修清零 / 故意留作人工核查项。"""
import sys, glob, os, json, re
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

REP = "D:/Desktop/shandou/学习汇报"
# (token, guard_to_exclude_false_positive_substring)
CHECK = [
    ("重谋", None), ("夹许", None), ("三势", None), ("河内", "世泽"),
    ("顶足", None), ("壁瑞", None), ("几封讯类", None), ("以逸待劳", None),
    ("奉移艇", None), ("极锋而适", None), ("鸟云山兵", None), ("当仰巧", None),
    ("风生火烧", None), ("操缠", None), ("垒实迎虚", None), ("唐童", None),
    ("豹文刀", None), ("Boss", None), ("成育", None), ("雷石", None),
    ("重整", "旗鼓"),
]
# 故意留作人工核查（不在自动修复范围）
MANUAL = ["机势", "成立"]

def count_in_doc(doc, tok, exclude_sub=None):
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
    if exclude_sub:
        # 粗略扣除：包含 exclude_sub 的整串（如 河内世泽）中的 tok 计数
        # 用全文拼接估算（run 级已累加，这里用文件全文本再算一次含 exclude 的）
        pass
    return n

# 用全文本（含子串）一次性统计，再减去“伪性子串”出现次数
def full_text(doc):
    t = "\n".join(p.text for p in doc.paragraphs)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                t += "\n" + cell.text
    return t

per_file = {}
manual_per_file = {}
total = {t: 0 for t, _ in CHECK}
broken = []
for f in sorted(glob.glob(REP + "/*_完整学习报告.docx")):
    try:
        doc = Document(f)
    except Exception as e:
        broken.append((os.path.basename(f), str(e))); continue
    txt = full_text(doc)
    rem = {}
    for tok, ex in CHECK:
        c = txt.count(tok)
        if ex:
            c -= txt.count(tok + ex)  # 扣除 河内世泽 / 重整旗鼓 中的假性子串
        if c > 0:
            rem[tok] = c; total[tok] += c
    if rem:
        per_file[os.path.basename(f)] = rem
    mrem = {m: txt.count(m) for m in MANUAL if txt.count(m) > 0}
    if mrem:
        manual_per_file[os.path.basename(f)] = mrem

print("=== 已自动修复项 当前真实残留（已扣假性子串）===")
for t, c in total.items():
    if c:
        print(f"  {t}: {c}")
print("\n=== 真实残留>0 的文件 ===")
for f, rem in per_file.items():
    print(f"  {f}\n     {rem}")
print("\n=== 故意留作人工核查（机势/成立）===")
mc = 0
for f, m in manual_per_file.items():
    print(f"  {f}\n     {m}")
    mc += sum(m.values())
print(f"  人工核查项合计: {mc}")
print(f"\n文件可打开性: {'全部正常' if not broken else '损坏:'+str(broken)}")
print(f"自动修复项剩余种类: {sum(1 for c in total.values() if c)} / {len(CHECK)}")
json.dump({"real_residual": per_file, "real_residual_total": total,
           "manual": manual_per_file, "broken": broken},
          open("D:/Desktop/shandou/资料库/verify_hj_fix2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
