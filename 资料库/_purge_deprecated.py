import os, shutil

zip_path = r"D:\Desktop\shandou\抖音\阵容\video-frames-2026-08-20.zip"
dep_dir = r"D:\Desktop\shandou\抖音_frames_dense_1s\_deprecated_root_阵容_2026-08-20"

def human(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}TB"

print("=== 删除前核验 ===")
freed = 0
if os.path.exists(zip_path):
    sz = os.path.getsize(zip_path)
    freed += sz
    print(f"  ZIP 存在: {zip_path}\n      大小 {human(sz)}")
else:
    print(f"  ZIP 不存在(已删?): {zip_path}")

if os.path.isdir(dep_dir):
    total = 0
    for root, _, files in os.walk(dep_dir):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    freed += total
    print(f"  DIR 存在: {dep_dir}\n      帧数 {sum(len(fs) for _,_,fs in os.walk(dep_dir))} 大小 {human(total)}")
else:
    print(f"  DIR 不存在(已删?): {dep_dir}")

print(f"\n预计释放: {human(freed)}")

# --- 永久删除 ---
print("\n=== 执行永久删除 ===")
if os.path.exists(zip_path):
    os.remove(zip_path)
    print(f"  已删 ZIP: 存在={os.path.exists(zip_path)}")
if os.path.isdir(dep_dir):
    shutil.rmtree(dep_dir)
    print(f"  已删 DIR: 存在={os.path.isdir(dep_dir)}")

print("\n=== 删除后核验 ===")
print("  ZIP 还存在:", os.path.exists(zip_path))
print("  DIR 还存在:", os.path.isdir(dep_dir))
