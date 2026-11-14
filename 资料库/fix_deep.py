# -*- coding: utf-8 -*-
import sys, shutil, glob, os
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

REP = "D:/Desktop/shandou/学习汇报"
BAK = os.path.join(REP, "_backup_before_errata")

# (文件名glob, [(旧, 新), ...])
RULES = [
    ("*率土武将志—文鸯*1秒版.docx", [
        ("「乘胜追击」详情：35% 发动",
         "「乘胜追击」详情：35% 发动（发动几率随战法等级在 25%–35% 区间，此为高等级取值；官网 stzb.163.com 战法库标注 25%–35%）"),
    ]),
    ("*率土武将志—魏晋篇*1秒版.docx", [
        ("「乘胜追击」详情页：S 级追击、发动率 25%、目标攻击目标",
         "「乘胜追击」详情页：S 级追击、发动率 25%（Lv.1；官方区间 25%–35%，随战法等级）、目标攻击目标"),
        ("，S 级追击、发动率 25%。",
         "，S 级追击、发动率 25%（Lv.1；官方区间 25%–35%，随战法等级）。"),
    ]),
    ("*史上最混乱的剧本*1秒版.docx", [
        ("战力部隊", "战力部队"),
    ]),
]

APPLY = "--apply" in sys.argv

for pat, subs in RULES:
    f = sorted(glob.glob(os.path.join(REP, pat)))
    if not f:
        print("!! 未找到:", pat); continue
    f = f[0]
    d = Document(f)
    full = "\n".join(p.text for p in d.paragraphs)
    total = 0
    for old, new in subs:
        c = full.count(old)
        total += c
        if c == 0:
            print(f"  [跳过] 未匹配: {old[:30]}")
        else:
            for p in d.paragraphs:
                if old in p.text:
                    p.text = p.text.replace(old, new)
            print(f"  [匹配 {c}] {old[:30]} -> {new[:30]}")
    if APPLY and total > 0:
        bak = os.path.join(BAK, os.path.basename(f).replace(".docx", "_deepfix.docx"))
        shutil.copy2(f, bak)
        d.save(f)
        print(f"  ✅ 已保存 + 备份: {os.path.basename(bak)}")
    elif total > 0:
        print(f"  (DRY-RUN) 将修改 {os.path.basename(f)} 共 {total} 处")
    print()
