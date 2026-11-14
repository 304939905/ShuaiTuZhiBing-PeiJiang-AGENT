#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用顺序解码（ground truth）验证 seek 抽帧的时间戳偏移量。

顺序解码是确定性的：逐帧 read()，第 round(t*fps) 帧即为第 t 秒的真实画面。
将保存的帧与顺序解码得到的候选帧窗口比对，找出最佳匹配位置，得出实际偏移。
"""
import io
import os
import re
import json
import ctypes
import numpy as np
import cv2
from PIL import Image

META = r'D:\Desktop\shandou\资料库\video_meta.json'
BASE = r'D:\Desktop\shandou\抖音_frames_dense_1s'
VID_ROOT = r'D:\Desktop\shandou'


def short_path(p):
    buf = ctypes.create_unicode_buffer(1024)
    if ctypes.windll.kernel32.GetShortPathNameW(p, buf, 1024):
        return buf.value
    return p


def sig(gray):
    return cv2.resize(gray, (64, 36)).astype(np.float32)


def check_video(rel, max_probe_sec=60, window=45):
    """顺序解码前 max_probe_sec 秒，对每个整秒帧找最佳匹配偏移。"""
    stem = os.path.splitext(rel)[0].replace('/', os.sep)
    d = os.path.join(BASE, stem)
    vpath = os.path.join(VID_ROOT, '抖音', rel) if not rel.startswith('开荒') \
        else os.path.join(VID_ROOT, rel)
    if not os.path.isdir(d) or not os.path.exists(vpath):
        return None

    cap = cv2.VideoCapture(short_path(vpath))
    if not cap.isOpened():
        return None
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    # 顺序解码，缓存前 N 秒所有帧的签名
    need = int(max_probe_sec * fps) + window + 5
    seq = []
    while len(seq) < need:
        ok, fr = cap.read()
        if not ok:
            break
        seq.append(sig(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)))
    cap.release()
    if not seq:
        return None

    files = sorted([f for f in os.listdir(d) if f.endswith('.jpg')],
                   key=lambda x: int(re.match(r'frame_(\d+)', x).group(1)))
    offsets = []
    for f in files:
        idx = int(re.match(r'frame_(\d+)', f).group(1))
        if idx > max_probe_sec:
            break
        target = int(round(idx * fps))
        lo = max(0, target - window)
        hi = min(len(seq), target + window + 1)
        if lo >= hi:
            continue
        with Image.open(os.path.join(d, f)) as im:
            got = np.asarray(im.convert('L').resize((64, 36)), dtype=np.float32)
        best, best_mae = None, 1e9
        for j in range(lo, hi):
            mae = float(np.abs(seq[j] - got).mean())
            if mae < best_mae:
                best_mae, best = mae, j
        offsets.append((idx, best - target, round(best_mae, 2)))
    return fps, offsets


meta = json.load(io.open(META, encoding='utf-8'))
videos = meta['videos']

targets = [
    '全新垒实体系震撼来袭！ 杜垒司见过没，杜预也能走垒实？.mp4',
    '全率土最全入门攻略合集!  来了!.mp4',
    '配将焚决来了 全体系队伍搭建思路最后一期，真焚决—宏观配将法，来了! 跟合集内容全部融会贯通，你也能成配将大手子!.mp4',
    '开荒\\关妹甄洛严颜开荒实录！ 翻车翻炸了咋补救？接着看！.mp4',
    '粉丝赞不绝口的队伍来咯！ 感谢粉丝分享！.mp4',
]

print("=" * 96)
print("seek 抽帧时间戳精度核验（以顺序解码为基准）")
print("=" * 96)
print("偏移单位 = 视频帧（30fps 时 30 帧 = 1 秒）。偏移 0 表示时间戳完全精确。\n")

all_off = []
for rel in targets:
    r = check_video(rel)
    if r is None:
        print(f"[跳过] {rel[:60]}")
        continue
    fps, offs = r
    if not offs:
        continue
    o = np.array([x[1] for x in offs], dtype=float)
    m = np.array([x[2] for x in offs], dtype=float)
    all_off.extend(o.tolist())
    matched = (m < 6).sum()
    print(f"{rel[:62]}")
    print(f"   fps={fps:.2f}  抽样整秒帧={len(offs)}  可靠匹配={matched}/{len(offs)}")
    print(f"   偏移: 均值={o.mean():+.1f}帧 ({o.mean()/fps:+.2f}s)  中位={np.median(o):+.0f}帧  "
          f"最大|偏移|={np.abs(o).max():.0f}帧 ({np.abs(o).max()/fps:.2f}s)")
    big = [(x[0], x[1], x[2]) for x in offs if abs(x[1]) > fps * 0.5]
    print(f"   偏移超过0.5秒的帧: {len(big)}/{len(offs)}", end='')
    if big:
        print(f"   例: " + ", ".join(f"F{a}偏{b:+d}帧" for a, b, c in big[:6]))
    else:
        print()
    print()

if all_off:
    a = np.abs(np.array(all_off))
    print("-" * 96)
    print(f"总体: 样本={len(a)}  平均|偏移|={a.mean():.1f}帧  "
          f"<=1帧占比={100*(a<=1).mean():.1f}%  <=15帧(0.5s)占比={100*(a<=15).mean():.1f}%  "
          f"最大={a.max():.0f}帧")
print("=" * 96)
