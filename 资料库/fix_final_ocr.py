# -*- coding: utf-8 -*-
"""
fix_final_ocr.py —— 用户肉眼确认后的最终 OCR 纠正（2026-08-09）

用户确认（基于 frame_0120_02-00 阵容详情 UI 截图）：
  - 甘宁宝物名 = **大柯斧**（非"大桐琴"，OCR 误识）
  - 大柯斧 词条 = **勇毅、列阵**（"勞駮"系 OCR 误识"勇毅"）
  - 两仪刀 词条 = **勇毅、守备**
  - 游飘 词条 = **迂回、地利**

结论：之前 fix_errata2.py 把 列阵/守备/迂回/地利 标为"兵种特性"是错的，
      它们就是这些宝物的自带词条。本脚本一并修正。
"""
import sys, shutil, glob, os, re
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

REP = "D:/Desktop/shandou/学习汇报"
BAK = os.path.join(REP, "_backup_before_errata")

APPLY = "--apply" in sys.argv

# ── 规则 ──
# 每条: (文件glob, [(旧串, 新串), ...])
RULES = [
    # ① 甘宁篇：大桐琴→大柯斧 + OCR存疑→勇毅 + 列阵/守备还原为宝物词条
    ("*甘宁带及锋*1秒版.docx", [
        # 宝物名
        ("大桐琴〔宝物名OCR存疑〕", "大柯斧"),
        ("大桐琴〔名称OCR存疑〕", "大柯斧"),
        ("大桐琴〔OCR存疑〕", "大柯斧"),
        ("大桐琴", "大柯斧"),
        # 词条：OCR存疑→勇毅
        ("宝物词条〔OCR存疑〕；列阵为兵种特性", "宝物词条【勇毅】【列阵】"),
        ("宝物词条〔OCR存疑〕；「列阵」为兵种特性非词条", "宝物词条【勇毅】【列阵】"),
        ("宝物词条〔OCR存疑〕", "宝物词条【勇毅】"),
        # 司马炎两仪刀：守备还原
        ("；「守备」为兵种特性非词条", "；宝物词条【勇毅】【守备】"),
        ("守备为兵种特性", "宝物词条【守备】"),
        # 孙权游飘：迂回/地利还原（如果甘宁篇也提到了）
        ("迂回为兵种特性", "宝物词条【迂回】"),
        ("地利为兵种特性", "宝物词条【地利】"),
    ]),
]

total_all = 0
for pat, subs in RULES:
    files = sorted(glob.glob(os.path.join(REP, pat)))
    if not files:
        print("!! 未找到:", pat); continue
    f = files[0]
    d = Document(f)
    full = "\n".join(p.text for p in d.paragraphs)
    total_f = 0
    for old, new in subs:
        c = full.count(old)
        if c == 0:
            continue
        total_f += c
        total_all += c
        for p in d.paragraphs:
            if old in p.text:
                p.text = p.text.replace(old, new)
        print(f"  [{c}×] {old[:40]} → {new[:40]}")
    if APPLY and total_f > 0:
        bak_name = os.path.basename(f).replace(".docx", "_finalocr.docx")
        bak_path = os.path.join(BAK, bak_name)
        shutil.copy2(f, bak_path)
        d.save(f)
        print(f"  ✅ 已保存 + 备份: {bak_name}")
    elif total_f > 0:
        print(f"  (DRY-RUN) 将修改 {os.path.basename(f)} 共 {total_f} 处")
    print()

# ── 验证 ──
if APPLY or True:
    f = sorted(glob.glob(os.path.join(REP, "*甘宁带及锋*1秒版.docx")))[0]
    t = "\n".join(p.text for p in Document(f).paragraphs)
    print("=== 修复后验证 ===")
    for k in ["大桐琴","勞駮","大柯斧","勇毅","列阵","兵种特性","OCR存疑"]:
        print(f"  {k}: {t.count(k)}")
    # 抽取关键句确认
    for m in re.finditer("大柯斧", t):
        s=max(0,m.start()-15);e=min(len(t),m.end()+50)
        print(f"  上下文: …{t[s:e].replace(chr(10),' ')}…")
