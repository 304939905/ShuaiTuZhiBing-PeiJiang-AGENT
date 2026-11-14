import sys, os, json, subprocess, shutil

# 必须在 import faster_whisper / huggingface_hub 之前设置
# 注意：不设 HF_ENDPOINT 镜像，直接走系统代理(HTTP_PROXY/HTTPS_PROXY)连 huggingface.co
# 经测试 hf-mirror.com 镜像的 LFS 大文件会回源原站导致失败；直连代理反而可用。
os.environ["HF_HOME"] = "D:/WorkBuddyData/hf_cache"

video = sys.argv[1]
out_json = sys.argv[2]
model_size = sys.argv[3] if len(sys.argv) > 3 else "base"
os.makedirs(os.path.dirname(out_json), exist_ok=True)

# 系统已有 ffmpeg，优先用绝对路径，避免 PATH 找不到
ffmpeg = shutil.which("ffmpeg") or \
    "D:/Desktop/GPTT/.tools/ffmpeg/ffmpeg-master-latest-win64-gpl/bin/ffmpeg.EXE"
print("ffmpeg:", ffmpeg, flush=True)
wav = out_json + ".wav"
cmd = [ffmpeg, "-y", "-i", video, "-vn", "-ac", "1", "-ar", "16000", "-f", "wav", wav]
subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("audio extracted", flush=True)

# 模型优先复用本地目录（已用 download_modelbin.py 完整下载，避免经代理大文件被截断）
local = os.path.join("D:/WorkBuddyData/whisper_models", model_size)
model_bin = os.path.join(local, "model.bin")
if os.path.exists(model_bin) and os.path.getsize(model_bin) > 100_000_000:
    model_path = local
    print("reuse local model at", model_path, flush=True)
else:
    from huggingface_hub import snapshot_download
    repo = f"Systran/faster-whisper-{model_size}"
    os.makedirs(local, exist_ok=True)
    print("downloading model from", repo, "->", local, flush=True)
    model_path = snapshot_download(repo_id=repo, local_dir=local, local_dir_use_symlinks=False)
    print("model cached at", model_path, flush=True)

from faster_whisper import WhisperModel
model = WhisperModel(model_path, device="cpu", compute_type="int8")
segments, info = model.transcribe(wav, language="zh", beam_size=5, vad_filter=True)

result = {
    "video": video,
    "model": model_size,
    "language": info.language,
    "duration": round(info.duration, 2),
    "segments": [],
}
for seg in segments:
    result["segments"].append({
        "start": round(seg.start, 2),
        "end": round(seg.end, 2),
        "text": seg.text.strip(),
    })
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("TRANSCRIBE_DONE", out_json, "segs=", len(result["segments"]))
