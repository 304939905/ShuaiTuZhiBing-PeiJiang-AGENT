import os, cv2, glob, sys, ctypes

def short_path(path):
    # 规避 opencv 在 Windows 下读中文路径失败：转 8.3 短路径（全 ASCII）
    try:
        buf = ctypes.create_unicode_buffer(4096)
        res = ctypes.windll.kernel32.GetShortPathNameW(path, buf, 4096)
        if res:
            return buf.value
    except Exception:
        pass
    return path

BASE = "D:/Desktop/shandou/抖音"
OUT = "D:/Desktop/shandou/抖音_frames"
os.makedirs(OUT, exist_ok=True)

# 递归收集所有 mp4（含子目录，如 开荒/）
vids = sorted(glob.glob(os.path.join(BASE, "**", "*.mp4"), recursive=True))
if "--test" in sys.argv:
    vids = vids[:1]
print("VIDEOS_TO_PROCESS:", len(vids), flush=True)

for f in vids:
    rel = os.path.relpath(f, BASE)              # 如 "开荒/xxx.mp4" 或 "yyy.mp4"
    stem = rel[:-4] if rel.lower().endswith(".mp4") else rel
    d = os.path.join(OUT, stem)
    os.makedirs(d, exist_ok=True)
    cap = cv2.VideoCapture(short_path(f))
    if not cap.isOpened():
        open(os.path.join(d, "_OPEN_FAIL.txt"), "w", encoding="utf-8").write(f)
        print("OPEN_FAIL:", rel, flush=True)
        continue
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    dur = total / fps if fps else 0
    n = min(8, max(3, int(dur // 20)))  # 每 ~20s 一张，至少 3 张最多 8 张
    positions = [int(total * (i + 0.5) / n) for i in range(n)]
    got = 0
    for idx, pos in enumerate(positions):
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        if ret and frame is not None:
            # 用 imencode 编码后字节写出，规避 imwrite 中文/特殊路径静默失败
            ok, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ok:
                with open(os.path.join(d, f"frame_{idx:02d}.jpg"), 'wb') as fo:
                    fo.write(buf)
                got += 1
    cap.release()
    with open(os.path.join(d, "_meta.txt"), "w", encoding="utf-8") as mf:
        mf.write(f"rel={rel}\nframes_total={total}\nfps={fps:.2f}\nduration_s={dur:.1f}\nextracted={got}\n")
    print("OK:", rel, "extracted", got, flush=True)

print("ALL_DONE", flush=True)
