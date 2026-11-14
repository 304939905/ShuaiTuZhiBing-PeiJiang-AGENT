# -*- coding: utf-8 -*-
"""Step2：抽取含算术推理的结论句，供人工/复核判读。
重点风险：发动率 加算 vs 乘算 模型误用；增伤叠加口径；百分比换算。
"""
import docx, os, glob, re

REPORT_DIR = r"D:\Desktop\shandou\学习汇报"
OUT = r"D:\Desktop\shandou\资料库\step2_reasoning.txt"

MARKERS = ["推算","因此","所以","合计","约等于","≈","叠加","增伤","伤害率","伤害",
           "发动率","发动概率","触发率","触发概率","几率","概率","期望值","提升","提高",
           "达到","相当于","倍率","净增","净","算","乘法","相加","总和","累计","凑满","叠满"]
# 高优先：发动率/概率类（加乘风险）
PROB_MARKERS = ["发动率","发动概率","触发率","触发概率","几率","概率","必中","必发动","一定发动","100%","百分之百"]

def text_of(path):
    d = docx.Document(path)
    out = []
    for p in d.paragraphs:
        if p.text.strip(): out.append(p.text)
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                if c.text.strip(): out.append(c.text)
    return out

def sentences(text):
    # split by Chinese/English terminators
    parts = re.split(r"[。！？\n；;]+", text)
    return [p.strip() for p in parts if p.strip()]

def has_num(s):
    return bool(re.search(r"\d|%|％|倍|×|倍率", s))

def main():
    files = sorted(glob.glob(os.path.join(REPORT_DIR, "*_1秒版.docx")))
    total = 0
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("# Step2 算术推理候选句（52 份一秒版）\n")
        for fp in files:
            name = os.path.basename(fp)
            txt = text_of(fp)
            for blk in txt:
                for s in sentences(blk):
                    if not has_num(s):
                        continue
                    if not any(m in s for m in MARKERS):
                        continue
                    total += 1
                    flag = " [PROB]" if any(m in s for m in PROB_MARKERS) else ""
                    f.write(f"\n[{name}]{flag}\n  {s}\n")
        f.write(f"\n# 合计候选句: {total}\n")
    print("done, candidates:", total, "->", OUT)

if __name__ == "__main__":
    main()
