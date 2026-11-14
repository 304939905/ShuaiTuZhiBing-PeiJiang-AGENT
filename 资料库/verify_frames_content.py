#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内容层核验：检测纯色帧/损坏帧/重复帧/尺寸异常，并与源视频随机时间点做像素级比对。"""
import io
import os
import re
import json
import random
import ctypes
import numpy as np
import cv2
from PIL import Image

META = r'D:\Desktop\shandou\资料库\video_meta.json'
BASE = r'D:\Desktop\shandou\抖音_frames_dense_1s'
VID_ROOT = r'D:\Desktop\shandou'

random.seed(42)


def short_path(p):
    buf = ctypes.create_unicode_buffer(1024)
    if ctypes.windll.kernel32.GetShortPathNameW(p, buf, 1024):
        return buf.value
    return p


meta = json.load(io.open(META, encoding='utf-8'))
videos = meta['videos']

print("=" * 96)
print("抽帧内容层核验")
print("=" * 96)

# ---------- Part 1: 全量统计（尺寸/纯色/重复） ----------
print("\n[1] 全量帧统计：尺寸一致性 / 纯色帧 / 连续重复帧")
print("-" * 96)

sizes = {}
solid_frames = []      # 近乎纯色（std 很低）
dup_runs = []          # 连续完全相同的帧
corrupt = []
checked = 0

for v in videos:
    stem = os.path.splitext(v['rel_path'])[0].replace('/', os.sep)
    d = os.path.join(BASE, stem)
    if not os.path.isdir(d):
        continue
    files = sorted([f for f in os.listdir(d) if f.endswith('.jpg')],
                   key=lambda x: int(re.match(r'frame_(\d+)', x).group(1)))
    prev_hash = None
    run = 0
    max_run = 0
    n_solid = 0
    for f in files:
        p = os.path.join(d, f)
        try:
            with Image.open(p) as im:
                im.verify()
            with Image.open(p) as im:
                sizes[im.size] = sizes.get(im.size, 0) + 1
                g = np.asarray(im.convert('L').resize((64, 36)), dtype=np.float32)
        except Exception as e:
            corrupt.append((stem, f, str(e)[:50]))
            continue
        checked += 1
        if g.std() < 3.0:
            n_solid += 1
        h = hash(g.astype(np.uint8).tobytes())
        if h == prev_hash:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 0
        prev_hash = h
    if n_solid:
        solid_frames.append((stem, n_solid, len(files)))
    if max_run >= 5:
        dup_runs.append((stem, max_run + 1, len(files)))

print(f"  已校验帧数        : {checked}")
print(f"  损坏/无法解码     : {len(corrupt)}")
if corrupt:
    for c in corrupt[:10]:
        print(f"      {c}")
print(f"  分辨率分布        : {dict(sizes)}")
print(f"  含近纯色帧的视频  : {len(solid_frames)}")
for s in sorted(solid_frames, key=lambda x: -x[1])[:12]:
    print(f"      {s[1]:>3}/{s[2]:<4} 纯色帧  {s[0][:58]}")
print(f"  出现>=6连续相同帧 : {len(dup_runs)}")
for s in sorted(dup_runs, key=lambda x: -x[1])[:12]:
    print(f"      最长连重 {s[1]:>3} 帧 / 共{s[2]:<4}  {s[0][:55]}")

# ---------- Part 2: 抽样与源视频像素级比对 ----------
print("\n[2] 抽样回读源视频，逐帧像素比对（验证时间戳对齐是否正确）")
print("-" * 96)
sample_videos = random.sample(videos, 10)
ok_cnt = 0
fail = []
for v in sample_videos:
    rel = v['rel_path']
    stem = os.path.splitext(rel)[0].replace('/', os.sep)
    d = os.path.join(BASE, stem)
    sub = '开荒' if rel.startswith('开荒') else '抖音'
    vpath = os.path.join(VID_ROOT, '抖音', rel) if not rel.startswith('开荒') \
        else os.path.join(VID_ROOT, rel)
    if not os.path.exists(vpath):
        fail.append((rel, 'video not found: ' + vpath))
        continue
    cap = cv2.VideoCapture(short_path(vpath))
    if not cap.isOpened():
        fail.append((rel, 'cannot open video'))
        continue
    fps = cap.get(cv2.CAP_PROP_FPS)
    files = sorted([f for f in os.listdir(d) if f.endswith('.jpg')],
                   key=lambda x: int(re.match(r'frame_(\d+)', x).group(1)))
    picks = random.sample(files, min(3, len(files)))
    diffs = []
    for f in picks:
        m = re.match(r'frame_(\d+)_(\d{2})-(\d{2})\.jpg$', f)
        idx = int(m.group(1))
        tsec = int(m.group(2)) * 60 + int(m.group(3))
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(idx * fps)))
        ret, frame = cap.read()
        if not ret:
            diffs.append(('read_fail', idx))
            continue
        src = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        src = cv2.resize(src, (64, 36)).astype(np.float32)
        with Image.open(os.path.join(d, f)) as im:
            got = np.asarray(im.convert('L').resize((64, 36)), dtype=np.float32)
        mae = float(np.abs(src - got).mean())
        # timestamp consistency
        ts_ok = (tsec == idx)
        diffs.append((round(mae, 2), idx, ts_ok))
    cap.release()
    bad = [x for x in diffs if x[0] == 'read_fail' or (isinstance(x[0], float) and x[0] > 12)]
    status = "OK  " if not bad else "FAIL"
    if not bad:
        ok_cnt += 1
    else:
        fail.append((rel, diffs))
    print(f"  {status} MAE={[x[0] for x in diffs]}  {rel[:56]}")

print(f"\n  抽样通过: {ok_cnt}/{len(sample_videos)}  (MAE<=12 视为同一画面)")
if fail:
    print("  失败明细:")
    for f in fail:
        print("     ", f)

print("\n" + "=" * 96)
