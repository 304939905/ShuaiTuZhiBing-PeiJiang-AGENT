#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""统一静帧命名为最新格式: frame_000001_00h00m00s000ms.jpg
处理: 旧56/开荒/海呼/赛季/机制 (旧格式 frame_XXXX_MM-SS.jpg 或 frame_XXXXX_MM-SS.jpg)
跳过: 阵容(已新格式)、contact_sheets、_开头目录、已是新格式的目录
映射表: D:/WorkBuddyData/shandou_frame_rename_map.json (可还原)
用法: rename_frames.py [--apply]   (默认干跑)
"""
import sys, json, re
from pathlib import Path

ROOT = Path("D:/Desktop/shandou")
MAP_FILE = Path("D:/WorkBuddyData/shandou_frame_rename_map.json")
APPLY = "--apply" in sys.argv

OLD_RE = re.compile(r"^frame_(\d+)_(\d{2})-(\d{2})\.jpg$")
NEW_RE = re.compile(r"^frame_\d{6}_\d{2}h\d{2}m\d{2}s\d{3}ms\.jpg$")


def new_name(idx1, sec):
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"frame_{idx1:06d}_{h:02d}h{m:02d}m{s:02d}s000ms.jpg"


def collect_dirs():
    dirs = []
    # 旧56: 抖音_frames_dense_1s 顶层各目录(排除 开荒/机制/阵容/contact_sheets/_*)
    top = ROOT / "抖音_frames_dense_1s"
    for d in sorted(top.iterdir()):
        if not d.is_dir():
            continue
        if d.name in ("开荒", "机制", "阵容", "contact_sheets") or d.name.startswith("_"):
            continue
        dirs.append(d)
    # 开荒/机制 子目录
    for grp in ("开荒", "机制"):
        g = top / grp
        if g.exists():
            dirs += [d for d in sorted(g.iterdir()) if d.is_dir() and not d.name.startswith("_")]
    # 海呼/赛季 根
    for fr in ("海之呼唤_frames_dense_1s", "赛季_frames_dense_1s"):
        r = ROOT / fr
        if r.exists():
            dirs += [d for d in sorted(r.iterdir()) if d.is_dir() and not d.name.startswith("_")]
    return dirs


def process_dir(d):
    """返回 (mapping, skipped_new, skipped_other)。mapping: [(old,new)]"""
    ff = sorted(d.glob("*.jpg"))
    old_items = []
    new_items = []
    skip_new = skip_other = 0
    for f in ff:
        m = OLD_RE.match(f.name)
        if m:
            sec = int(m.group(2)) * 60 + int(m.group(3))
            old_items.append((int(m.group(1)), sec, f.name))
        elif NEW_RE.match(f.name):
            new_items.append(f.name)
        else:
            skip_other += 1
    if old_items and new_items:
        skip_other += len(new_items)  # 混合: 保守跳过该目录
        return [], 0, skip_other
    if not old_items:
        return [], len(new_items), skip_other
    # 按时间戳秒排序(同秒按序号)
    old_items.sort(key=lambda x: (x[1], x[0]))
    mapping = []
    seen_sec = {}
    for i, (idx, sec, name) in enumerate(old_items):
        if sec in seen_sec:
            # 同秒多帧: 用序号细分, 保持新时间戳同秒(序号递增保证唯一)
            seen_sec[sec] += 1
        else:
            seen_sec[sec] = 1
        nn = new_name(i + 1, sec)
        mapping.append((name, nn))
    return mapping, 0, skip_other


def main():
    dirs = collect_dirs()
    total_map = {}
    total_files = 0
    print(f"扫描目录: {len(dirs)}")
    for d in dirs:
        mapping, skip_new, skip_other = process_dir(d)
        if mapping:
            total_map[str(d)] = mapping
            total_files += len(mapping)
            print(f"  [{d.parent.name}/{d.name[:28]}] 旧格式 {len(mapping)} 帧 -> 新格式")
        elif skip_other:
            print(f"  [SKIP 混合/异常] {d.name[:40]} (其他={skip_other})")
    print(f"\n将重命名: {total_files} 帧, 涉及 {len(total_map)} 目录")
    # 校验: 新名唯一 + 时间戳可还原
    err = 0
    for d, mapping in total_map.items():
        names = [n for _, n in mapping]
        if len(set(names)) != len(names):
            print(f"  [新名重复!] {d[:40]}")
            err += 1
    MAP_FILE.write_text(json.dumps(total_map, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"映射表已写: {MAP_FILE} (共 {total_files} 条)")
    if not APPLY:
        print("\n[干跑模式] 未实际重命名。加 --apply 执行。")
        return
    done = 0
    for d, mapping in total_map.items():
        p = Path(d)
        for old, new in mapping:
            (p / old).rename(p / new)
            done += 1
    print(f"已重命名 {done} 帧")


if __name__ == "__main__":
    main()
