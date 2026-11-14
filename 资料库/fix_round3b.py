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

JOBS = [
    ("徐庶能玩吗？ 当然可以，平民极佳的战磐选择，来了！_逐帧深度学习报告_1秒版.docx",
     {"奇策与目标距离": "奇袭与目标距离",
      "奇策距离增伤": "奇袭距离增伤",
      "英务造成攻击伤害": "英勇造成攻击伤害",
      "英务追击战法发动率": "英勇追击战法发动率"}),
]
for fn, mp in JOBS:
    src = os.path.join(REP, fn)
    if not os.path.exists(src):
        print("MISS", fn); continue
    if APPLY:
        dst = os.path.join(BAK, fn)
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
    doc = Document(src)
    n = replace_all_runs(doc, mp)
    print(("[APPLY] " if APPLY else "[DRY] ") + fn[:30] + " 替换 %d 次" % n)
    if APPLY and n:
        doc.save(src)
