#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""核验 1秒版 内所有帧引用 vs 新更名帧文件。
引用形式: 新格式 frame_000006_00h00m05s000ms.jpg / 纯序号 frame_0005
排除: frame_json / frame_report_schema.md / frame_only_value 等技术术语
"""
import re
from pathlib import Path
import docx

ROOT = Path("D:/Desktop/shandou/报告库")
FR = Path("D:/Desktop/shandou")

NEW = re.compile(r"frame_(\d{6})_(\d{2})h(\d{2})m(\d{2})s(\d{3})ms\.jpg")
IDX = re.compile(r"\bframe_(\d{4,6})\b")  # 纯序号(须排除技术术语)
TECH = ("frame_json", "frame_report_schema", "frame_only_value", "frame_xxxx", "frame_x")


def norm(s):
    return re.sub(r"[\s\W_]+", "", s, flags=re.UNICODE).lower()


def find_frame_dir(title):
    cands = [
        FR / "抖音_frames_dense_1s" / title,
        FR / "海之呼唤_frames_dense_1s" / title,
        FR / "赛季_frames_dense_1s" / title,
    ]
    nt = norm(title)
    for c in cands:
        if c.exists():
            return c
    # 模糊匹配
    for root in ["抖音_frames_dense_1s", "海之呼唤_frames_dense_1s", "赛季_frames_dense_1s"]:
        for d in (FR / root).iterdir():
            if d.is_dir() and norm(d.name) == nt:
                return d
    return None


def check_frame(fdir, sec):
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    name = f"frame_{sec+1:06d}_{h:02d}h{m:02d}m{s:02d}s000ms.jpg"
    f = fdir / name
    if f.exists():
        return True, name
    # 开荒合并: 帧在子目录
    for sd in fdir.iterdir():
        if sd.is_dir() and (sd / name).exists():
            return True, name
    return False, name


rows = []
total_ref = 0
missing = []
for sub in ["旧56项目", "开荒", "海之呼唤", "赛季"]:
    d = ROOT / sub / "逐帧1秒版"
    if not d.exists():
        continue
    for f in sorted(d.glob("*.docx")):
        full = "\n".join(p.text for p in docx.Document(str(f)).paragraphs)
        title_m = re.search(r"视频标题[:：]\s*(.+)", full)
        title = title_m.group(1).strip() if title_m else f.stem
        fdir = find_frame_dir(title)
        if not fdir:
            rows.append((sub, f.name[:30], "无帧目录", 0))
            continue
        # 新格式引用
        refs = []
        for m in NEW.finditer(full):
            sec = int(m.group(2)) * 3600 + int(m.group(3)) * 60 + int(m.group(4))
            refs.append(("new", sec, m.group(0)))
        # 纯序号引用(排除技术术语上下文)
        for m in IDX.finditer(full):
            ctx = full[max(0, m.start() - 12):m.start()]
            if any(t in ctx for t in TECH):
                continue
            if "frame_" + m.group(1) not in [r[2] for r in refs]:  # 不与新格式重复计
                refs.append(("idx", int(m.group(1)), "frame_" + m.group(1)))
        ok = miss = 0
        for kind, sec, ref in refs:
            total_ref += 1
            # 纯序号: 按秒数制假设 秒=序号
            s2 = sec if kind == "new" else sec
            found, name = check_frame(fdir, s2)
            if found:
                ok += 1
            else:
                miss += 1
                missing.append((sub, f.name[:26], ref, "->", name))
        rows.append((sub, f.name[:30], f"{ok}/{len(refs)}", miss))

print(f"{'子项目':<8}{'报告':<32}{'帧引用':<10}缺失")
print("-" * 80)
for sub, name, stat, miss in rows:
    flag = "❌" if (isinstance(miss, int) and miss) else "✅"
    print(f"{flag} {sub:<8}{name:<32}{stat:<10}{miss if isinstance(miss, int) else ''}")
print(f"\n总帧引用: {total_ref}  缺失: {len(missing)}")
for m in missing[:20]:
    print("  MISS:", m)
