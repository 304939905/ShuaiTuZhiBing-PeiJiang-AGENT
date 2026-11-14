# -*- coding: utf-8 -*-
"""第三轮：无歧义、非子串碰撞的 武将/战法 音译误识 全局修复（所有完整版）。
   带负向预查，避免 河内->河内世泽 后 河内世泽 被再次追加。"""
import sys, glob, os, json, re
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

REP = "D:/Desktop/shandou/学习汇报"

# (old, new, guard_regex_for_old)  guard=None 表示直接替换
GLOBAL = [
    ("重谋", "众谋不懈", None),
    ("夹许", "众谋不懈", None),
    ("三势", "三术奇谋", None),
    ("河内", "河内世泽", r"河内(?!世泽)"),
    ("顶足", "鼎足江东", None),
    ("壁瑞", "避锐治气", None),
    ("几封讯类", "疾风迅雷", None),
    ("以逸待劳", "以诱待来", None),
    ("奉移艇", "掎角之势", None),
    ("极锋而适", "及锋而试", None),
    ("鸟云山兵", "乌云山兵", None),
    ("当仰巧", "当阳桥", None),
    ("风生火烧", "风声鹤唳+火烧连营", None),
    ("操缠", "衡轭", None),
    ("垒实迎虚", "垒实迎击", None),
    ("唐童", "庞统", None),
    ("豹文刀", "曹纯", None),
    ("Boss", "褒姒", None),
    ("成育", "程昱", None),
    ("雷石", "垒实", None),
    ("重整", "重整旗鼓", r"重整(?!旗鼓)"),
    # 注意：「成立」为常用词，全局替换有污染合法用法风险，留作人工逐篇核查（不在全局自动修复）
]

def replace_in_doc(doc):
    counts = {}
    def do_runs(paras):
        for p in paras:
            for r in p.runs:
                for old, new, guard in GLOBAL:
                    if guard:
                        if re.search(guard, r.text):
                            c = len(re.findall(guard, r.text))
                            r.text = re.sub(guard, new, r.text)
                            counts[old] = counts.get(old, 0) + c
                    else:
                        if old in r.text:
                            c = r.text.count(old)
                            r.text = r.text.replace(old, new)
                            counts[old] = counts.get(old, 0) + c
    do_runs(doc.paragraphs)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                do_runs(cell.paragraphs)
    return counts

log = []
g_total = {}
for f in sorted(glob.glob(REP + "/*_完整学习报告.docx")):
    doc = Document(f)
    c = replace_in_doc(doc)
    if c:
        doc.save(f)
        for k, v in c.items():
            g_total[k] = g_total.get(k, 0) + v
        log.append(f"[全局] {os.path.basename(f)}: {c}")
log.append(f"全局合计本轮新增替换: {g_total}")
# 机势 仍按视频（已在 pass1/pass2 处理高顺/徐庶）；其余机势留待人工
print("\n".join(log))
json.dump({"per_file": log, "total": g_total},
          open("D:/Desktop/shandou/资料库/fix_fullver_hj_log3.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n[完成] 见 fix_fullver_hj_log3.json")
