#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""视觉核验汇总: 报告首条分析点文本 vs 视觉识别文本, 一致性判定。
判定: 用报告文本中的游戏关键词(武将名/常见UI词)在视觉识别文本中的命中率。
输出: 一致/存疑清单 + 汇总报告 资料库/VERIFY_VISION.md
"""
import json, re
from pathlib import Path
import docx

ROOT = Path("D:/Desktop/shandou/报告库")
DATA = json.load(open("D:/Desktop/shandou/资料库/_vision_verify.json", encoding="utf-8"))

def extract_first_point(report_path):
    paras = [p.text for p in docx.Document(str(report_path)).paragraphs]
    full = "\n".join(paras)
    m = re.search(r"^\[\d\d:\d\d\]\s+(.+)", full, flags=re.M)
    return m.group(1) if m else None


STOP = set("，。！？、：；（）「」『』 的了是在与和及个这那")


def ngram_hits(report_text, vision_text):
    """报告文本 2-4gram, 统计出现在视觉文本中的比例与命中样本(实体级重叠)。"""
    grams = set()
    for n in (2, 3, 4):
        for i in range(max(0, len(report_text) - n + 1)):
            g = report_text[i:i + n]
            if g.isdigit():
                continue
            if any(c in STOP for c in g):
                continue
            grams.add(g)
    hits = sorted(g for g in grams if g in vision_text)
    return len(hits) / max(len(grams), 1), hits


def judge(report_text, vision_text):
    if not report_text or not vision_text or vision_text in ("NO_FRAME", "FRAME_MISSING", "NO_ANCHOR"):
        return "无法判断", 0.0, []
    if vision_text.startswith("ERR") or vision_text == "EXIT":
        return "无法判断", 0.0, []
    ratio, hits = ngram_hits(report_text, vision_text)
    if ratio >= 0.15:
        return "一致", ratio, hits[:10]
    if ratio >= 0.06:
        return "部分一致", ratio, hits[:10]
    return "存疑", ratio, hits[:10]

rows = []
for x in DATA:
    rep = ROOT / x["sub"] / "精编" / x["report"]
    desc = extract_first_point(rep)
    verdict, ratio, hits = judge(desc, x["vision_text"])
    rows.append({**x, "desc": desc, "verdict": verdict, "ratio": ratio, "hits": hits})

ok = [r for r in rows if r["verdict"] == "一致"]
partial = [r for r in rows if r["verdict"] == "部分一致"]
doubt = [r for r in rows if r["verdict"] == "存疑"]
na = [r for r in rows if r["verdict"] == "无法判断"]

lines = ["# 视觉交叉核验汇总", "",
         f"总核验: {len(rows)} 一致: {len(ok)} 部分一致: {len(partial)} 存疑: {len(doubt)} 无法判断: {len(na)}", ""]
if doubt:
    lines += ["## 存疑清单(需人工复查)", ""]
    for r in doubt:
        lines += [f"- [{r['sub']}] {r['report'][:40]} (命中率 {r['ratio']:.2f})",
                  f"  报告: {(r['desc'] or '')[:90]}",
                  f"  视觉: {(r['vision_text'] or '')[:140]}", ""]
if partial:
    lines += ["## 部分一致(参考)", ""]
    for r in partial:
        lines += [f"- [{r['sub']}] {r['report'][:40]} (命中 {r['ratio']:.2f}): {r['hits']}", ""]
if na:
    lines += ["## 无法判断(无关键词或无帧)", ""]
    for r in na:
        lines += [f"- [{r['sub']}] {r['report'][:40]}", ""]
lines += ["## 一致样例(前5)", ""]
for r in ok[:5]:
    lines += [f"- [{r['sub']}] {r['report'][:40]} 命中 {r['hits']}", ""]

out = "\n".join(lines)
Path("D:/Desktop/shandou/资料库/VERIFY_VISION.md").write_text(out, encoding="utf-8")
print(out)
print(f"\n[已写 资料库/VERIFY_VISION.md]")
