#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量生成新精修: 遍历全部1秒版, 跳过3份标杆视频, 生成到其他 71 份。
输出: 报告库/精修_新标/<子项目>/<视频名>_精修学习报告.docx
"""
import sys, importlib.util, traceback
from pathlib import Path

spec = importlib.util.spec_from_file_location("gen_refined", "D:/Desktop/shandou/资料库/gen_refined.py")
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

ROOT = Path("D:/Desktop/shandou/报告库")
OUT = Path("D:/Desktop/shandou/报告库/精修_新标")

# 跳过3份标杆视频对应的1秒版
SKIP = ["攻其篇—粉丝投稿解析", "神赏篇 来了! 评论投稿", "从零开始，宝物养成焚决"]

SUBPROJ = ["旧56项目", "开荒", "海之呼唤", "赛季"]

gen = 0
skip = 0
err = 0
for sub in SUBPROJ:
    src_dir = ROOT / sub / "逐帧1秒版"
    if not src_dir.exists():
        continue
    for src in sorted(src_dir.glob("*.docx")):
        if any(k in src.name for k in SKIP):
            print("SKIP(benchmark):", src.name)
            skip += 1
            continue
        vt = src.name.replace("_逐帧深度学习报告_1秒版.docx", "")
        out = OUT / sub / f"{vt}_精修学习报告.docx"
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            sys.argv = ["gen_refined.py", str(src), str(out)]
            g.main()
            gen += 1
        except Exception as e:
            err += 1
            print("ERR:", src.name, "->", repr(e))
            traceback.print_exc()

print(f"\nDONE generated={gen} skipped={skip} errors={err}")
