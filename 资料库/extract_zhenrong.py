# -*- coding: utf-8 -*-
"""仅对 抖音/阵容/ 22 视频做 1秒/帧密集抽帧（Phase B 新批前置）。"""
import os, sys
sys.path.insert(0, r'D:/Desktop/shandou/资料库')
import extract_frames_1s as E

ROOT = r'D:/Desktop/shandou/抖音'
SRC = os.path.join(ROOT, '阵容')
OUT_BASE = r'D:/Desktop/shandou/抖音_frames_dense_1s'

res = E.process_folder(SRC, OUT_BASE)
total = 0
for name, n, skipped in res:
    total += n
    print(f"{'[SKIP]' if skipped else '[DONE]'} {name}: {n} frames", flush=True)
print(f"ZHENRONG_TOTAL_FRAMES={total}", flush=True)
