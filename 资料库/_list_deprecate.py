import os, json
base = r"D:\Desktop\shandou\抖音_frames_dense_1s"
zhenrong = os.path.join(base, "阵容")
root_dirs = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)) and d != "阵容"]
zhenrong_dirs = sorted(os.listdir(zhenrong)) if os.path.isdir(zhenrong) else []
to_move = sorted([d for d in root_dirs if d in zhenrong_dirs])
total_frames = 0
for d in to_move:
    total_frames += len([f for f in os.listdir(os.path.join(base, d)) if f.lower().endswith(".jpg")])
print("根目录子文件夹总数:", len(root_dirs))
print("阵容子目录包数:", len(zhenrong_dirs))
print("将要弃用(移动)的文件夹数:", len(to_move))
print("弃用帧总数:", total_frames)
print("--- 列表 ---")
for d in to_move:
    print("  ", d)
print("\n校验: 阵容包全部命中根目录:", len(zhenrong_dirs) == len(to_move) and set(zhenrong_dirs) == set(to_move))
