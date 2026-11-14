import os, re, subprocess
from PIL import Image
import numpy as np

VIDEO = r"D:/Desktop/shandou/抖音/阵容/撸铁队详解.mp4"
FRAME_DIR = r"D:/Desktop/shandou/抖音/阵容/撸铁队详解"
FFPROBE = r"D:/Desktop/GPTT/.tools/ffmpeg/ffmpeg-master-latest-win64-gpl/bin/ffprobe.exe"
FFMPEG = r"D:/Desktop/GPTT/.tools/ffmpeg/ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe"

def dur(path):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", path],
                       capture_output=True, text=True, timeout=120)
    return float(r.stdout.strip())

def ahash(path, size=8):
    im = Image.open(path).convert("L").resize((size, size), Image.LANCZOS)
    a = np.asarray(im, dtype=np.float64)
    return a > a.mean()

def hamming(h1, h2):
    return int(np.sum(h1 != h2))

def fmt_ts(ts):
    h = int(ts // 3600); rem = ts % 3600; mi = int(rem // 60); s = int(rem % 60); ms = int(round((ts - h*3600 - mi*60 - s) * 1000))
    return f"{h:02d}h{mi:02d}m{s:02d}s{ms:03d}ms"

pat = re.compile(r"frame_(\d+)_(\d+)h(\d+)m(\d+)s(\d+)ms\.jpg$")

files = sorted(f for f in os.listdir(FRAME_DIR) if f.lower().endswith(".jpg"))
entries = []
for f in files:
    m = pat.search(f)
    if m:
        idx = int(m.group(1)); ts = int(m.group(2))*3600 + int(m.group(3))*60 + int(m.group(4)) + int(m.group(5))/1000.0
        entries.append((idx, ts, f))

cnt = len(entries)
idxs = [i for i, _, _ in entries]
tss = [t for _, t, _ in entries]
idx_ok = idxs == list(range(1, cnt+1))
ts_step_ok = all(abs(t - (i-1)) < 0.05 for i, t, _ in entries)
d = dur(VIDEO)
max_ts = max(tss); min_ts = min(tss)
within = max_ts <= d + 0.5

print(f"视频时长: {d:.2f}s")
print(f"帧数: {cnt}")
print(f"时间戳范围: {fmt_ts(min_ts)} ~ {fmt_ts(max_ts)}")
print(f"序号连续: {idx_ok}")
print(f"时间戳1fps对齐: {ts_step_ok}")
print(f"末帧({max_ts:.1f}s) <= 时长({d:.1f}s): {within}")

# spot-check 3 points
import tempfile
tmp = tempfile.mkdtemp()
print("\n=== 抽点核验（ffmpeg按时间戳解码原画 vs 静帧包）===")
for idx in [1, 152, 304]:
    ts = idx - 1
    zpath = os.path.join(FRAME_DIR, fmt_ts_built := fmt_ts(ts))
    zpath = [f for _, _, f in entries if _ == ts][0] if False else None
    # find actual filename
    actual = [f for i, t, f in entries if i == idx][0]
    zdata = open(os.path.join(FRAME_DIR, actual), "rb").read()
    za = os.path.join(tmp, "zip.jpg"); open(za, "wb").write(zdata)
    outp = os.path.join(tmp, "real.jpg")
    r = subprocess.run([FFMPEG, "-ss", f"{ts:.3f}", "-i", VIDEO, "-frames:v", "1", "-vf", "scale=320:-1", "-y", outp],
                       capture_output=True, text=True, timeout=120)
    if not os.path.exists(outp):
        print(f"  idx{idx}: ffmpeg失败 {r.stderr[-150:]}"); continue
    dist = hamming(ahash(za), ahash(outp))
    verdict = "✅精确匹配" if dist <= 2 else ("⚠️近似" if dist <= 6 else "❌不符")
    print(f"  idx{idx} ts={fmt_ts(ts)} 哈希距离={dist} {verdict}")

print("\n结论:", "PASS - 时间戳可精确对应原视频时间轴" if (idx_ok and ts_step_ok and within) else "CHECK NEEDED")
