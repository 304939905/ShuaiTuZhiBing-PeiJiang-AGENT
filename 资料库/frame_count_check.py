#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""核对: 每个视频的静帧数 vs 视频时长(秒), 允许误差 ±2。
视频来源: 抖音/根(50) 抖音/开荒(6) 抖音/海之呼唤(19) 抖音/赛季(4) = 79
"""
import re, ctypes
from pathlib import Path
import cv2

ROOT = Path("D:/Desktop/shandou")

def norm(s):
    return re.sub(r"[\s\W_]+", "", s, flags=re.UNICODE).lower()

def short_path(p):
    """中文路径转 8.3 短路径(规避 opencv 读中文失败)。"""
    buf = ctypes.create_unicode_buffer(512)
    if ctypes.windll.kernel32.GetShortPathNameW(str(p), buf, 512):
        return buf.value
    return str(p)

def video_duration_sec(mp4):
    cap = cv2.VideoCapture(short_path(mp4))
    if not cap.isOpened():
        return None
    fps = cap.get(cv2.CAP_PROP_FPS)
    n = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    if not fps or not n:
        return None
    return round(n / fps)

# 视频 -> (类别, 帧目录)
groups = [
    ("旧56", ROOT / "抖音", ROOT / "抖音_frames_dense_1s"),
    ("开荒", ROOT / "抖音" / "开荒", ROOT / "抖音_frames_dense_1s" / "开荒"),
    ("海之呼唤", ROOT / "抖音" / "海之呼唤", ROOT / "海之呼唤_frames_dense_1s"),
    ("赛季", ROOT / "抖音" / "赛季", ROOT / "赛季_frames_dense_1s"),
]

rows = []
for cat, vdir, froot in groups:
    if not vdir.exists():
        print(f"[{cat}] 视频目录缺失: {vdir}")
        continue
    for mp4 in sorted(vdir.glob("*.mp4")):
        dur = video_duration_sec(mp4)
        # 帧目录 = froot/<视频名>
        fdir = froot / mp4.stem
        if cat == "开荒":
            # 开荒帧在 抖音_frames_dense_1s/开荒/<视频名>/
            pass
        if fdir.exists():
            n_jpg = len([f for f in fdir.glob("*.jpg") if "contact_sheets" not in str(f)])
        else:
            n_jpg = -1
        rows.append((cat, mp4.stem, dur, n_jpg))

print(f"{'类别':<6}{'帧数':<6}{'时长秒':<6}{'差值':<6}状态")
print("-" * 70)
bad = []
for cat, name, dur, n in rows:
    if dur is None:
        status = "时长读取失败"
    elif n == -1:
        status = "帧目录缺失"
    elif abs(n - dur) <= 2:
        status = "OK"
    else:
        status = f"异常(差{abs(n-dur)})"
    if status != "OK":
        bad.append((cat, name, dur, n, status))
    print(f"{cat:<6}{str(n):<6}{str(dur):<6}{str(n-dur if n>=0 and dur else '?'):<6}{status}  {name[:34]}")

print(f"\n共 {len(rows)} 视频, 异常 {len(bad)}:")
for cat, name, dur, n, status in bad:
    print(f"  [{cat}] {name[:44]} 时长={dur}s 帧数={n} {status}")
