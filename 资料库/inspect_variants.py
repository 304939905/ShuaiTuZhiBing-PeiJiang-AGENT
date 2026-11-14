# -*- coding: utf-8 -*-
"""校准结构判定 + 打印变体上下文，决定修正策略。"""
import os, re, glob
from docx import Document

REPORT_DIR = r"D:/Desktop/shandou/学习汇报"
PATTERN = "*逐帧深度学习报告_1秒版.docx"

FOCUS = ["高顺领衔群骑，来了！ 8回合高频解控，四重增伤，非常均衡的一队。_逐帧深度学习报告_1秒版.docx",
         "装糖队到底糖不糖 一支拉满细节的队伍，非常值得推敲。  原创队伍。_逐帧深度学习报告_1秒版.docx",
         "七擒七纵就是高配磐阵 ，战磐体系迎来全面加强，七擒七纵强度不错。_逐帧深度学习报告_1秒版.docx"]

VARIANTS = ["重谋","全军","薄浪","鼎足","避其锐气","巨黍","三部上线","魂水","战盘",
            "同素","当洋桥","油飘","极锋而适","衡热","巨熟","远宫密策","星汉继世"]

def get_text(doc):
    parts=[]
    for p in doc.paragraphs:
        if p.text.strip(): parts.append(p.text)
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                if c.text.strip(): parts.append(c.text)
    return "\n".join(parts)

def headings(doc):
    out=[]
    for p in doc.paragraphs:
        sn=(p.style.name or "") if p.style else ""
        if ("Heading" in sn or "标题" in sn) and p.text.strip():
            out.append(p.text.strip())
    return out

print("########## 结构校准：抽样报告真实标题 ##########")
for fn in FOCUS:
    fp=os.path.join(REPORT_DIR, fn)
    if not os.path.exists(fp): 
        print("缺失:", fn); continue
    doc=Document(fp)
    print(f"\n--- {fn[:30]}... ---")
    for h in headings(doc)[:30]:
        print("  H:", h)

print("\n\n########## 变体上下文（每词首现 ±30 字）##########")
files=sorted(glob.glob(os.path.join(REPORT_DIR, PATTERN)))
for f in files:
    name=os.path.basename(f); doc=Document(f); text=get_text(doc)
    for v in VARIANTS:
        idx=text.find(v)
        if idx>=0:
            s=max(0,idx-30); e=min(len(text),idx+len(v)+30)
            ctx=text[s:e].replace("\n"," ")
            print(f"[{name[:18]}] {v} :: …{ctx}…")
