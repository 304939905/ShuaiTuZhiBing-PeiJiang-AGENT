#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""赛季视频专属：1 秒/帧全量抽帧。"""
import os, glob, cv2, ctypes
from ctypes import wintypes

ROOT = r"D:/Desktop/shandou/抖音/赛季"
OUT_BASE = r"D:/Desktop/shandou/赛季_frames_dense_1s"
STEP = 1.0

def short_path(p):
    buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
    ctypes.windll.kernel32.GetShortPathNameW(p, buf, wintypes.MAX_PATH)
    return buf.value

def extract(mp4, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    existing = glob.glob(os.path.join(out_dir, "frame_*.jpg"))
    if existing:
        return len(existing), True, 0.0
    vc = cv2.VideoCapture(short_path(mp4))
    if not vc.isOpened():
        print(f"OPEN_FAIL {mp4}")
        return 0, False, 0.0
    fps = vc.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(vc.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total / fps if fps else 0
    idx = 0
    while True:
        ret, frame = vc.read()
        if not ret:
            break
        if idx % max(1, int(round(fps * STEP))) == 0:
            ts = idx / fps
            fn = f"frame_{idx:04d}_{int(ts)//60:02d}-{int(ts)%60:02d}.jpg"
            # NOTE: cv2.imwrite 在当前环境无法写入 D: 盘（后端权限问题），
            # 改用 cv2.imencode + 普通文件写入（已验证可用）。
            ok, buf = cv2.imencode(".jpg", frame)
            if ok:
                with open(os.path.join(out_dir, fn), "wb") as _f:
                    _f.write(buf.tobytes())
        idx += 1
    vc.release()
    written = len(glob.glob(os.path.join(out_dir, "frame_*.jpg")))
    return written, False, duration

if __name__ == "__main__":
    mp4s = sorted(glob.glob(os.path.join(ROOT, "*.mp4")))
    print(f"[赛季] {len(mp4s)} videos")
    ok = fail = 0
    for m in mp4s:
        name = os.path.splitext(os.path.basename(m))[0]
        d = os.path.join(OUT_BASE, name)
        n, skip, dur = extract(m, d)
        status = "SKIP" if skip else f"{n}帧"
        print(f"  {name}  {status}  {dur:.1f}s")
        if n > 0: ok += 1
        else: fail += 1
    total_f = sum(len(glob.glob(os.path.join(d, "frame_*.jpg")))
                 for d in glob.glob(os.path.join(OUT_BASE, "*")) if os.path.isdir(d))
    print(f"\n合计 {ok}成功 {fail}失败  总帧{total_f}")
