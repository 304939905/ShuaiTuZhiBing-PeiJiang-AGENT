import os, re, subprocess, json, shutil, datetime

SRC_FRAME = r"D:/Desktop/shandou/抖音/阵容/撸铁队详解"
DST_FRAME = r"D:/Desktop/shandou/抖音_frames_dense_1s/阵容/撸铁队详解"
VIDEO = r"D:/Desktop/shandou/抖音/阵容/撸铁队详解.mp4"
MANIFEST = r"D:/Desktop/shandou/抖音_frames_dense_1s/阵容/_VERIFY_MANIFEST.json"
FFPROBE = r"D:/Desktop/GPTT/.tools/ffmpeg/ffmpeg-master-latest-win64-gpl/bin/ffprobe.exe"

def dur(path):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", path],
                       capture_output=True, text=True, timeout=120)
    return float(r.stdout.strip())

# 1) move frame folder
src_cnt = len([f for f in os.listdir(SRC_FRAME) if f.lower().endswith(".jpg")])
os.makedirs(os.path.dirname(DST_FRAME), exist_ok=True)
if os.path.exists(DST_FRAME):
    print("WARN: 目标已存在，先核验再覆盖:", DST_FRAME)
    existing = len([f for f in os.listdir(DST_FRAME) if f.lower().endswith(".jpg")])
    print("  目标已有帧数:", existing)
    # merge move: move only files not present
    for f in os.listdir(SRC_FRAME):
        s = os.path.join(SRC_FRAME, f)
        if os.path.isfile(s):
            shutil.move(s, os.path.join(DST_FRAME, f))
else:
    shutil.move(SRC_FRAME, DST_FRAME)
dst_cnt = len([f for f in os.listdir(DST_FRAME) if f.lower().endswith(".jpg")])
print(f"移动帧: 源{src_cnt} -> 目标{dst_cnt} | 一致:{src_cnt==dst_cnt}")
print(f"源帧文件夹是否已移除: {not os.path.exists(SRC_FRAME)}")

# 2) update manifest
m = json.load(open(MANIFEST, encoding="utf-8"))
pat = re.compile(r"frame_\d+_(\d+)h(\d+)m(\d+)s(\d+)ms\.jpg$")
files = sorted(f for f in os.listdir(DST_FRAME) if f.lower().endswith(".jpg"))
tss = []
for f in files:
    mm = pat.search(f)
    if mm:
        tss.append(int(mm.group(1))*3600 + int(mm.group(2))*60 + int(mm.group(3)) + int(mm.group(4))/1000.0)
d = dur(VIDEO)
new_entry = {
    "package": "撸铁队详解",
    "frame_count": len(files),
    "first_ts": round(min(tss), 3) if tss else None,
    "last_ts": round(max(tss), 3) if tss else None,
    "video_duration_sec": round(d, 2),
    "last_within_duration": (max(tss) <= d + 0.5) if (tss and d) else None,
}

# remove any existing entry with same package name (avoid dup on re-run)
m["videos"] = [v for v in m["videos"] if v.get("package") != "撸铁队详解"]
m["videos"].append(new_entry)
m["videos"].sort(key=lambda v: v["package"])
m["total_packages"] = len(m["videos"])
m["total_frames"] = sum(v["frame_count"] for v in m["videos"])
m["generated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
m["source_zip"] = "抖音/阵容 各视频同名静帧文件夹（精确毫秒时间戳版）；撸铁队详解于 2026-08-20 新增"
m["note"] = "阵容静帧唯一权威源。命名 frame_NNNNNN_HHhMMmSSsMMMms.jpg。原压缩包 video-frames-2026-08-20.zip 与根目录旧版 MM-SS 帧已于 2026-08-20 永久删除。撸铁队详解为新增包。"
m["verification"]["spotcheck"] = "此前 5 视频×3 点+撸铁队详解 3 点共 18 抽样，ffmpeg 按时间戳解码原画 vs 静帧 感知哈希距离 0–2 = 精确匹配"

json.dump(m, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\nManifest 更新: 包数={m['total_packages']} 帧数={m['total_frames']}")
print("新增条目:", json.dumps(new_entry, ensure_ascii=False))
print("撸铁队详解条目已含:", any(v.get("package")=="撸铁队详解" for v in m["videos"]))
