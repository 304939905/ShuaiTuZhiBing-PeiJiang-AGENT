#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最终核验：全分辨率 + 流式顺序解码基准（低内存），判定抽帧时间戳精度。"""
import io
import os
import re
import sys
import json
import random
import ctypes
import numpy as np
import cv2

META = r'D:\Desktop\shandou\资料库\video_meta.json'
BASE = r'D:\Desktop\shandou\抖音_frames_dense_1s'
VID_ROOT = r'D:\Desktop\shandou'
random.seed(7)
WIN = 3  # 允许比对的偏移窗口（帧）


def short_path(p):
    buf = ctypes.create_unicode_buffer(1024)
    if ctypes.windll.kernel32.GetShortPathNameW(p, buf, 1024):
        return buf.value
    return p


def imread_u(p):
    return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)


def check_one(rel, n_pick=5, max_sec_limit=88):
    """流式顺序解码，只在目标帧附近保留画面，逐个比对。"""
    stem = os.path.splitext(rel)[0].replace('/', os.sep)
    d = os.path.join(BASE, stem)
    vpath = os.path.join(VID_ROOT, '抖音', rel) if not rel.startswith('开荒') \
        else os.path.join(VID_ROOT, rel)
    if not os.path.isdir(d) or not os.path.exists(vpath):
        return None, [(rel, 'path missing')]

    files = sorted([f for f in os.listdir(d) if f.endswith('.jpg')],
                   key=lambda x: int(re.match(r'frame_(\d+)', x).group(1)))
    cand = [f for f in files if int(re.match(r'frame_(\d+)', f).group(1)) <= max_sec_limit]
    if len(cand) < n_pick:
        cand = files[:n_pick]
    if not cand:
        return None, [(rel, 'no frames')]
    picks = sorted(random.sample(cand, min(n_pick, len(cand))),
                   key=lambda x: int(re.match(r'frame_(\d+)', x).group(1)))

    cap = cv2.VideoCapture(short_path(vpath))
    if not cap.isOpened():
        return None, [(rel, 'cannot open')]
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    # 目标帧号 -> 保存的图
    targets = {}
    for f in picks:
        sec = int(re.match(r'frame_(\d+)', f).group(1))
        targets[int(round(sec * fps))] = f

    want = sorted(targets)
    last_need = want[-1] + WIN
    # 每个 target 收集 [target-WIN, target+WIN] 的帧
    collected = {t: {} for t in want}
    i = 0
    while i <= last_need:
        ok, fr = cap.read()
        if not ok:
            break
        for t in want:
            if abs(i - t) <= WIN:
                collected[t][i] = fr
        i += 1
    cap.release()

    res = []
    probs = []
    for t in want:
        f = targets[t]
        saved = imread_u(os.path.join(d, f))
        best, bo = 1e9, None
        for j, fr in collected[t].items():
            if fr.shape != saved.shape:
                continue
            m = float(np.abs(fr.astype(np.float32) - saved.astype(np.float32)).mean())
            if m < best:
                best, bo = m, j - t
        if bo is None:
            probs.append((rel, f'{f} 无可比对帧'))
            continue
        res.append((f, bo, best))
        if bo != 0 or best > 5:
            probs.append((rel, f"{f} 偏移{bo:+d}帧 MAE={best:.2f}"))
    return (fps, res), probs


def main():
    meta = json.load(io.open(META, encoding='utf-8'))
    videos = meta['videos']
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    sample = random.sample(videos, min(n, len(videos)))

    print("=" * 100)
    print(f"最终核验：全分辨率 + 流式顺序解码基准（{len(sample)} 个随机视频 × 每个 5 帧）")
    print("=" * 100)
    print(f"{'状态':<6}{'帧':>4}{'偏移0':>7}{'均MAE':>8}{'максMAE':>9}  视频")
    print("-" * 100)

    tot = zero = 0
    all_mae = []
    problems = []
    for v in sample:
        r, p = check_one(v['rel_path'])
        problems.extend(p)
        if not r:
            continue
        fps, res = r
        if not res:
            continue
        maes = [x[2] for x in res]
        z = sum(1 for x in res if x[1] == 0)
        tot += len(res)
        zero += z
        all_mae.extend(maes)
        flag = "OK" if (z == len(res) and max(maes) < 5) else "WARN"
        print(f"{flag:<6}{len(res):>4}{z:>7}{np.mean(maes):>8.2f}{max(maes):>9.2f}  {v['rel_path'][:50]}")

    print("-" * 100)
    print(f"合计: 检查 {tot} 帧，时间戳偏移为 0 的 {zero} 帧 ({100*zero/max(tot,1):.1f}%)")
    if all_mae:
        print(f"      全分辨率 MAE 平均 {np.mean(all_mae):.2f} / 最大 {max(all_mae):.2f}"
              f"   （JPEG 有损压缩基线约 0.5~2，越小越好）")
    if problems:
        print(f"\n异常 {len(problems)} 项：")
        for x in problems[:15]:
            print("   ", x)
    else:
        print("\n无异常：抽查帧全部时间戳精确，画面与源视频逐像素一致（仅 JPEG 压缩差异）。")
    print("=" * 100)


if __name__ == '__main__':
    main()
