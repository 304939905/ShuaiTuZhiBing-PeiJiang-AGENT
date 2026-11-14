import os, shutil, json

base = r"D:\Desktop\shandou\抖音_frames_dense_1s"
zhenrong = os.path.join(base, "阵容")
deprecated = os.path.join(base, "_deprecated_root_阵容_2026-08-20")
os.makedirs(deprecated, exist_ok=True)

root_dirs = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)) and d != "阵容"]
zhenrong_dirs = set(os.listdir(zhenrong)) if os.path.isdir(zhenrong) else set()
to_move = sorted([d for d in root_dirs if d in zhenrong_dirs])

moved = []
for d in to_move:
    src = os.path.join(base, d)
    dst = os.path.join(deprecated, d)
    if os.path.exists(dst):
        print("跳过(目标已存在):", d)
        continue
    shutil.move(src, dst)
    moved.append(d)

# count frames moved
total = 0
for d in moved:
    total += len([f for f in os.listdir(os.path.join(deprecated, d)) if f.lower().endswith(".jpg")])

print(f"已移动 {len(moved)} 个文件夹到: {deprecated}")
print(f"移动帧总数: {total}")
print("移动列表:")
for d in moved:
    print("  ", d)

# verify root no longer has these
remaining = [d for d in root_dirs if d in zhenrong_dirs and os.path.isdir(os.path.join(base, d))]
print("\n根目录残留的旧版阵容帧文件夹:", remaining)
print("根目录残留数:", len(remaining))
