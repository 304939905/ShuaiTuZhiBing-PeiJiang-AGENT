# -*- coding: utf-8 -*-
"""抽查：把指定报告全文 + 对应视频转录全文 并排导出，供人工核对是否有编造/失真"""
import os, sys, json, re, glob
from docx import Document

ROOT = r"D:\Desktop\shandou"
REP = os.path.join(ROOT, "学习汇报")
TDIRS = [os.path.join(ROOT, "抖音_transcripts"), os.path.join(ROOT, "抖音_transcripts", "开荒")]
OUT = os.path.join(ROOT, "资料库", "_spotcheck")
os.makedirs(OUT, exist_ok=True)

def norm(s):
    t = s
    for a, b in [("！","!"),("？","?"),("，",","),("：",":"),("；",";"),
                 ("（","("),("）",")"),("、",","),("　"," "),("｜","|")]:
        t = t.replace(a, b)
    return re.sub(r"\s+", "", t)

# 建转录索引
tmap = {}
for d in TDIRS:
    if not os.path.isdir(d): continue
    for f in os.listdir(d):
        if f.endswith(".json"):
            tmap[norm(os.path.splitext(f)[0])] = os.path.join(d, f)

def load_trans(stem):
    p = tmap.get(norm(stem))
    if not p: return None, None
    with open(p, encoding="utf-8") as fp:
        j = json.load(fp)
    segs = j.get("segments") or []
    lines = []
    for s in segs:
        st = s.get("start", 0); tx = (s.get("text") or "").strip()
        if tx:
            lines.append(f"[{int(st)//60:02d}:{int(st)%60:02d}] {tx}")
    return "\n".join(lines), p

def docx_text(p):
    d = Document(p)
    out = []
    for par in d.paragraphs:
        t = par.text.strip()
        if t: out.append(t)
    return "\n".join(out)

keys = sys.argv[1:]
for key in keys:
    cands = [f for f in os.listdir(REP)
             if f.endswith("_逐帧深度学习报告_1秒版.docx") and key in f]
    if not cands:
        print(f"!! 未找到匹配报告: {key}"); continue
    f = cands[0]
    stem = f[: -len("_逐帧深度学习报告_1秒版.docx")]
    rtxt = docx_text(os.path.join(REP, f))
    ttxt, tp = load_trans(stem)
    name = re.sub(r'[\\/:*?"<>|]', "_", stem)[:40]
    op = os.path.join(OUT, f"pair_{name}.txt")
    with open(op, "w", encoding="utf-8") as fp:
        fp.write("#" * 30 + " 报告全文 " + "#" * 30 + "\n")
        fp.write(f"文件: {f}\n\n{rtxt}\n\n")
        fp.write("#" * 30 + " 源视频转录 " + "#" * 30 + "\n")
        fp.write(f"来源: {tp}\n\n{ttxt if ttxt else '（未找到转录）'}\n")
    print(f"OK -> {op}  报告{len(rtxt)}字 / 转录{len(ttxt) if ttxt else 0}字")
