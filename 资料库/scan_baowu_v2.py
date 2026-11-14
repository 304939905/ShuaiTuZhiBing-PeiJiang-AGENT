# -*- coding: utf-8 -*-
"""产出可读摘要：每份报告含'宝物'的段落 + 所有【X】词条上下文，供人工研判 OCR 误识。"""
import sys, glob, re, os
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

REP = "D:/Desktop/shandou/学习汇报"

out = []
for f in sorted(glob.glob(REP + "/*_逐帧深度学习报告_1秒版.docx")):
    name = os.path.basename(f).replace("_逐帧深度学习报告_1秒版.docx", "")
    doc = Document(f)
    paras = [p.text for p in doc.paragraphs if p.text.strip()]
    # 宝物相关段落
    bao = [t for t in paras if "宝物" in t]
    # 【X】 词条上下文：取所在句子
    citiao_ctx = []
    for t in paras:
        for m in re.finditer(r"【([\u4e00-\u9fff]{1,8})】", t):
            citiao_ctx.append((m.group(1), t))
    if bao or citiao_ctx:
        out.append("="*70)
        out.append(f"报告：{name}")
        if bao:
            out.append("-- 含'宝物'的段落 --")
            for t in bao:
                out.append("  · " + t)
        if citiao_ctx:
            out.append("-- 【X】 词条/术语上下文 --")
            for x, t in citiao_ctx:
                out.append(f"  【{x}】 <- {t}")

open("D:/Desktop/shandou/资料库/scan_baowu_digest.txt", "w", encoding="utf-8").write("\n".join(out))
print(f"写出 scan_baowu_digest.txt，共 {len(out)} 行")
