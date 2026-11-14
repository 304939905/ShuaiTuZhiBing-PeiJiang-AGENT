#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Transcribe all 机制/ videos."""
import os, glob, subprocess, sys

ROOT = r"D:/Desktop/shandou/抖音/机制"
OUT_DIR = r"D:/Desktop/shandou/资料库/jizhi_transcripts"
PYTHON = r"C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
TRANSCRIBE = r"D:/Desktop/shandou/资料库/transcribe.py"

os.makedirs(OUT_DIR, exist_ok=True)

for mp4 in sorted(glob.glob(os.path.join(ROOT, "*.mp4"))):
    name = os.path.splitext(os.path.basename(mp4))[0]
    out_json = os.path.join(OUT_DIR, f"{name}.json")
    if os.path.exists(out_json):
        print(f"[SKIP] {name}")
        continue
    cmd = [PYTHON, TRANSCRIBE, mp4, out_json, "base"]
    env = os.environ.copy()
    env["PYTHONPATH"] = r"D:/WorkBuddyData/python-env/shandou/Lib/site-packages"
    print(f"[RUN] {name} -> {out_json}", flush=True)
    subprocess.run(cmd, env=env, check=False)

print("ALL_DONE")
