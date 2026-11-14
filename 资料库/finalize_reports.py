#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""最终整合: 移动71新精修入精编/ + 删126冗余(非标杆精编+完整版)。带数量护栏。"""
import shutil, os, sys
from pathlib import Path

ROOT = Path("D:/Desktop/shandou/报告库")
SUB = ["旧56项目", "开荒", "海之呼唤", "赛季"]

# 动态识别3份标杆(精确文件名)
BENCH = set()
jd0 = ROOT / "旧56项目" / "精编"
for f in jd0.glob("*.docx"):
    if any(k in f.name for k in ["攻其篇—粉丝投稿解析", "神赏篇 来了! 评论投稿", "从零开始，宝物养成焚决"]):
        BENCH.add(f.name)
print("保留标杆:", BENCH)

# 计算移动列表
move_list = []
for sub in SUB:
    src = ROOT / "精修_新标" / sub
    if src.exists():
        for f in src.glob("*.docx"):
            move_list.append((f, ROOT / sub / "精编" / f.name))

# 计算删除列表
del_list = []
for sub in SUB:
    jd = ROOT / sub / "精编"
    if jd.exists():
        for f in jd.glob("*.docx"):
            if f.name.endswith("_精编学习报告.docx") and f.name not in BENCH:
                del_list.append(f)
    wb = ROOT / sub / "完整版"
    if wb.exists():
        for f in wb.glob("*.docx"):
            del_list.append(f)

print(f"计划: 移动={len(move_list)}  删除={len(del_list)}")
assert len(move_list) == 71, f"移动数异常 {len(move_list)} != 71"
assert len(del_list) == 126, f"删除数异常 {len(del_list)} != 126"

# 执行移动
moved = merr = 0
for src, dst in move_list:
    try:
        shutil.move(str(src), str(dst)); moved += 1
    except Exception as e:
        merr += 1; print("MOVE ERR", src.name, e)

# 执行删除
deleted = derr = 0
for f in del_list:
    try:
        os.remove(f); deleted += 1
    except Exception as e:
        derr += 1; print("DEL ERR", f.name, e)

# 删空目录(完整版)与暂存目录
for sub in SUB:
    wb = ROOT / sub / "完整版"
    try: wb.rmdir()
    except Exception: pass
try:
    shutil.rmtree(str(ROOT / "精修_新标"))
except Exception as e:
    print("cleanup err", e)

# 终态统计
print("\n=== 终态 ===")
for sub in SUB:
    jn = len(list((ROOT/sub/"精编").glob("*.docx")))
    sn = len(list((ROOT/sub/"逐帧1秒版").glob("*.docx")))
    print(f"{sub}: 精编={jn}  1秒版={sn}")
print(f"moved={moved} merr={merr} deleted={deleted} derr={derr} bench_kept={len(BENCH)}")
