#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract 1fps frames for 机制/ videos only."""
import os, glob, cv2, ctypes
from ctypes import wintypes

ROOT = r"D:/Desktop/shandou/抖音/机制"
OUT_BASE = r"D:/Desktop/shandou/抖音_frames_dense_1s/机制"
STEP = 1.0


def short_path(p):
    buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
    ctypes.windll.kernel32.GetShortPathNameW(p, buf, wintypes.MAX_PATH)
    return buf.value


def extract(mp4, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    existing = glob.glob(os.path.join(out_dir, "frame_*.jpg"))
    if existing:
        return len(existing), True
    vc = cv2.VideoCapture(short_path(mp4))
    if not vc.isOpened():
        print(f"OPEN_FAIL {mp4}")
        return 0, False
    fps = vc.get(cv2.CAP_PROP_FPS) or 30.0
    total = vc.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = total / fps if fps else 0
    saved = 0
    t = 0.0
    while t <= duration:
        frame_idx = int(t * fps)
        vc.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ok, img = vc.read()
        if not ok:
            break
        fn = os.path.join(out_dir, f"frame_{saved:04d}_{int(t//60):02d}-{int(t%60):02d}.jpg")
        ok, buf = cv2.imencode(".jpg", img)
        open(fn, "wb").write(buf.tobytes())
        saved += 1
        t += STEP
    vc.release()
    return saved, False


if __name__ == "__main__":
    all_results = []
    for mp4 in sorted(glob.glob(os.path.join(ROOT, "*.mp4"))):
        name = os.path.splitext(os.path.basename(mp4))[0]
        out_dir = os.path.join(OUT_BASE, name)
        n, skipped = extract(mp4, out_dir)
        all_results.append((name, n, skipped))
    for name, n, skipped in all_results:
        print(f"{'[SKIP]' if skipped else '[DONE]'} {name}: {n} frames")
    total = sum(n for _, n, _ in all_results)
    print(f"TOTAL_FRAMES={total}")
