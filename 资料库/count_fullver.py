# -*- coding: utf-8 -*-
import glob, os
from docx import Document
REP = "D:/Desktop/shandou/学习汇报"
# 按文件定制的映射（因同一音译在不同报告指向不同宝物，不能全局替换）
JOBS = {
 "从零开始，宝物养成焚决，来了！ 刚进征服看见宝物系统，摸不着头脑？老北带你从零开始上手宝物系统！":
    {"伯朗":"博浪","同素":"彤素","制策":"至策"},
 "徐庶能玩吗？ 当然可以，平民极佳的战磐选择，来了！":
    {"龙林":"龙鳞","薄浪":"彤素","别名":"博浪"},
 "玉符分配焚决， 来了！好刚花在刀刃上！":
    {"仇算":"筹算","薄浪":"博浪","坚韧":"坚忍"},
 "纯刀居然还有上升空间？ 一个改动，拉高强度":
    {"巨熟":"钜黍","巨黍":"钜黍","崩溪驱逻":"屈卢"},
 "距离思路究极细节 ，普攻距离和战法距离，真的是越远越好吗？":
    {"巨熟":"钜黍","巨黍":"钜黍"},
 "马超纯刀最强配置卷土来袭! 单次进攻两万五武勋!两个细节带飞马超!":
    {"巨黍":"钜黍","驱逻":"屈卢"},
 "程昱魏智最强搭配—所有细节一篇看懂 魏智的宝物你真的带对了吗？":
    {"兴汉大陆":"星汉","大补":"大橹"},
}
allf = glob.glob(REP + "/*_完整学习报告.docx")
tot = 0
for key, mp in JOBS.items():
    cands = [f for f in allf if key[:22] in os.path.basename(f)]
    if not cands:
        print("!! 未匹配到文件:", key[:30]); continue
    f = cands[0]
    doc = Document(f)
    texts = [p.text for p in doc.paragraphs]
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    texts.append(p.text)
    body = "\n".join(texts)
    parts = []
    for o, n in mp.items():
        c = body.count(o)
        tot += c
        parts.append("%s→%s:%d" % (o, n, c))
    print("%-30s  %s" % (os.path.basename(f)[:28], " | ".join(parts)))
print("\n合计待替换 %d 处" % tot)
