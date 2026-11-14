import requests, os, sys

out = "D:/WorkBuddyData/whisper_models/base/model.bin"
# 优先国内镜像（完整镜像 LFS），失败回退原站（走系统代理）
urls = [
    "https://hf-mirror.com/Systran/faster-whisper-base/resolve/main/model.bin",
    "https://huggingface.co/Systran/faster-whisper-base/resolve/main/model.bin",
]

for url in urls:
    print("TRY", url, flush=True)
    for attempt in range(5):
        try:
            if os.path.exists(out):
                os.remove(out)
            with requests.get(url, stream=True, timeout=300) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                print("  attempt", attempt, "content-length:", total, flush=True)
                downloaded = 0
                with open(out, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                if total and downloaded >= total * 0.99:
                    print("  OK size:", downloaded, flush=True)
                    sys.exit(0)
                else:
                    print("  incomplete:", downloaded, "of", total, flush=True)
        except Exception as e:
            print("  err:", repr(e)[:160], flush=True)
    print("  -> url failed after retries", flush=True)

print("ALL FAILED", flush=True)
sys.exit(1)
