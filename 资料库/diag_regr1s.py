# -*- coding: utf-8 -*-
"""诊断：把一秒版回归残留 token 的上下文全部 dump 出来，判断是引用型还是断言型。"""
import sys, glob, re, os, json
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

BASE = "D:/Desktop/shandou/资料库"
REP = "D:/Desktop/shandou/学习汇报"

QUOTE_MARK = re.compile(
    r"(?:既有报告|既有音频|音频转写|音频版|转写为|转写作|误写|误读|误作|误识为|写作|记为|称为|称作|"
    r"音译|近音|读音|无法确认|猜测|泛称|标注推断|旧版|原片|前作|上集|同系列|同款|对比|卡面佐证|"
    r"姊妹|画面对比|早期|初版|草案|暂记|待核|亦作|即[「『【])"
)
BOOK = re.compile(r"《([\u4e00-\u9fff]{2,10})》")

def is_cited(text, pos, tok, span=40):
    head = text[max(0, pos - span):pos]
    if QUOTE_MARK.search(head):
        return True
    seg = text[max(0, pos - 12):pos + len(tok) + 1]
    if re.search(r"《\s*" + re.escape(tok) + r"\s*》", seg):
        return True
    return False

WRONG = ["重谋","夹许","三势","河内","顶足","壁瑞","几封讯类","以逸待劳","奉移艇",
         "极锋而适","鸟云山兵","当仰巧","风生火烧","操缠","垒实迎虚","唐童","豹文刀",
         "Boss","成育","雷石","重整","机势"]
STRICT = {"河内":r"河内(?!郡|之地|世泽)","三势":r"三势(?!阵)","重整":r"重整(?!旗鼓|军备)"}

files = sorted(glob.glob(REP + "/*_逐帧深度学习报告_1秒版.docx"))
for f in files:
    bn = os.path.basename(f)
    doc = Document(f)
    text = "\n".join(p.text for p in doc.paragraphs)
    for tbl in doc.tables:
        for row in tbl.rows:
            for c in row.cells:
                text += "\n" + c.text
    for w in WRONG:
        pat = STRICT.get(w, re.escape(w))
        for m in re.finditer(pat, text):
            cited = is_cited(text, m.start(), w)
            ctx = text[max(0,m.start()-45):m.end()+20].replace("\n"," ")
            if not cited:
                print(f"[断言?] {bn[:30]} | 「{w}」 | {ctx}")
