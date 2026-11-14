# -*- coding: utf-8 -*-
"""Step1 修复：将 3 处已官方三方核验确认的数值断言错误写入 docx。
备份目录：学习汇报/_backup_numeric/
修改清单（均为官方 skill_extra.json 金标准 + 网易大神 + 官网 stzb.163.com 三方核验确认）：
  1. 程昱魏智_1秒：「众谋不懈」(A级XP) -> (S级XP)   官方=指挥 S级
  2. 程昱魏智_1秒：「河内世泽」(A级)   -> (S级)      官方=主动 S级 距4
  3. 高顺群骑_完整：奇正之势是被动战法 -> 奇正之势是主动战法  官方=主动 B级
"""
import docx, os, shutil

REPORT_DIR = r"D:\Desktop\shandou\学习汇报"
FILES = {
    "程昱魏智最强搭配—所有细节一篇看懂 魏智的宝物你真的带对了吗？_逐帧深度学习报告_1秒版.docx": [
        ("「众谋不懈」(A级XP)", "「众谋不懈」(S级XP)"),
        ("「河内世泽」(A级)", "「河内世泽」(S级)"),
    ],
    "高顺领衔群骑，来了！ 8回合高频解控，四重增伤，非常均衡的一队。_完整学习报告.docx": [
        ("奇正之势是被动战法", "奇正之势是主动战法"),
    ],
}

def replace_in_text(obj, old, new, log):
    # obj: paragraph or cell-like (has .paragraphs)
    for p in obj.paragraphs:
        _replace_in_para(p, old, new, log)
    # tables inside
    for t in getattr(obj, "tables", []):
        for row in t.rows:
            for c in row.cells:
                replace_in_text(c, old, new, log)

def _replace_in_para(p, old, new, log):
    runs = p.runs
    if not runs:
        return
    full = "".join(r.text for r in runs)
    if old not in full:
        return
    if len(runs) == 1:
        runs[0].text = full.replace(old, new)
        log.append(("single-run", old, new))
        return
    # multi-run: rewrite first run, clear others (preserves single-run formatting in common case)
    runs[0].text = full.replace(old, new)
    for r in runs[1:]:
        r.text = ""
    log.append(("multi-run", old, new))

def main():
    for fname, repls in FILES.items():
        path = os.path.join(REPORT_DIR, fname)
        doc = docx.Document(path)
        log = []
        for old, new in repls:
            before = count_text(doc, old)
            replace_in_text(doc, old, new, log)
            after = count_text(doc, old)
            assert before >= 1, f"未找到待修复串：{old} 于 {fname}"
            assert after == 0, f"修复后仍存在：{old} 于 {fname}（剩余 {after}）"
            print(f"[OK] {fname}  替换 {old!r} -> {new!r}  (命中 {before})")
        doc.save(path)
        print(f"[SAVED] {fname}")

def count_text(doc, sub):
    n = 0
    for p in doc.paragraphs:
        n += "".join(r.text for r in p.runs).count(sub)
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                n += count_text(c, sub) if False else sum(("".join(r.text for r in pp.runs).count(sub)) for pp in c.paragraphs)
    return n

if __name__ == "__main__":
    main()
