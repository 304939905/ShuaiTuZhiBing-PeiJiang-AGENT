# -*- coding: utf-8 -*-
"""按 VERIFY_REPORT.md 的勘误清单，修正 docx 中的事实错误（段落级安全替换，保留插图）"""
import os, re, shutil, sys
from docx import Document

ROOT = r"D:\Desktop\shandou"
REP = os.path.join(ROOT, "学习汇报")
BAK = os.path.join(ROOT, "学习汇报", "_backup_before_errata")
os.makedirs(BAK, exist_ok=True)

# ---- 勘误规则：文件关键词 -> [(旧, 新), ...]  按长串优先顺序排列
RULES = {
    "这战法概率也太夸张": [
        # 3 先替换长句（推算式），避免被短规则打断
        ("完整计算式可还原：及锋而试基础35% + 像掠如火约11%(满级) + 司马炎谋议宏图增幅49%中的发动率部分(约35-36%) + 宝物词条英勇/筹算加成 ≈ 82%。注：画面未一次性展示完整加法算式，各项分见于不同帧。",
         "完整计算式可还原（乘算模型，已核验）：（及锋而试基础35% + 侵掠如火满级20%）× (1 + 司马炎谋议宏图增幅49%) = 55% × 1.49 ≈ 82%，与画面完全吻合。同法验证汜水关：(30% + 20%) × 1.49 ≈ 74.5% ≈ 74%。注：画面未一次性展示算式，本式由官方战法数值反推并经算术校验。"),
        # 2 满级标注
        ("A级被动，使主动战法发动率提升10.0%>>11.1%（满级），攻击时30.0%几率本次攻击伤害提高25.0%>>27.8%。",
         "A级被动，画面显示当前等级下主动战法发动率提升10.0%>>11.1%（Lv.1>>Lv.2，非满级；官方满级为攻击类主动战法发动率+20.0%），攻击时30.0%几率本次攻击伤害提高25.0%>>27.8%。"),
        ("A级被动，Lv.1>>Lv.2，主动战法发动率提升10.0%>>11.1%，攻击时30.0%几率的本次攻击伤害提高25.0%>>27.8%。",
         "A级被动，Lv.1>>Lv.2，主动战法发动率提升10.0%>>11.1%（官方满级为攻击类主动战法发动率+20.0%），攻击时30.0%几率的本次攻击伤害提高25.0%>>27.8%。"),
        # 7 赞诗误配（长串必须排在短串之前）
        ("S級「及锋而试」+ A級「汜水关」（描述：飞廉带铃任侠精，负江东斗将名）",
         "S级「及锋而试」+ 典藏战法「汜水关」（同屏「飞廉带铃任侠精，负江东斗将名」为甘宁赞诗，非战法描述）"),
        ("A級「汜水关」（描述：飞廉带铃任侠精，负江东斗将名）",
         "典藏战法「汜水关」（同屏「飞廉带铃任侠精，负江东斗将名」为甘宁武将赞诗，非本战法描述）"),
        # 8 汜水关级别
        ("「汜水关」（A級主动战法）", "「汜水关」（典藏攻击战法）"),
        # 5 游騎
        ("游騎", "游飘"),
        # 6 大桐琴
        ("大桐琴", "大桐琴〔OCR存疑〕"),
        # 4 勞駮
        ("勞駮", "〔词条OCR存疑〕"),
        # 1 像掠如火
        ("像掠如火", "侵掠如火"),
        # 繁体级别标记归一
        ("A級", "A级"), ("S級", "S级"),
    ],
    "马超纯刀最强配置": [
        ("【日宁】", "【甘宁】"),
        ("日宁", "甘宁"),
    ],
}


def replace_in_paragraph(par, old, new):
    """段落级替换，尽量保留格式：若单 run 命中直接换；否则合并到第一个 run"""
    if old not in par.text:
        return 0
    n = par.text.count(old)
    # 尝试 run 内替换
    done = 0
    for r in par.runs:
        if old in r.text:
            c = r.text.count(old)
            r.text = r.text.replace(old, new)
            done += c
    if done == n:
        return done
    # 跨 run：合并
    full = par.text.replace(old, new)
    if par.runs:
        par.runs[0].text = full
        for r in par.runs[1:]:
            r.text = ""
    return n


def fix_doc(path, rules):
    d = Document(path)
    total = {}
    targets = list(d.paragraphs)
    for t in d.tables:
        for row in t.rows:
            for cell in row.cells:
                targets.extend(cell.paragraphs)
    for old, new in rules:
        c = 0
        for par in targets:
            c += replace_in_paragraph(par, old, new)
        if c:
            total[old] = c
    if total:
        d.save(path)
    return total


apply = "--apply" in sys.argv
docs = [f for f in os.listdir(REP) if f.endswith(".docx") and not f.startswith("~$")]

for key, rules in RULES.items():
    hits = [f for f in docs if key in f]
    for f in hits:
        p = os.path.join(REP, f)
        if apply:
            shutil.copy2(p, os.path.join(BAK, f))
        # 先统计
        d = Document(p)
        txt = "\n".join(x.text for x in d.paragraphs)
        pre = {old: txt.count(old) for old, _ in rules if txt.count(old)}
        print(f"\n--- {f}")
        for k, v in pre.items():
            print(f"    命中 {v:>2} 次: {k[:60]}")
        if apply and pre:
            res = fix_doc(p, rules)
            print(f"    => 已替换: {sum(res.values())} 处，备份于 _backup_before_errata/")

if not apply:
    print("\n[DRY-RUN] 加 --apply 实际执行")
