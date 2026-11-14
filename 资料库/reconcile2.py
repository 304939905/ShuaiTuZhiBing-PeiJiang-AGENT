#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""精确三向对账: 按子目录分类的视频 vs 静帧目录 vs 1秒版 vs 精编。"""
import re
from pathlib import Path

ROOT = Path("D:/Desktop/shandou")

def norm(s):
    return re.sub(r"[\s\W_]+", "", s, flags=re.UNICODE).lower()

# 1 视频: 抖音/根=旧56, 抖音/开荒, 抖音/海之呼唤, 抖音/赛季, 抖音/机制, 抖音/阵容
video_groups = {}
for sub_dir, cat in [(None, "旧56"), ("开荒", "开荒"), ("海之呼唤", "海之呼唤"),
                     ("赛季", "赛季"), ("机制", "机制"), ("阵容", "阵容")]:
    d = ROOT / "抖音" / sub_dir if sub_dir else ROOT / "抖音"
    names = [p.stem for p in d.glob("*.mp4")] if d.exists() else []
    video_groups[cat] = {norm(n): n for n in names}
print("视频数:", {k: len(v) for k, v in video_groups.items()})

# 2 静帧目录
frame_groups = {"旧56": {}, "开荒": {}, "海之呼唤": {}, "赛季": {}}
for fr, cats in [("抖音_frames_dense_1s", ["旧56", "开荒"]), ("海之呼唤_frames_dense_1s", ["海之呼唤"]),
                 ("赛季_frames_dense_1s", ["赛季"])]:
    d = ROOT / fr
    if d.exists():
        for sub in d.iterdir():
            if not sub.is_dir() or "contact_sheets" in sub.name or sub.name.startswith("_"):
                continue
            if fr == "抖音_frames_dense_1s":
                if sub.name == "开荒":
                    cat = "开荒"
                elif sub.name.startswith("video_") or sub.name.startswith("_deprecated"):
                    continue
                else:
                    cat = "旧56"
            else:
                cat = cats[0]
            frame_groups.setdefault(cat, {})[norm(sub.name)] = sub.name
print("静帧目录数:", {k: len(v) for k, v in frame_groups.items()})

# 3 报告
rep_groups = {"旧56项目": {}, "开荒": {}, "海之呼唤": {}, "赛季": {}}
for sub in rep_groups:
    for layer in ("逐帧1秒版", "精编"):
        d = ROOT / "报告库" / sub / layer
        if d.exists():
            for f in d.glob("*.docx"):
                key = norm(f.stem.replace("_逐帧深度学习报告_1秒版", "").replace("_精修学习报告", ""))
                rep_groups[sub].setdefault(layer, {})[key] = f.name

print("\n=== 各子项目: 视频 / 静帧 / 1秒版 / 精编 ===")
mapping = [("旧56项目", "旧56"), ("开荒", "开荒"), ("海之呼唤", "海之呼唤"), ("赛季", "赛季")]
for rep_sub, vcat in mapping:
    vn = len(video_groups.get(vcat, {}))
    fn = len(frame_groups.get(vcat, {}))
    r1 = len(rep_groups[rep_sub].get("逐帧1秒版", {}))
    r2 = len(rep_groups[rep_sub].get("精编", {}))
    print(f"  {rep_sub}: 视频={vn} 静帧={fn} 1秒版={r1} 精编={r2}")

print("\n=== 缺失检查 ===")
for rep_sub, vcat in mapping:
    vmap = video_groups.get(vcat, {})
    fmap = frame_groups.get(vcat, {})
    p1 = rep_groups[rep_sub].get("逐帧1秒版", {})
    p2 = rep_groups[rep_sub].get("精编", {})
    # 视频有但无精编
    for k, nm in sorted(vmap.items(), key=lambda x: x[1]):
        if k not in p2:
            print(f"  [视频无精编] {rep_sub}: {nm[:45]}")
    # 精编有但无视频
    for k, nm in p2.items():
        if k not in vmap:
            print(f"  [精编无视频] {rep_sub}: {nm[:45]}")
    # 精编有但无静帧
    for k, nm in p2.items():
        if k not in fmap:
            print(f"  [精编无静帧] {rep_sub}: {nm[:45]}")
    # 静帧有但无精编
    for k, nm in sorted(fmap.items(), key=lambda x: x[1]):
        if k not in p2:
            print(f"  [静帧无精编] {rep_sub}: {nm[:45]}")
print("(若以上各区均无输出 = 该区 1:1 完全对齐)")

print("\n=== 阵容/机制(非旧一批, 仅统计) ===")
print("  阵容视频:", len(video_groups.get("阵容", {})))
print("  机制视频:", len(video_groups.get("机制", {})))
zj = ROOT / "报告库" / "阵容新批" / "精编"
print("  阵容新批精编:", len(list(zj.glob("*.docx"))) if zj.exists() else 0)
