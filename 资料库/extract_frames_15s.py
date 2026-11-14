import sys, os, cv2, ctypes

def short_path(p):
    try:
        buf = ctypes.create_unicode_buffer(32768)
        if ctypes.windll.kernel32.GetShortPathNameW(p, buf, 32768):
            return buf.value
    except Exception:
        pass
    return p

video = sys.argv[1]
outdir = sys.argv[2]
interval = int(sys.argv[3]) if len(sys.argv) > 3 else 15
os.makedirs(outdir, exist_ok=True)

cap = cv2.VideoCapture(short_path(video))
if not cap.isOpened():
    print("OPEN_FAIL", video)
    sys.exit(1)
fps = cap.get(cv2.CAP_PROP_FPS) or 25
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
dur = total / fps if fps else 0
n = int(dur // interval) + 1
cnt = 0
for i in range(n):
    t = i * interval
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
    ret, frame = cap.read()
    if ret and frame is not None:
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if ok:
            with open(os.path.join(outdir, f"f_{t:04d}.jpg"), "wb") as f:
                f.write(buf.tobytes())
            cnt += 1
cap.release()
print("FRAMES_DONE", cnt, "dir=", outdir, "interval=", interval)
