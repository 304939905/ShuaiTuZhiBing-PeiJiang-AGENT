# -*- coding: utf-8 -*-
"""第二轮安全修复（完整版 武将/战法 音译误识）。
   - 全局（所有完整版）：成育->程昱、雷石->垒实（无歧义、非子串，安全）
   - 徐庶篇单独：机势->金吾飞将（机势 是多义音近错名，不可全局统一）"""
import sys, glob, os, json
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

REP = "D:/Desktop/shandou/学习汇报"

GLOBAL = {"成育": "程昱", "雷石": "垒实"}

def replace_in_doc(doc, mp):
    counts = {}
    def do_runs(paras):
        for p in paras:
            for r in p.runs:
                for old, new in mp.items():
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
# 全局
g_total = {}
for f in sorted(glob.glob(REP + "/*_完整学习报告.docx")):
    doc = Document(f)
    c = replace_in_doc(doc, GLOBAL)
    if c:
        doc.save(f)
        for k, v in c.items():
            g_total[k] = g_total.get(k, 0) + v
        log.append(f"[全局] {os.path.basename(f)}: {c}")
log.append(f"全局合计: {g_total}")

# 徐庶篇 机势->金吾飞将
fs = glob.glob(REP + "/*徐庶*_完整学习报告.docx")
if fs:
    doc = Document(fs[0])
    c = replace_in_doc(doc, {"机势": "金吾飞将"})
    if c:
        doc.save(fs[0])
        log.append(f"[徐庶] {os.path.basename(fs[0])}: 机势->{c['机势']}处")
    else:
        log.append(f"[徐庶] 机势未出现（0处）")
else:
    log.append("[徐庶] 未找到文件")

print("\n".join(log))
json.dump(log, open("D:/Desktop/shandou/资料库/fix_fullver_hj_log2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n[完成] 见 fix_fullver_hj_log2.json")
