import json
from pathlib import Path

root = Path("D:/Desktop/shandou/报告库")
bench_kw = ["攻其", "神赏", "焚决", "009", "战法阈值"]  # 标杆精修 / 已定稿精简报告的标记

inv = {}  # (sub, tier) -> [filenames]
for p in root.rglob("*.docx"):
    parts = p.relative_to(root).parts
    if len(parts) >= 2:
        sub, tier = parts[0], parts[1]
    else:
        sub, tier = "(root)", parts[0]
    inv.setdefault((sub, tier), []).append(p.name)

print("=== 目录结构 (子项目 / 层级 / 份数) ===")
for (sub, tier), files in sorted(inv.items()):
    print(f"{sub}\t{tier}\t{len(files)}")

# 标杆精修定位
bench = []
for (sub, tier), files in inv.items():
    if tier == "精编":
        for f in files:
            if any(k in f for k in bench_kw):
                bench.append(f"{sub}/{f}")
print("\n=== 标杆精修 (保留, 不删) ===")
for b in bench:
    print("  ", b)

# 删除目标: 旧一批(非阵容新批) 的 精编(剔除标杆) + 完整版
del_list = []
for (sub, tier), files in inv.items():
    if sub == "阵容新批":
        continue  # 新一批, 不动
    if tier in ("精编", "完整版"):
        for f in files:
            if tier == "精编" and any(k in f for k in bench_kw):
                continue
            del_list.append(f"{sub}/{tier}/{f}")

# 1秒版源
src_1s = [(sub, len(fs)) for (sub, tier), fs in inv.items() if tier == "逐帧1秒版"]
src_total = sum(n for _, n in src_1s)

print("\n=== 删除目标统计 ===")
print("  待删文件总数:", len(del_list))
by_tier = {}
for d in del_list:
    t = d.split("/")[1]
    by_tier[t] = by_tier.get(t, 0) + 1
print("  按层级:", by_tier)

print("\n=== 1秒版源 (用于产出精修) ===")
for sub, n in src_1s:
    print(f"  {sub}: {n}")
print("  1秒版源总数:", src_total)

print("\n=== 保留项 ===")
print("  阵容新批 精编(1份, 新一批, 不动):",
      [f for (sub, tier), fs in inv.items() if sub == '阵容新批' and tier == '精编' for f in fs])
print("  标杆精修(保留):", len(bench), "份")

# 输出 JSON 供后续删除脚本使用
out = {"delete": del_list, "benchmark_keep": bench,
       "src_1s_total": src_total, "src_1s_by_sub": dict(src_1s)}
Path("D:/Desktop/shandou/资料库/_manifest.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nmanifest -> _manifest.json")
