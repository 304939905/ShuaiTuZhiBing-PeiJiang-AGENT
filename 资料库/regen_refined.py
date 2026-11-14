#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""重渲71份新精修(修复frame_ref连字符后), 直出覆盖到 报告库/<sub>/精编/。
跳过3份标杆视频。带数量护栏。
"""
import sys, importlib.util, traceback
from pathlib import Path

spec = importlib.util.spec_from_file_location("gen_refined", "D:/Desktop/shandou/资料库/gen_refined.py")
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

ROOT = Path("D:/Desktop/shandou/报告库")
SKIP = ["攻其篇—粉丝投稿解析", "神赏篇 来了! 评论投稿", "从零开始，宝物养成焚决"]
SUBPROJ = ["旧56项目", "开荒", "海之呼唤", "赛季"]

gen = skip = err = 0
targets = []  # 记录所有输出路径, 用于事后核对帧路径落地
for sub in SUBPROJ:
    src_dir = ROOT / sub / "逐帧1秒版"
    if not src_dir.exists():
        continue
    for src in sorted(src_dir.glob("*.docx")):
        if any(k in src.name for k in SKIP):
            skip += 1
            continue
        vt = src.name.replace("_逐帧深度学习报告_1秒版.docx", "")
        out = ROOT / sub / "精编" / f"{vt}_精修学习报告.docx"
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            sys.argv = ["gen_refined.py", str(src), str(out)]
            g.main()
            gen += 1
            targets.append(out)
        except Exception as e:
            err += 1
            print("ERR:", src.name, "->", repr(e))
            traceback.print_exc()

print(f"\nREGEN generated={gen} skipped={skip} errors={err}")
# 数量护栏
assert gen == 71, f"生成数异常 {gen} != 71"
assert err == 0, f"有错误 {err}"

# 事后核对: 全部71份的索引帧路径须用连字符, 且至少抽查首帧是否落地
import re, docx
hpat = re.compile(r"frame_(\d{4})_(\d{2})-(\d{2})\.jpg")
cpat = re.compile(r"frame_\d{4}_\d{2}:\d{2}\.jpg")
bad_colon = 0
checked_exist = 0
exist_ok = 0
for out in targets:
    txt = "\n".join(p.text for p in docx.Document(str(out)).paragraphs)
    idx = txt.rfind("溯源索引")
    tail = txt[idx:] if idx > 0 else ""
    if cpat.search(tail):
        bad_colon += 1
    # 取首条索引行, 测其 frame 路径落地
    m = re.search(r"\[\d\d:\d\d-\d\d:\d\d\]\s*(.+)", tail)
    if m:
        line = m.group(1).strip()
        hm = hpat.search(line)
        bmatch = re.match(r"(.+?)\s+frame_", line)
        if hm and bmatch:
            base = Path(bmatch.group(1).strip().rstrip("/"))
            cand = base / f"frame_{hm.group(1)}_{hm.group(2)}-{hm.group(3)}.jpg"
            checked_exist += 1
            if cand.exists():
                exist_ok += 1

print(f"帧路径核对: 冒号错误(应0)={bad_colon}  抽查首帧落地={exist_ok}/{checked_exist}")
