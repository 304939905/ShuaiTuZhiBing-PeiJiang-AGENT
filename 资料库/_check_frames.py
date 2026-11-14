# -*- coding: utf-8 -*-
import json, os, glob, sys

BASE = r"D:\Desktop\shandou"
LIB  = os.path.join(BASE, "资料库")
HZH_JSON = os.path.join(LIB, "hzh_frame_json")
SAI_JSON = os.path.join(LIB, "saiji_frame_json")
HZH_FR  = os.path.join(BASE, "海之呼唤_frames_dense_1s")
SAI_FR  = os.path.join(BASE, "赛季_frames_dense_1s")

def walk_frames(json_path):
    with open(json_path, encoding="utf-8") as f:
        d = json.load(f)
    fd = d.get("frames_dir") or d.get("video_title") or os.path.splitext(os.path.basename(json_path))[0]
    refs = []
    for seg in d.get("timeline", []):
        for fr in seg.get("frames", []):
            fn = fr.get("file")
            if fn:
                refs.append(fn)
    return fd, refs

def resolve_framedir(folder_base, fd):
    cand = os.path.join(folder_base, fd)
    if os.path.isdir(cand):
        return cand
    # fuzzy: ignore leading/trailing spaces & punctuation
    norm = lambda s: "".join(ch for ch in s if ch.isalnum() or '\u4e00' <= ch <= '\u9fff')
    target = norm(fd)
    if not target:
        return None
    best = None
    for name in os.listdir(folder_base):
        if norm(name) == target:
            return os.path.join(folder_base, name)
    return None

def check_one(json_path, folder_base):
    fd, refs = walk_frames(json_path)
    fdir = resolve_framedir(folder_base, fd)
    if fdir is None:
        return (os.path.basename(json_path), fd, "FRAME_DIR_MISSING", [], len(refs), refs)
    missing = []
    for fn in refs:
        if not os.path.isfile(os.path.join(fdir, fn)):
            missing.append(fn)
    status = "OK" if not missing else "MISSING_FRAMES"
    return (os.path.basename(json_path), fd, status, missing, len(refs), refs)

results = []
for jp in glob.glob(os.path.join(HZH_JSON, "*.json")):
    results.append(check_one(jp, HZH_FR))
for jp in glob.glob(os.path.join(SAI_JSON, "*.json")):
    results.append(check_one(jp, SAI_FR))

print("=== 帧引用完整性核验（23 份源 JSON → dense_1s 抽帧目录）===\n")
total_refs = 0
total_missing = 0
for name, fd, status, missing, nref, _ in results:
    total_refs += nref
    total_missing += len(missing)
    flag = "  <<< 异常" if status != "OK" else ""
    print(f"[{status:16}] {name}")
    print(f"    frames_dir={fd}  引用帧数={nref}{flag}")
    for m in missing[:30]:
        print(f"    缺失: {m}")
    if len(missing) > 30:
        print(f"    ... 另有 {len(missing)-30} 个缺失")

print(f"\n汇总：JSON 份数={len(results)}  总引用帧={total_refs}  缺失帧={total_missing}")
# write machine summary
with open(os.path.join(LIB, "_frame_check_out.txt"), "w", encoding="utf-8") as f:
    f.write(f"JSON={len(results)} refs={total_refs} missing={total_missing}\n")
    for name, fd, status, missing, nref, _ in results:
        f.write(f"{name}\t{fd}\t{status}\t{nref}\t{len(missing)}\n")
        for m in missing:
            f.write(f"  MISSING {m}\n")
print("done")
