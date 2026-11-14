# -*- coding: utf-8 -*-
import os, shutil, sys
from docx import Document
REP = "D:/Desktop/shandou/学习汇报"
BAK = REP + "/_backup_before_errata/official_ocr_20260809"
os.makedirs(BAK, exist_ok=True)
APPLY = "--apply" in sys.argv

def replace_all_runs(doc, mapping):
    n = 0
    def do(paras):
        nonlocal n
        for p in paras:
            for r in p.runs:
                for old, new in mapping.items():
                    if old in r.text:
                        n += r.text.count(old)
                        r.text = r.text.replace(old, new)
    do(doc.paragraphs)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                do(cell.paragraphs)
    return n

# 按文件定制映射（同一音译在不同报告指向不同宝物）
JOBS = [
 ("从零开始，宝物养成焚决，来了！ 刚进征服看见宝物系统，摸不着头脑？老北带你从零开始上手宝物系统！",
  {"伯朗":"博浪","同素":"彤素","制策":"至策","迅锋":"选锋"}),
 ("徐庶能玩吗？ 当然可以，平民极佳的战磐选择，来了！",
  {"龙林":"龙鳞","薄浪":"博浪","别名":"别鸣"}),
 ("玉符分配焚决， 来了！好刚花在刀刃上！",
  {"仇算":"筹算","坚韧":"坚忍"}),
 ("纯刀居然还有上升空间？ 一个改动，拉高强度",
  {"巨熟":"钜黍","巨黍":"钜黍","崩溪驱逻":"屈卢"}),
 ("距离思路究极细节 ，普攻距离和战法距离，真的是越远越好吗？",
  {"巨熟":"钜黍","巨黍":"钜黍"}),
 ("马超纯刀最强配置卷土来袭! 单次进攻两万五武勋!两个细节带飞马超!",
  {"巨黍":"钜黍","驱逻":"屈卢"}),
 ("率土武将志—贾诩 使用手册来了!一篇全看懂!",
  {"大补":"大橹"}),
]

allf = [f for f in __import__('os').listdir(REP) if f.endswith('_完整学习报告.docx')]
total = 0
for key, mp in JOBS:
    cands = [f for f in allf if key[:20] in f]
    if not cands:
        print("!! 未匹配到文件:", key[:35]); continue
    fn = cands[0]
    src = os.path.join(REP, fn)
    if APPLY:
        dst = os.path.join(BAK, fn)
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
    doc = Document(src)
    n = replace_all_runs(doc, mp)
    total += n
    tag = "[APPLY] " if APPLY else "[DRY] "
    print(tag + fn[:34] + "  %d 处替换" % n)
    for o, nv in mp.items():
        print("   %s → %s" % (o, nv))
    if APPLY and n:
        doc.save(src)

print("\n合计 %d 处" % total)
