#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""深挖 3 条真存疑: 扫帧定位证据帧。
1. 心愿武将: 找"官方规则原文截图"实际出现秒数
2. 攻其篇: 找"攻其不备战法卡"实际出现秒数
3. 垒实克制: 确认"杀"字帧内容
"""
import sys, io, re
from pathlib import Path
import contextlib, importlib.util
import docx

ROOT = Path("D:/Desktop/shandou/报告库")
PROMPT = "这是《率土之滨》游戏截图。请判断并回答：1画面类型(战法卡/规则说明/武将面板/片头/地图/其他) 2画面中可见的关键文字(逐字) 3是否有'杀'字。简洁回答。"

spec = importlib.util.spec_from_file_location("vg", "D:/Desktop/shandou/资料库/vision_glm.py")
vg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vg)

# (报告, 帧目录, 扫描秒点)
SCANS = [
    ("旧56项目", "一篇看懂心愿武将所有细节 多少玉一张保底，积分能否保留？一篇全看懂_精修学习报告.docx", range(6, 36, 3)),
    ("旧56项目", "全率土最细最全攻略合集—攻其篇 评论区投稿，下期点评队伍哦_精修学习报告.docx", range(3, 33, 3)),
    ("旧56项目", "垒实体系克制关系，来了! 下期带来大量粉丝投稿解析，期待一下有没有你!_精修学习报告.docx", range(0, 25, 2)),
]

def probe(dp, sec):
    mm, ss = sec // 60, sec % 60
    # 探测命名模式
    ff = sorted(dp.glob("frame_*.jpg"))
    if not ff:
        return None, "NO_FRAMES"
    mode = "sec"
    if len(ff) >= 2:
        fm = re.match(r"frame_(\d+)_(\d{2})-(\d{2})", ff[1].name)
        if fm and int(fm.group(1)) > 0:
            fsec = int(fm.group(2)) * 60 + int(fm.group(3))
            if fsec > 0 and int(fm.group(1)) / fsec >= 25:
                mode = "x30"
    idx = sec * 30 if mode == "x30" else sec
    cand = dp / f"frame_{idx:04d}_{mm:02d}-{ss:02d}.jpg"
    if not cand.exists():
        return None, f"MISSING({mode})"
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
    return cand, text

for sub, fname, secs in SCANS:
    f = ROOT / sub / "精编" / fname
    full = "\n".join(p.text for p in docx.Document(str(f)).paragraphs)
    dm = re.search(r"源静帧目录[:：]\s*(.+)", full)
    dp = Path(dm.group(1).strip().rstrip("/")) if dm else None
    print("=" * 64)
    print(f"[{sub}] {fname[:40]}")
    if not dp:
        print("  无帧目录")
        continue
    for s in secs:
        cand, text = probe(dp, s)
        tag = cand.name if cand else "?"
        brief = (text or "")[:110].replace("\n", " ")
        print(f"  {s:>3}s {tag}: {brief}")
