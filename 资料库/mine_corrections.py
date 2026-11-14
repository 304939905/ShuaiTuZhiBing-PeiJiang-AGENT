# -*- coding: utf-8 -*-
"""从 1秒版 报告中挖掘 (错名 -> 正名) 校正对，用于反哺 完整版。
   重点提取箭头 `「X」→Y` 与 `误读/误写/确认为` 句式。"""
import sys, glob, re, os, json
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

BASE = "D:/Desktop/shandou/资料库"
REP = "D:/Desktop/shandou/学习汇报"

hero = set(json.load(open(BASE + "/official_hero_names.json", encoding="utf-8"))["names"])
jin = set(json.load(open(BASE + "/official_jineng_names_ext.json", encoding="utf-8"))["names"])
gear = set(json.load(open(BASE + "/official_gear_names.json", encoding="utf-8"))["names"])
allmap = json.load(open(BASE + "/official_all_names.json", encoding="utf-8"))["map"]

def doc_text(f):
    doc = Document(f)
    t = "\n".join(p.text for p in doc.paragraphs)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                t += "\n" + cell.text
    return t

pairs = {}  # basename -> list of (wrong, correct, kind)
for f in sorted(glob.glob(REP + "/*_逐帧深度学习报告_1秒版.docx")):
    base = os.path.basename(f).replace("_逐帧深度学习报告_1秒版.docx", "")
    text = doc_text(f)
    found = []
    # 1) 箭头: 「X」→Y  (Y 可能含 + 等连接)
    for m in re.finditer(r"[「『]([\u4e00-\u9fff]{1,8})[」』]\s*[→\-＞>]\s*([\u4e00-\u9fffA-Za-z+，、（）()\s]{1,24})", text):
        wrong = m.group(1).strip()
        right = m.group(2).strip().strip("，、 ")
        # 取右值里第一个白名单词作为正名（处理 "风声鹤唳+火烧连营" 多词）
        found.append(("arrow", wrong, right))
    # 2) 误读/误写为「Y」/误读为Y
    for m in re.finditer(r"误[读写]为?[「『]?\s*([\u4e00-\u9fff]{1,10})", text):
        found.append(("misc", "", m.group(1).strip()))
    # 3) 逐帧确认为「Y」/确认为「Y」
    for m in re.finditer(r"确认为[「『]?\s*([\u4e00-\u9fff]{1,12})", text):
        found.append(("confirm", "", m.group(1).strip()))
    if found:
        pairs[base] = found

# 打印箭头对（最干净），并标注右值是否在白名单
print("===== 箭头校正对（逐文件）=====")
arrow_count = 0
for base, found in pairs.items():
    arrows = [x for x in found if x[0] == "arrow"]
    if not arrows:
        continue
    print(f"\n▸ {base}")
    for kind, wrong, right in arrows:
        # 检验 right 是否整体或前缀是白名单名
        in_wl = right in allmap
        # 拆解 right 中可能的多词（+/、，）
        parts = re.split(r"[+，、，\s]", right)
        parts = [p for p in parts if p]
        wlparts = [p for p in parts if p in allmap]
        tag = "OK白名单" if (in_wl or wlparts) else "待核"
        print(f"   「{wrong}」→「{right}」  [{tag}]  含白名单:{wlparts}")
        arrow_count += 1
print(f"\n[箭头对总数] {arrow_count}")

# 也输出 misc/confirm 的正名候选（去重，不含箭头，仅看确认出的正名）
print("\n===== 误读/误写/确认为 提取的正名候选（去重，前60）=====")
cands = {}
for base, found in pairs.items():
    for kind, wrong, right in found:
        if kind == "arrow":
            continue
        if right in allmap:
            cands.setdefault(right, 0)
            cands[right] += 1
for c, n in sorted(cands.items(), key=lambda x: -x[1])[:60]:
    print(f"   {c}  ({n})")
