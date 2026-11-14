#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""赛季视频专属：批量 faster-whisper 中文转写（base / CPU int8）。"""
import os, glob, subprocess

SRC = r"D:/Desktop/shandou/抖音/赛季"
OUT = r"D:/Desktop/shandou/赛季_transcripts"
TRANSCRIBE = r"D:/Desktop/shandou/资料库/transcribe.py"
PY = r"C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"

os.makedirs(OUT, exist_ok=True)

def main():
    vids = sorted(glob.glob(os.path.join(SRC, "*.mp4")))
    print(f"VIDEOS={len(vids)}", flush=True)
    done = skip = fail = 0
    for i, v in enumerate(vids, 1):
        base = os.path.splitext(os.path.basename(v))[0]
        oj = os.path.join(OUT, base + ".json")
        if os.path.exists(oj) and os.path.getsize(oj) > 100:
            print(f"[{i}/{len(vids)}] SKIP {base}", flush=True)
            skip += 1
            continue
        print(f"[{i}/{len(vids)}] TRANSCRIBE {base}", flush=True)
        try:
            subprocess.run([PY, TRANSCRIBE, v, oj, "base"], check=True)
            done += 1
        except Exception as e:
            print(f"  FAIL {base}: {e}", flush=True)
            fail += 1
    print(f"\nDONE done={done} skip={skip} fail={fail}")

if __name__ == "__main__":
    main()
