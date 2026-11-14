#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""三向对账: 源视频 vs 静帧目录 vs 1秒版 vs 精编。找出缺失/多余。"""
import re
from pathlib import Path

ROOT = Path("D:/Desktop/shandou")

def norm(s):
    return re.sub(r"[\s\W_]+", "", s, flags=re.UNICODE).lower()

def files_of(d, ext):
    return [p.stem for p in d.glob("*." + ext)] if d.exists() else []

# 1 源视频
video_map = {}  # norm -> (类别, 原始名)
srcs = [
    ("旧56(抖音根)", ROOT / "抖音", "mp4"),
    ("开荒", ROOT / "开荒", "mp4"),
    ("海之呼唤", ROOT / "海之呼唤", "mp4"),
    ("赛季", ROOT / "赛季", "mp4"),
]
for cat, d, ext in srcs:
    if d.exists():
        for f in d.glob("*." + ext):
            video_map[norm(f.stem)] = (cat, f.stem)
print("源视频总数:", len(video_map))

# 2 静帧目录
frame_map = {}
for fr, cat in [("抖音_frames_dense_1s", "旧56/开荒"), ("海之呼唤_frames_dense_1s", "海之呼唤"), ("赛季_frames_dense_1s", "赛季")]:
    d = ROOT / fr
    if d.exists():
        for sub in d.iterdir():
            if sub.is_dir():
                frame_map[norm(sub.name)] = (fr, sub.name)
print("静帧目录总数:", len(frame_map))

# 3 报告(1秒版 + 精编) 按子项目
rep_map = {"旧56项目": {}, "开荒": {}, "海之呼唤": {}, "赛季": {}}
for sub in rep_map:
    for layer in ("逐帧1秒版", "精编"):
        d = ROOT / "报告库" / sub / layer
        if d.exists():
            for f in d.glob("*.docx"):
                key = norm(f.name.replace("_逐帧深度学习报告_1秒版", "").replace("_精修学习报告", ""))
                rep_map[sub].setdefault(layer, {})[key] = f.name

print("\n=== 各子项目报告数 ===")
for sub, layers in rep_map.items():
    n1 = len(layers.get("逐帧1秒版", {}))
    n2 = len(layers.get("精编", {}))
    print(f"  {sub}: 1秒版={n1} 精编={n2}")

# 4 对账: 精编 ↔ 源视频
print("\n=== 对账: 精编 vs 源视频 ===")
for sub, layers in rep_map.items():
    if "精编" not in layers:
        continue
    for key, fname in layers["精编"].items():
        if key not in video_map:
            print(f"  [精编无对应视频?] {sub}: {fname[:40]}")
print("(以上为空则精编全部有对应源视频)")

# 5 对账: 源视频 缺 精编
print("\n=== 对账: 源视频 无 精编 ===")
for key, (cat, vname) in sorted(video_map.items(), key=lambda x: x[1]):
    has = any(key in layers.get("精编", {}) for layers in rep_map.values())
    if not has:
        print(f"  [视频无精编] {cat}: {vname[:45]}")
print("(以上为空则所有视频都有精编)")

# 6 对账: 精编 缺 静帧目录
print("\n=== 对账: 精编 vs 静帧目录 ===")
for sub, layers in rep_map.items():
    if "精编" not in layers:
        continue
    for key, fname in layers["精编"].items():
        if key not in frame_map:
            print(f"  [精编无静帧目录?] {sub}: {fname[:40]}")
print("(以上为空则精编全部有静帧目录)")

# 7 对账: 静帧目录 无 精编
print("\n=== 对账: 静帧目录 无 精编 ===")
for key, (fr, dname) in sorted(frame_map.items(), key=lambda x: x[1][1]):
    if "contact_sheets" in dname or dname.startswith("_"):
        continue
    has = any(key in layers.get("精编", {}) for layers in rep_map.values())
    if not has:
        print(f"  [静帧无精编] {fr}: {dname[:45]}")
print("(以上为空则所有静帧目录都有精编)")
