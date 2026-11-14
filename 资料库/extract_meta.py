import os, sys, json, subprocess, shutil

BASE = "D:/Desktop/shandou/抖音"
OUT = "D:/Desktop/shandou/资料库/video_meta.json"

ffprobe = shutil.which("ffprobe") or "ffprobe"
print("ffprobe:", ffprobe, flush=True)

videos = []
for root, dirs, files in os.walk(BASE):
    for f in sorted(files):
        if f.lower().endswith(".mp4"):
            full = os.path.join(root, f)
            rel = os.path.relpath(full, BASE)
            videos.append((rel, full))

print("total mp4:", len(videos), flush=True)

records = []
no_sub = 0
for rel, full in videos:
    rec = {"rel_path": rel, "file": os.path.basename(full)}
    try:
        cmd = [ffprobe, "-v", "quiet", "-print_format", "json",
               "-show_format", "-show_streams", full]
        out = subprocess.check_output(cmd, encoding="utf-8", errors="replace")
        info = json.loads(out)
        fmt = info.get("format", {})
        dur = fmt.get("duration")
        rec["duration_s"] = round(float(dur), 2) if dur else None
        vstream = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
        if vstream:
            rec["width"] = vstream.get("width")
            rec["height"] = vstream.get("height")
            fr = vstream.get("avg_frame_rate")
            rec["frame_rate_raw"] = fr
        subs = [s for s in info.get("streams", []) if s.get("codec_type") == "subtitle"]
        rec["has_subtitle_stream"] = bool(subs)
        rec["subtitle_streams"] = [
            {"codec": s.get("codec_name"), "lang": s.get("tags", {}).get("language")}
            for s in subs
        ]
        rec["source"] = "ffprobe"
        if not subs:
            no_sub += 1
    except Exception as e:
        rec["error"] = str(e)[:200]
        rec["source"] = "failed"
    records.append(rec)
    print("  ", rel, "dur=", rec.get("duration_s"), "res=", rec.get("width"), "x", rec.get("height"),
          "sub=", rec.get("has_subtitle_stream"), flush=True)

summary = {
    "total": len(records),
    "no_subtitle_stream": no_sub,
    "with_subtitle_stream": len(records) - no_sub,
    "total_duration_s": round(sum(r.get("duration_s") or 0 for r in records), 1),
}
data = {"summary": summary, "videos": records}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("=== SUMMARY ===")
print(json.dumps(summary, ensure_ascii=False, indent=2))
print("WROTE", OUT)
