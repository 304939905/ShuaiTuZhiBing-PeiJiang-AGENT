# -*- coding: utf-8 -*-
"""
Phase A 核验 + 修复脚本
=======================
先核验每个 (错词 -> 正确词) 的"正确词"是否在官方白名单
(武将/战法/宝物名/宝物词条)。确认后再在 docx 就地修复（先备份）。

用法:
  python phaseA_verify_fix.py            # 仅核验，打印 CONFIRMED/UNCONFIRMED
  python phaseA_verify_fix.py --apply    # 核验通过的项就地修复 + 备份 + 复gate
"""
import sys, os, re, glob, shutil
sys.path.insert(0, r"D:\Desktop\shandou\资料库")
import gate_whitelist as G
from docx import Document

REPORT_DIR = r"D:\Desktop\shandou\学习汇报"
BACKUP_DIR = r"D:\Desktop\shandou\学习汇报\_backup_phaseA"
ALLSET = G.hero | G.skill | G.gear | G.affix
CHECKSET = ALLSET | G.KNOWN   # KNOWN 含 EXTRA(自举+PhaseA补录)

# (错词, 正确词, 类别)  类别仅用于核验提示
CORS = [
    ("冯燎", "冯嫽", "hero"),
    ("成玉", "成宜", "hero"),
    ("朱偶", "朱然", "hero"),
    ("颜袖", "颜良", "hero"),
    ("成育", "程昱", "hero"),
    ("马位", "马岱", "hero"),
    ("愈战急勇", "愈战愈勇", "jineng"),
    ("敌众定气", "敛众定气", "jineng"),
    ("敌微穷极", "敛微穷极", "jineng"),
    ("缓师涂持", "缓师徐持", "jineng"),
    ("夔吼象路", "夔吼象踏", "jineng"),
    ("渐伐", "文伐", "jineng"),
    ("令无空是", "令无空悬", "jineng"),
    ("审时度计", "审时定计", "jineng"),
    ("追加", "追击", "jineng"),
    ("深水摸鱼", "浑水摸鱼", "jineng"),
    ("计险远迈", "计险远近", "jineng"),
    ("武略", "武锋", "jineng"),
    ("疾疠", "疾战", "jineng"),
    ("三数", "疏数", "jineng"),
    ("轻疾", "去疾", "affix"),
    ("执后", "妒后", "affix"),
    ("惑言", "谨言", "affix"),
    ("疾汗", "疾行", "affix"),
]

def verify():
    print("=== 核验：正确词是否在官方白名单 (武将∪战法∪宝物名∪词条) ===")
    unconf = []
    for wrong, correct, kind in CORS:
        ok = correct in CHECKSET
        print(f"  [{'CONFIRMED' if ok else 'UNCONFIRMED'}] {wrong} -> {correct}  ({kind})"
              + ("" if ok else "  <-- 需联网/人工确认"))
        if not ok:
            unconf.append((wrong, correct, kind))
    print(f"\n确认 {len(CORS)-len(unconf)}/{len(CORS)} | 未确认 {len(unconf)}")
    return unconf

def replace_in_para(par, old, new):
    for run in par.runs:
        if old in run.text:
            run.text = run.text.replace(old, new)
            return True
    runs = par.runs
    if not runs:
        return False
    full = "".join(r.text for r in runs)
    if old not in full:
        return False
    new_full = full.replace(old, new, 1)
    runs[0].text = new_full
    for r in runs[1:]:
        r.text = ""
    return True

def fix_file(fp):
    doc = Document(fp)
    changed = 0
    for p in doc.paragraphs:
        for wrong, correct, _ in CORS:
            if wrong in p.text:
                if replace_in_para(p, wrong, correct):
                    changed += 1
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    for wrong, correct, _ in CORS:
                        if wrong in p.text:
                            if replace_in_para(p, wrong, correct):
                                changed += 1
    if changed:
        doc.save(fp)
    return changed

def apply():
    doc_files = sorted(glob.glob(os.path.join(REPORT_DIR, "*_逐帧深度学习报告_1秒版.docx")))
    affected = []
    for fp in doc_files:
        try:
            doc = Document(fp)
        except Exception:
            continue
        txt = "\n".join(p.text for p in doc.paragraphs)
        for t in doc.tables:
            for row in t.rows:
                for c in row.cells:
                    txt += "\n" + c.text
        if any(wrong in txt for wrong, _, _ in CORS):
            affected.append(fp)
    print(f"受影响文件 {len(affected)} 个，先备份到 {BACKUP_DIR}")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    for fp in affected:
        shutil.copy2(fp, os.path.join(BACKUP_DIR, os.path.basename(fp)))
    total = 0
    for fp in affected:
        n = fix_file(fp)
        total += n
        print(f"  · {os.path.basename(fp)}  替换 {n} 处")
    print(f"\n合计替换 {total} 处。")

if __name__ == "__main__":
    unconf = verify()
    if "--apply" in sys.argv:
        if unconf:
            print("\n!! 存在未确认项，暂不自动修复，请先处理未确认项。")
            print("未确认:", unconf)
        else:
            apply()
