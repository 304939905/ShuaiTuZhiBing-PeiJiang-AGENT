#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""全量核验新版精修报告(74份):
1. 四章节齐全  2. 正文无内联帧引用  3. 溯源索引帧路径落地(帧或目录)
4. 时间锚一致性: 精修每个[MM:SS]点须能在源1秒版找到同时间戳且文本一致
5. 帧命名连字符
输出: 每份状态 + 问题清单
"""
import re, sys
from pathlib import Path
import docx

ROOT = Path("D:/Desktop/shandou/报告库")
SUB = ["旧56项目", "开荒", "海之呼唤", "赛季"]
BENCH_K = ["攻其篇—粉丝投稿解析", "神赏篇 来了! 评论投稿", "从零开始，宝物养成焚决"]

fpat = re.compile(r"frame_(\d{6})_(\d{2})h(\d{2})m(\d{2})s\d{3}ms\.jpg")
cpat = re.compile(r"frame_\d{4}_\d{2}:\d{2}\.jpg")  # 旧格式冒号(历史), 现应无


def extract_src_points(path):
    """源1秒版: 返回 [(ts, text)]，兼容单点与范围两种格式。"""
    paras = [p.text.strip() for p in docx.Document(str(path)).paragraphs if p.text.strip()]
    pts = []
    for t in paras:
        m = re.match(r"^(\d\d:\d\d)\s+(?!\|)(.*)", t)
        if m:
            pts.append((m.group(1), m.group(2).strip()))
            continue
        m = re.match(r"^(\d\d:\d\d)[–-](\d\d:\d\d)\s+(?!\|)(.+)", t)
        if m:
            pts.append((m.group(1), m.group(3).strip()))
    return pts


def sim(a, b):
    """简单字符重合率。"""
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    return len(sa & sb) / max(len(sa), len(sb))


problems = []
stats = {"total": 0, "bench": 0, "new": 0, "sec4_ok": 0, "inline_bad": 0,
         "colon": 0, "land_ok": 0, "land_fail": 0, "no_idx": 0}

for sub in SUB:
    jd = ROOT / sub / "精编"
    src_dir = ROOT / sub / "逐帧1秒版"
    for f in sorted(jd.glob("*.docx")):
        is_bench = any(k in f.name for k in BENCH_K)
        stats["total"] += 1
        stats["bench" if is_bench else "new"] += 1
        full = "\n".join(p.text for p in docx.Document(str(f)).paragraphs)

        # 1 四章节
        has4 = all(k in full for k in ["核心结论", "分段精要", "AI 主动推断", "溯源索引"])
        if has4:
            stats["sec4_ok"] += 1

        idx = full.rfind("溯源索引")
        tail = full[idx:] if idx > 0 else ""
        body = full[:idx] if idx > 0 else full

        # 2 正文内联帧引用
        if fpat.search(body) or cpat.search(body):
            stats["inline_bad"] += 1
            problems.append(f"内联帧引用: {sub}/{f.name[:40]}")

        # 3 冒号错误 + 落地
        if cpat.search(tail):
            stats["colon"] += 1
            problems.append(f"冒号帧名: {sub}/{f.name[:40]}")
        frames = fpat.findall(tail)
        if not frames:
            if not is_bench:
                stats["no_idx"] += 1
                problems.append(f"索引无帧: {sub}/{f.name[:40]}")
            land = None
        else:
            first = fpat.search(tail)
            st = tail.rfind("\n", 0, first.start())
            line = tail[st + 1:first.start()] if st >= 0 else tail[:first.start()]
            dm = re.search(r"\]\s*(.+?)/?\s*$", line)
            dp = Path(dm.group(1).strip().rstrip("/")) if dm else None
            idx, hh, mm, ss = first.groups()
            cand = (dp / f"frame_{idx}_{hh}h{mm}m{ss}s000ms.jpg") if dp else None
            land = (cand.exists() if cand else False) or (dp.exists() if dp else False)
            if land:
                stats["land_ok"] += 1
            else:
                stats["land_fail"] += 1
                problems.append(f"落地失败: {sub}/{f.name[:40]}")

        # 4 时间锚一致性(仅非标杆; 标杆格式不同不适用)
        if not is_bench and "分段精要" in full:
            # 精修正文分析点
            ref_pts = []
            for p in full.split("\n"):
                m = re.match(r"^\[\d\d:\d\d\]\s+(.*)", p.strip())
                if m:
                    ref_pts.append((p.strip()[1:6], m.group(1).strip()))
            # 源1秒版
            vt = f.name.replace("_精修学习报告.docx", "")
            src_f = src_dir / f"{vt}_逐帧深度学习报告_1秒版.docx"
            if src_f.exists():
                src_pts = extract_src_points(src_f)
                src_map = {}
                for ts, tx in src_pts:
                    src_map.setdefault(ts, []).append(tx)
                for ts, tx in ref_pts:
                    if ts not in src_map:
                        problems.append(f"时间锚不存在({ts}): {sub}/{f.name[:30]}")
                        continue
                    best = max(sim(tx, s) for s in src_map[ts])
                    if best < 0.7:
                        problems.append(f"时间锚文本差异({ts},sim={best:.2f}): {sub}/{f.name[:30]}")

print(f"总={stats['total']} 标杆={stats['bench']} 新精修={stats['new']}")
print(f"四章节齐全={stats['sec4_ok']}  正文内联帧={stats['inline_bad']}  冒号帧={stats['colon']}")
print(f"索引落地OK={stats['land_ok']}  落地失败={stats['land_fail']}  索引无帧={stats['no_idx']}")
print(f"\n问题清单共 {len(problems)} 条:")
for p in problems:
    print("  -", p)
