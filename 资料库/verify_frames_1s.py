#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核验 1秒/帧 抽帧成果：目录对应、帧数-时长匹配、文件完整性、时间戳连续性。"""
import io
import os
import re
import json

META = r'D:\Desktop\shandou\资料库\video_meta.json'
BASE = r'D:\Desktop\shandou\抖音_frames_dense_1s'

meta = json.load(io.open(META, encoding='utf-8'))
videos = meta['videos']

print("=" * 100)
print("1 秒/帧抽帧成果核验报告")
print("=" * 100)
print(f"元数据视频总数: {meta['summary']['total']}  总时长: {meta['summary']['total_duration_s']:.1f}s")
print()

rows = []
missing_dir = []
for v in videos:
    rel = v['rel_path']
    dur = v['duration_s']
    stem = os.path.splitext(rel)[0].replace('/', os.sep)
    d = os.path.join(BASE, stem)
    if not os.path.isdir(d):
        missing_dir.append((rel, dur))
        continue
    files = [f for f in os.listdir(d) if f.endswith('.jpg')]
    n = len(files)
    # expected: 1 frame per second, 0..floor(dur) -> floor(dur)+1
    exp = int(dur) + 1
    # parse timestamps
    idxs = []
    secs = []
    bad_name = 0
    for f in files:
        m = re.match(r'frame_(\d+)_(\d{2})-(\d{2})\.jpg$', f)
        if m:
            idxs.append(int(m.group(1)))
            secs.append(int(m.group(2)) * 60 + int(m.group(3)))
        else:
            bad_name += 1
    gaps = []
    dups = 0
    if idxs:
        idxs_sorted = sorted(idxs)
        dups = len(idxs) - len(set(idxs))
        for a, b in zip(idxs_sorted, idxs_sorted[1:]):
            if b - a > 1:
                gaps.append((a, b))
    # zero-byte / tiny files
    tiny = 0
    total_bytes = 0
    for f in files:
        sz = os.path.getsize(os.path.join(d, f))
        total_bytes += sz
        if sz < 1024:
            tiny += 1
    maxsec = max(secs) if secs else -1
    rows.append(dict(rel=rel, dur=dur, n=n, exp=exp, diff=n - exp, bad_name=bad_name,
                     dups=dups, gaps=len(gaps), tiny=tiny, maxsec=maxsec,
                     mb=total_bytes / 1048576.0, gaplist=gaps[:5]))

# ---- report ----
print("-" * 100)
print("A. 目录缺失")
print("-" * 100)
if missing_dir:
    for r, dur in missing_dir:
        print(f"  [缺失] {r}  ({dur:.1f}s)")
else:
    print("  无。56 个视频全部有对应帧目录。")
print()

print("-" * 100)
print("B. 帧数 vs 时长 严重不符（|差值| > 2 帧）")
print("-" * 100)
bad = [r for r in rows if abs(r['diff']) > 2]
if bad:
    print(f"  {'实际帧':>6} {'应有帧':>6} {'差值':>6} {'时长s':>8} {'末帧秒':>7}  视频")
    for r in sorted(bad, key=lambda x: x['diff']):
        print(f"  {r['n']:>6} {r['exp']:>6} {r['diff']:>+6} {r['dur']:>8.1f} {r['maxsec']:>7}  {r['rel'][:60]}")
else:
    print("  无。全部视频帧数与时长匹配。")
print()

print("-" * 100)
print("C. 文件问题（命名异常 / 重复序号 / 序号断层 / 小于1KB）")
print("-" * 100)
prob = [r for r in rows if r['bad_name'] or r['dups'] or r['gaps'] or r['tiny']]
if prob:
    for r in prob:
        print(f"  {r['rel'][:55]}")
        print(f"     命名异常={r['bad_name']} 重复={r['dups']} 断层={r['gaps']} 小文件={r['tiny']} 断层示例={r['gaplist']}")
else:
    print("  无。所有帧文件命名规范、序号连续、无重复、无空文件。")
print()

print("-" * 100)
print("D. 汇总")
print("-" * 100)
print(f"  核验视频数      : {len(rows)} / {len(videos)}")
print(f"  实际总帧数      : {sum(r['n'] for r in rows)}")
print(f"  理论总帧数      : {sum(r['exp'] for r in rows)}")
print(f"  总占用          : {sum(r['mb'] for r in rows):.0f} MB")
print(f"  帧数完全吻合    : {sum(1 for r in rows if r['diff'] == 0)} 个")
print(f"  差值在 ±1 内    : {sum(1 for r in rows if abs(r['diff']) <= 1)} 个")
print(f"  差值在 ±2 内    : {sum(1 for r in rows if abs(r['diff']) <= 2)} 个")
print()

print("-" * 100)
print("E. 全部明细（按差值排序）")
print("-" * 100)
print(f"  {'实际':>5} {'应有':>5} {'差':>4} {'时长s':>7}  视频")
for r in sorted(rows, key=lambda x: (x['diff'], -x['dur'])):
    flag = "  " if abs(r['diff']) <= 2 else "!!"
    print(f"{flag}{r['n']:>5} {r['exp']:>5} {r['diff']:>+4} {r['dur']:>7.1f}  {r['rel'][:62]}")
