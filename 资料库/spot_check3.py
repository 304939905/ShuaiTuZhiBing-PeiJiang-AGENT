#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""深度抽检 3 份存疑项: 取报告首条时间锚 ±2 秒共 5 帧, 逐帧视觉识别, 输出对照。"""
import sys, io, json, re
from pathlib import Path
import contextlib, importlib.util
import docx

ROOT = Path("D:/Desktop/shandou/报告库")
TARGETS = [
    ("旧56项目", "率土武将志—贾诩 使用手册来了!一篇全看懂!_精修学习报告.docx"),
    ("旧56项目", "一篇看懂心愿武将所有细节 多少玉一张保底，积分能否保留？一篇全看懂_精修学习报告.docx"),
    ("赛季", "最强四星0氪蜀之智，萌新玩家必看_精修学习报告.docx"),
]
PROMPT = "这是《率土之滨》游戏截图，请精确识别：1画面类型(战法卡/武将面板/阵容/地图/片头等) 2可见文字(逐字识别战法名/武将名/数值) 3武将或战法名。重点：战法名、武将名、数值务必准确。"

spec = importlib.util.spec_from_file_location("vg", "D:/Desktop/shandou/资料库/vision_glm.py")
vg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vg)

for sub, fname in TARGETS:
    f = ROOT / sub / "精编" / fname
    paras = [p.text for p in docx.Document(str(f)).paragraphs]
    full = "\n".join(paras)
    # 报告首条分析点
    m = re.search(r"^\[(\d\d):(\d\d)\]\s+(.+)", full, flags=re.M)
    mm, ss = m.group(1), m.group(2)
    sec = int(mm) * 60 + int(ss)
    desc = m.group(3)
    dm = re.search(r"源静帧目录[:：]\s*(.+)", full)
    dp = Path(dm.group(1).strip().rstrip("/")) if dm else None
    print("=" * 66)
    print(f"[{sub}] {fname[:38]}")
    print(f"时间锚: {mm}:{ss} (sec={sec})  目录: {dp.name if dp else '?'}")
    print(f"报告原文: {desc[:150]}")
    # ±2 秒 5 帧
    for delta in (-2, -1, 0, 1, 2):
        s2 = sec + delta
        if s2 < 0:
            continue
        mm2, ss2 = s2 // 60, s2 % 60
        cand = dp / f"frame_{s2:04d}_{mm2:02d}-{ss2:02d}.jpg"
        if not cand.exists():
            print(f"  [{delta:+d}s] 帧缺失: {cand.name}")
            continue
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                sys.argv = ["vision_glm.py", str(cand), PROMPT]
                vg.main()
            text = buf.getvalue().strip()
        except SystemExit:
            text = buf.getvalue().strip() or "EXIT"
        except Exception as e:
            text = f"ERR {e!r}"
        print(f"  [{delta:+d}s {cand.name}] {text[:220]}")
        print("  " + "-" * 40)
