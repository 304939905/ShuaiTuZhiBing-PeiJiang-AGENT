#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""静帧文件名核验: 全量扫描 + 每包随机抽查。
全量: 格式正则 / 序号连续(1..N 无缺) / 序号-1 == 时间戳秒
抽查: 每包随机 5 个, 验证 JPEG 头(FFD8)、文件非空、时间戳换算一致。
"""
import random, re
from pathlib import Path

ROOT = Path("D:/Desktop/shandou")
random.seed(20260820)
NEW = re.compile(r"^frame_(\d{6})_(\d{2})h(\d{2})m(\d{2})s(\d{3})ms\.jpg$")


def sec_of(hh, mm, ss):
    return int(hh) * 3600 + int(mm) * 60 + int(ss)


def collect_dirs():
    dirs = []
    top = ROOT / "抖音_frames_dense_1s"
    for d in sorted(top.iterdir()):
        if not d.is_dir() or d.name in ("contact_sheets",) or d.name.startswith("_"):
            continue
        if d.name in ("开荒", "机制", "阵容"):
            # 父目录: 递归其子目录(每个子目录=一个视频帧包)
            dirs += [x for x in sorted(d.iterdir()) if x.is_dir() and not x.name.startswith("_")]
        else:
            dirs.append(d)
    for fr in ("海之呼唤_frames_dense_1s", "赛季_frames_dense_1s"):
        r = ROOT / fr
        if r.exists():
            dirs += [d for d in sorted(r.iterdir()) if d.is_dir() and not d.name.startswith("_")]
    return dirs


results = []
for d in collect_dirs():
    files = sorted(d.glob("*.jpg"))
    n = len(files)
    # 全量: 格式 + 序号连续性 + 序号-秒一致性
    bad_fmt = 0
    idx_list = []
    sec_list = []
    for f in files:
        m = NEW.match(f.name)
        if not m:
            bad_fmt += 1
            continue
        idx = int(m.group(1))
        sec = sec_of(m.group(2), m.group(3), m.group(4))
        idx_list.append(idx)
        sec_list.append(sec)
    gap = []
    for i in range(1, len(idx_list)):
        if idx_list[i] != idx_list[i - 1] + 1:
            gap.append((idx_list[i - 1], idx_list[i]))
    sec_mismatch = sum(1 for idx, sec in zip(idx_list, sec_list) if idx - 1 != sec)
    # 随机抽查 5 个
    samples = random.sample(files, min(5, n)) if n else []
    s_ok = s_bad = 0
    for f in samples:
        m = NEW.match(f.name)
        ok = False
        if m:
            data = f.read_bytes()
            if data and data[:2] == b"\xff\xd8":  # JPEG 头
                sec = sec_of(m.group(2), m.group(3), m.group(4))
                ok = (int(m.group(1)) - 1 == sec) and len(data) > 5000
        if ok:
            s_ok += 1
        else:
            s_bad += 1
    status = "OK"
    probs = []
    if bad_fmt:
        status = "格式异常"
        probs.append(f"格式不符 {bad_fmt}")
    if gap:
        status = "序号跳号"
        probs.append(f"跳号 {len(gap)} 处 {gap[:3]}")
    if sec_mismatch:
        status = "时间戳不符"
        probs.append(f"序号-秒不一致 {sec_mismatch}")
    if s_bad:
        status = "抽查失败"
        probs.append(f"抽查 {s_bad}/{len(samples)} 失败")
    results.append((d, n, status, "; ".join(probs) if probs else "-", s_ok, len(samples)))

print(f"{'目录':<42}{'帧数':<7}{'抽查':<5}状态")
print("-" * 90)
bad_total = 0
for d, n, status, probs, s_ok, s_n in results:
    flag = "❌" if status != "OK" else "✅"
    if status != "OK":
        bad_total += 1
    print(f"{flag} {d.parent.name}/{d.name[:26]:<28}{n:<7}{s_ok}/{s_n}  {status} {probs}")
print(f"\n目录总数: {len(results)}  异常目录: {bad_total}")
