# -*- coding: utf-8 -*-
"""Step5 联网核验修复：大橹品质/自带效果 + 元戎自带效果名（官方 gear_id.json + 官网 + 网易大神 三方核验）。"""
import docx, os

REP = "D:/Desktop/shandou/学习汇报"

f1 = os.path.join(REP, "从零开始，宝物养成焚决，来了！ 刚进征服看见宝物系统，摸不着头脑？老是乱打一堆毫不适配的残品？别着急，北冥让你一篇看懂！_逐帧深度学习报告_1秒版.docx")
f2 = os.path.join(REP, "程昱魏智最强搭配—所有细节一篇看懂 魏智的宝物你真的带对了吗？_逐帧深度学习报告_1秒版.docx")

# (file, old, new)
REPL = [
    # 元戎 自带效果名：骁锐/无妄/选锋 -> 陷阵/无畏/迸发（数值1.0%/2.0%保留，官方 gear_id.json 确认）
    (f1, "三条自带效果（骁锐：攻击属性提高1.0%；无妄：追击战法伤害提高2.0%；选锋：首次发动追击主战法时额外选取距离内1个目标）",
         "三条自带效果（陷阵：攻击属性提高1.0%；无畏：追击战法伤害提高2.0%；迸发：首次发动追击主战法时额外选取距离内1个目标）"),
    (f1, "三条自带效果（骁锐+1.0%/无妄+2.0%/选锋额外目标）",
         "三条自带效果（陷阵+1.0%/无畏+2.0%/迸发额外目标）"),
    (f1, "元戎：骁锐+1.0%/无妄+2.0%/选锋（额外目标）",
         "元戎：陷阵+1.0%/无畏+2.0%/迸发（额外目标）"),
    # 大橹 品质 六韬 -> 稀世（官网 stzb.163.com/baowulist/1078.html 明写 品质:稀世）
    (f2, "（刀类，六韬品质），四条效果：骁韧(普攻伤降1.0%)、坚忍(主动战法伤降1.0%)、规避(首受伤害进规避免1次)、机敏(主战法发动率+6.0%)",
         "（刀类，稀世品质），自带效果：强韧(普攻伤降1.0%)、坚忍(主动战法伤降1.0%)、规避(首受伤害进规避免1次)；该大橹另锻造机敏词条(主战法发动率+6.0%)"),
    (f2, "大橹宝物详情页（六韬品质）：骁韧(普攻伤降1.0%)、坚忍(主动战法伤降1.0%)、规避(首受伤害进规避状态免1次)、机敏(主战法发动率+6.0%)",
         "大橹宝物详情页（稀世品质）：强韧(普攻伤降1.0%)、坚忍(主动战法伤降1.0%)、规避(首受伤害进规避状态免1次)；该大橹另锻造机敏词条(主战法发动率+6.0%)"),
    (f2, "大橹的四条效果（骁韧/坚忍/规避/机敏）",
         "大橹的自带效果（强韧/坚忍/规避）+ 锻造词条机敏"),
    (f2, "大橹(刀类/六韬/骁韧+坚忍+规避+机敏词条)",
         "大橹(刀类/稀世/强韧+坚忍+规避自带+机敏锻造词条)"),
]

def apply(doc_path, old, new):
    d = docx.Document(doc_path)
    targets = list(d.paragraphs) + [c for t in d.tables for r in t.rows for c in r.cells]
    n = 0
    for obj in targets:
        text = obj.text
        if old in text:
            # run-level replace to preserve formatting
            if hasattr(obj, "runs") and obj.runs:
                for run in obj.runs:
                    if old in run.text:
                        run.text = run.text.replace(old, new)
                        n += 1
                        break
                else:
                    obj.text = text.replace(old, new); n += 1
            else:
                obj.text = text.replace(old, new); n += 1
    if n:
        d.save(doc_path)
    return n

total = 0
for fp, old, new in REPL:
    c = apply(fp, old, new)
    print(("OK  " if c else "MISS") + "  x%d  %s" % (c, old[:40]))
    total += c
print("TOTAL replacements:", total)
