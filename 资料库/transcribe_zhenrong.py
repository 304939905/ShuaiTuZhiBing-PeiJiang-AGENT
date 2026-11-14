import os, subprocess, sys, glob, time

ROOT = r'D:/Desktop/shandou'
SRC = os.path.join(ROOT, '抖音', '阵容')
OUT = os.path.join(ROOT, '资料库', 'zhenrong_transcripts')
os.makedirs(OUT, exist_ok=True)

PY = r'C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe'
SCRIPT = os.path.join(ROOT, '资料库', 'transcribe.py')

videos = sorted(glob.glob(os.path.join(SRC, '*.mp4')))
print('ZHENRONG_VIDEO_COUNT=%d' % len(videos))

done = 0
for v in videos:
    name = os.path.splitext(os.path.basename(v))[0]
    out_json = os.path.join(OUT, name + '.json')
    if os.path.exists(out_json):
        print('SKIP (exists):', name)
        done += 1
        continue
    t0 = time.time()
    try:
        subprocess.run([PY, SCRIPT, v, out_json, 'base'], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        done += 1
        print('DONE (%ds): %s' % (int(time.time()-t0), name), flush=True)
    except Exception as e:
        print('FAIL: %s -> %s' % (name, e), flush=True)

print('ZHENRONG_TRANSCRIBE_DONE done=%d total=%d' % (done, len(videos)))
