#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""精细诊断：单帧像素级比对，判断 MAE 偏高来自时间错位还是编码差异。"""
import os
import re
import ctypes
import numpy as np
import cv2
from PIL import Image

BASE = r'D:\Desktop\shandou\抖音_frames_dense_1s'
VID = r'D:\Desktop\shandou\抖音\配将焚决来了 全体系队伍搭建思路最后一期，真焚决—宏观配将法，来了! 跟合集内容全部融会贯通，你也能成配将大手子!.mp4'
DIR = os.path.join(BASE, os.path.splitext(os.path.basename(VID))[0])


def short_path(p):
    buf = ctypes.create_unicode_buffer(1024)
    if ctypes.windll.kernel32.GetShortPathNameW(p, buf, 1024):
        return buf.value
    return p


cap = cv2.VideoCapture(short_path(VID))
fps = cap.get(cv2.CAP_PROP_FPS)
print(f"fps={fps}")

# 顺序解码前 70 秒
seq = []
while len(seq) < int(70 * fps):
    ok, fr = cap.read()
    if not ok:
        break
    seq.append(fr)
cap.release()
print(f"顺序解码帧数={len(seq)}\n")

print(f"{'秒':>4} {'目标帧':>7} | {'全分辨率MAE':>11} {'均值差':>8} {'完全相同':>8} | {'±3帧内最小MAE':>13} {'最佳偏移':>8}")
print("-" * 92)

for sec in [1, 5, 10, 23, 40, 55, 59]:
    f = None
    for name in os.listdir(DIR):
        if re.match(rf'frame_0*{sec}_', name):
            f = name
            break
    if not f:
        continue
    saved = cv2.imdecode(np.fromfile(os.path.join(DIR, f), dtype=np.uint8), cv2.IMREAD_COLOR)
    target = int(round(sec * fps))
    if target >= len(seq):
        continue
    src = seq[target]
    if src.shape != saved.shape:
        print(f"{sec:>4} 形状不一致 src={src.shape} saved={saved.shape}")
        continue
    d = np.abs(src.astype(np.float32) - saved.astype(np.float32))
    mae = d.mean()
    meandiff = (src.astype(np.float32) - saved.astype(np.float32)).mean()
    identical = np.array_equal(src, saved)

    best, bo = 1e9, None
    for off in range(-3, 4):
        j = target + off
        if 0 <= j < len(seq) and seq[j].shape == saved.shape:
            m = np.abs(seq[j].astype(np.float32) - saved.astype(np.float32)).mean()
            if m < best:
                best, bo = m, off
    print(f"{sec:>4} {target:>7} | {mae:>11.2f} {meandiff:>8.2f} {str(identical):>8} | {best:>13.2f} {bo:>+8d}")

print("\n说明：JPEG 有损压缩基线 MAE 通常 1~4；若最佳偏移为 0 且 MAE 接近基线，则时间戳精确。")
