import os, sys, glob, json, subprocess, time

BASE = "D:/Desktop/shandou/抖音"
OUT = "D:/Desktop/shandou/抖音_transcripts"
os.makedirs(OUT, exist_ok=True)

vids = sorted(glob.glob(os.path.join(BASE, "**", "*.mp4"), recursive=True))
print("TOTAL_VIDEOS:", len(vids), flush=True)

for i, vid in enumerate(vids, 1):
    rel = os.path.relpath(vid, BASE)
    stem = rel[:-4] if rel.lower().endswith(".mp4") else rel
    out_json = os.path.join(OUT, stem + ".json")
    if os.path.exists(out_json) and os.path.getsize(out_json) > 100:
        print(f"[{i}/{len(vids)}] SKIP (exists): {rel}", flush=True)
        continue

    print(f"[{i}/{len(vids)}] TRANSCRIBE: {rel}", flush=True)
    t0 = time.time()
    try:
        subprocess.run(
            [
                sys.executable,
                "D:/Desktop/shandou/资料库/transcribe.py",
                vid,
                out_json,
                "base",
            ],
            check=True,
            text=True,
        )
        dur = time.time() - t0
        # 读回 segs 数
        with open(out_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(
            f"[{i}/{len(vids)}] DONE in {dur:.1f}s: {rel} segs={len(data.get('segments', []))} dur={data.get('duration')}",
            flush=True,
        )
    except Exception as e:
        print(f"[{i}/{len(vids)}] FAIL: {rel} -> {e}", flush=True)

print("ALL_DONE", flush=True)
