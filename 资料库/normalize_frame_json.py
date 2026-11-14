# -*- coding: utf-8 -*-
"""校正 frame_json / zhenrong_frame_json 里的帧文件名：按帧序号在实际目录中查找真实文件名。
支持：帧目录在 抖音_frames_dense_1s/<frames_dir> 或 抖音_frames_dense_1s/阵容/<frames_dir>
用法: python normalize_frame_json.py [zhenrong|frame]
"""
import io, os, sys, json, re, glob
BASE = r"D:/Desktop/shandou"
TARGET = sys.argv[1] if len(sys.argv) > 1 else "frame"
FJ   = os.path.join(BASE, "资料库", "zhenrong_frame_json" if TARGET == "zhenrong" else "frame_json")
ROOT = os.path.join(BASE, "抖音_frames_dense_1s")

def frames_dir(name):
    for sub in ("", "阵容", "开荒"):
        p = os.path.join(ROOT, sub, name) if sub else os.path.join(ROOT, name)
        if os.path.isdir(p): return p
    return None

total_fix = total_miss = 0
for p in sorted(glob.glob(os.path.join(FJ, "*.json"))):
    d = json.load(io.open(p, encoding="utf-8"))
    fdir = frames_dir(d.get("frames_dir") or d.get("video_title", ""))
    if not fdir:
        print("NO DIR:", os.path.basename(p)); continue
    index = {}
    for f in os.listdir(fdir):
        m = re.match(r"frame_(\d+)_", f)
        if m: index[int(m.group(1))] = f
    fix = miss = 0
    for seg in d.get("timeline", []):
        for fr in seg.get("frames", []):
            fn = fr.get("file", "")
            if os.path.exists(os.path.join(fdir, fn)): continue
            m = re.match(r"frame_(\d+)_", fn)
            if m and int(m.group(1)) in index:
                fr["file"] = index[int(m.group(1))]; fix += 1
            else:
                miss += 1
    if fix or miss:
        print(f"{'FIX' if fix else '   '} {fix:>2}  MISS {miss:>2}  {os.path.basename(p)[:52]}")
    if fix:
        json.dump(d, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    total_fix += fix; total_miss += miss
print(f"\n合计 校正={total_fix}  仍缺失={total_miss}")
