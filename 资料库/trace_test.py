#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""随机溯源测试: 抽10份精编, 每份随机一个[MM:SS]分析点, 按溯源规则取帧+视觉核验。
规则: 首帧与描述不符时, 查相邻 ±2~4 秒帧取匹配者(±4秒容差)。
"""
import sys, io, re, json, random
from pathlib import Path
import contextlib, importlib.util
import docx

ROOT = Path("D:/Desktop/shandou/报告库")
random.seed(20260820)
STOP = set("，。！？、：；（）「」『』 的了是在与和及个这那")

spec = importlib.util.spec_from_file_location("vg", "D:/Desktop/shandou/资料库/vision_glm.py")
vg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vg)
PROMPT = "识别这张《率土之滨》截图：1画面类型 2关键文字(战法名/武将名/数值) 3武将或战法名。简洁列出。"


def new_frame(dp, sec):
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return dp / f"frame_{sec+1:06d}_{h:02d}h{m:02d}m{s:02d}s000ms.jpg"


def vision(dp, sec):
    f = new_frame(dp, sec)
    if not f.exists():
        return None, "FRAME_MISSING"
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            sys.argv = ["vision_glm.py", str(f), PROMPT]
            vg.main()
        return f.name, buf.getvalue().strip()
    except SystemExit:
        return f.name, buf.getvalue().strip() or "EXIT"
    except Exception as e:
        return f.name, f"ERR {e!r}"


def ngram_overlap(a, b):
    grams = set()
    for n in (2, 3, 4):
        for i in range(max(0, len(a) - n + 1)):
            g = a[i:i + n]
            if g.isdigit() or any(c in STOP for c in g):
                continue
            grams.add(g)
    if not grams:
        return 0.0, []
    hits = [g for g in grams if g in b]
    return len(hits) / len(grams), hits[:6]


# 收集全部新精编
allf = []
for sub in ["旧56项目", "开荒", "海之呼唤", "赛季"]:
    d = ROOT / sub / "精编"
    for f in d.glob("*.docx"):
        if any(k in f.name for k in ["攻其篇—粉丝投稿解析", "神赏篇 来了! 评论投稿", "从零开始，宝物养成焚决"]):
            continue
        allf.append((sub, f))
pick = random.sample(allf, 10)

print("=" * 78)
results = []
for i, (sub, f) in enumerate(pick, 1):
    paras = [p.text for p in docx.Document(str(f)).paragraphs]
    full = "\n".join(paras)
    # 随机一个正文分析点
    pts = re.findall(r"^\[(\d\d):(\d\d)\]\s+(.+)", full, flags=re.M)
    if not pts:
        continue
    mm, ss, desc = random.choice(pts)
    sec = int(mm) * 60 + int(ss)
    dm = re.search(r"源静帧目录[:：]\s*(.+)", full)
    dp = Path(dm.group(1).strip().rstrip("/")) if dm else None
    # 溯源: 首帧
    fname, vtext = vision(dp, sec)
    ratio, hits = ngram_overlap(desc, vtext or "")
    status = "✓首帧匹配" if ratio >= 0.15 else ("△部分" if ratio >= 0.06 else "✗不符")
    # 若首帧不符: 按规则查 ±2~4 秒
    if ratio < 0.15:
        best = (ratio, sec, vtext, fname, hits)
        for delta in (2, 3, 4, -2, -3, -4):
            s2 = sec + delta
            if s2 < 0:
                continue
            n2, t2 = vision(dp, s2)
            r2, h2 = ngram_overlap(desc, t2 or "")
            if r2 > best[0]:
                best = (r2, s2, t2, n2, h2)
        if best[0] > ratio:
            status = f"邻帧修正({best[1]-sec:+d}s)"
            fname, vtext, ratio, hits = best[3], best[2], best[0], best[4]
        else:
            status += "(邻帧无更佳)"
    print(f"【{i}】[{sub}] {f.stem[:34]}")
    print(f"   随机锚点 [{mm}:{ss}] 描述: {desc[:60]}")
    print(f"   溯源帧: {fname}  判定: {status} (重叠率 {ratio:.2f})")
    print(f"   视觉识别: {(vtext or '')[:110]}")
    print("-" * 78)
