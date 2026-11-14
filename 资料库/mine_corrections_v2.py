# -*- coding: utf-8 -*-
"""句子级挖掘 1秒版 纠错留痕：定位含纠错关键词的句子，抽取内部「X」令牌，
   按 前错后对 + 误写反转 规则配对 (wrong->correct)，并校验正名是否在白名单。"""
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

KEYW = re.compile(r"(误[读写称]|实为|确认为|无法确认|逐帧|转写|留痕|校正|近似|近音|不清|存疑|搞反|搞错|不对|不是|而非|即非|记作|记为|写作|误作)")
QUOTE = re.compile(r"[「『]([\u4e00-\u9fffA-Za-z+，、]{1,12})[」』]")

def validate(tok):
    tok = tok.strip().strip("，、+")
    return tok in allmap

results = {}
for f in sorted(glob.glob(REP + "/*_逐帧深度学习报告_1秒版.docx")):
    base = os.path.basename(f).replace("_逐帧深度学习报告_1秒版.docx", "")
    text = doc_text(f)
    sents = re.split(r"[。；;！!？?\n]", text)
    pairs = []
    for s in sents:
        if not KEYW.search(s):
            continue
        toks = QUOTE.findall(s)
        toks = [t for t in toks if t.strip()]
        if len(toks) < 1:
            continue
        wrong = correct = None
        if re.search(r"误[读写称]", s):
            # 误写/误读 后的令牌是错的；其余（尤其 确认为/实为 后的）是对的
            mw = re.search(r"误[读写称][为作]?[「『]?\s*([\u4e00-\u9fffA-Za-z+，、]{1,12})", s)
            if mw:
                wrong = mw.group(1).strip().strip("，、+")
            # correct = 确认为/实为 后的令牌
            mc = re.search(r"(?:确认为|实为)[「『]?\s*([\u4e00-\u9fffA-Za-z+，、]{1,12})", s)
            if mc:
                correct = mc.group(1).strip().strip("，、+")
        if not correct:
            mc = re.search(r"(?:确认为|实为|即)[「『]?\s*([\u4e00-\u9fffA-Za-z+，、]{1,12})", s)
            if mc:
                correct = mc.group(1).strip().strip("，、+")
        if not wrong and len(toks) >= 2:
            wrong = toks[0].strip().strip("，、+")
        if not correct and len(toks) >= 2:
            correct = toks[-1].strip().strip("，、+")
        if wrong and correct and wrong != correct and validate(correct):
            pairs.append((wrong, correct))
    # 去重
    seen = set(); uniq = []
    for p in pairs:
        if p not in seen:
            seen.add(p); uniq.append(p)
    if uniq:
        results[base] = uniq

total = 0
for base, pairs in results.items():
    print(f"\n▸ {base}")
    for w, c in pairs:
        kind = allmap.get(c, "?")
        print(f"   「{w}」→「{c}」  [{kind}]")
        total += 1
print(f"\n[校正对总数] {total}  （涉及 {len(results)} 个视频）")
json.dump(results, open(BASE + "/corrections_mined.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("[写出] corrections_mined.json")
