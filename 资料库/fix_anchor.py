#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修正心愿武将 1秒版 + 精编 的时间锚错位: 规则截图行 00:05 -> 00:09"""
import docx, sys
from pathlib import Path

ROOT = Path("D:/Desktop/shandou/报告库")
APPLY = "--apply" in sys.argv

targets = [
    (ROOT / "旧56项目" / "逐帧1秒版" / "一篇看懂心愿武将所有细节 多少玉一张保底，积分能否保留？一篇全看懂_逐帧深度学习报告_1秒版.docx",
     "00:05 官方规则原文截图", "00:09 官方规则原文截图"),
    (ROOT / "旧56项目" / "精编" / "一篇看懂心愿武将所有细节 多少玉一张保底，积分能否保留？一篇全看懂_精修学习报告.docx",
     "[00:05] 官方规则原文截图", "[00:09] 官方规则原文截图"),
]

for f, old, new in targets:
    if not f.exists():
        print("缺失:", f.name)
        continue
    doc = docx.Document(str(f))
    hit = 0
    for p in doc.paragraphs:
        if p.text.strip().startswith(old):
            if p.runs:
                # 前缀可能拆在多个 run, 整段重写第一个 run
                new_text = p.text.replace(old, new, 1)
                p.runs[0].text = new_text
                for r in p.runs[1:]:
                    r.text = ""
            else:
                p.add_run(p.text.replace(old, new, 1))
            hit += 1
            print(f"  [{f.parent.name}] 命中并替换: {old} -> {new}")
    if hit == 0:
        print(f"  [未命中!] {f.parent.name}: {old}")
    if APPLY and hit:
        doc.save(str(f))
        print(f"  [已保存] {f.name[:40]}")
print("[干跑]" if not APPLY else "[完成]")
