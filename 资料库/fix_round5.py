# -*- coding: utf-8 -*-
"""第五轮勘误修复：断言型名称写错（"把错的改成另一个错的"）。
依据：官方 jineng 扩展白名单 + 网易大神(ds.163.com) 佐证。
安全：先整目录备份到 _backup_round5/，再原地改；run 级优先，跨 run 才合并段落。
用法: python fix_round5.py [--apply]   (不加 --apply 只预演)
"""
import sys, os, re, shutil, json
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

REP = "D:/Desktop/shandou/学习汇报"
BAK = REP + "/_backup_round5"
APPLY = "--apply" in sys.argv

# 文件名关键字 -> [(正则, 替换, 说明)]
FIX = {
    "率土武将志—贾诩 使用手册来了!一篇全看懂!_逐帧深度学习报告_1秒版.docx": [
        (r"久战魏犠", "久战熟谋", "OCR生僻字误识；官方库仅「久战熟谋」"),
    ],
    "程昱魏智最强搭配—所有细节一篇看懂 魏智的宝物你真的带对了吗？_逐帧深度学习报告_1秒版.docx": [
        (r"久战不殆", "久战熟谋", "成语化误写；官方库仅「久战熟谋」"),
        (r"磐阵擅守", "磐阵善守", "同音误写；官方名「磐阵善守」"),
        (r"河内(?!世泽)", "河内世泽", "战法名脱字；官方名「河内世泽」，完整版已正确"),
    ],
    "开荒专题（6 视频合并）_逐帧深度学习报告_1秒版.docx": [
        (r"磐阵擅守", "磐阵善守", "同音误写；官方名「磐阵善守」"),
    ],
    # 注意：规则按顺序执行。必须先做全局改名，再做整句改写，
    # 否则改写后新句中作为"引用"保留的旧错名会被后续规则二次误改。
    "全率土最细最全攻略合集攻其篇—粉丝投稿解析 来了!看看粉丝们的奇思妙想吧_逐帧深度学习报告_1秒版.docx": [
        (r"捋出关西", "将出关西", "字形误识；官方名「将出关西」"),
        (r"投稿二华雄第一位战法画面显示为「将出关西」，与常见战法库中的「措手不及/关西」等名称存在差异，以画面实际显示为准。",
         "投稿二华雄第一位战法画面显示为「将出关西」（A 级，官方战法库已收录）；此前因字形相近误识为「捋出关西」，"
         "亦与「措手不及/关西」等音近猜测混淆，现依官方战法库定名。",
         "整句改写：错名已定名（须在改名规则之后执行）"),
    ],
    "杜预垒实队，战报来了！ 一起来看看实战表现如何吧！_逐帧深度学习报告_1秒版.docx": [
        (r"以逸待劳", "以诱待来", "贾充战法；同片完整版及姊妹视频逐帧卡面均为「以诱待来」"),
    ],
    "全率土最全攻略合集！体系篇 ——战磐体系 来了！_完整学习报告.docx": [
        (r"是否程昱", "是否成立", "establish→程昱 误替换残留，回退为「成立」"),
    ],
}


def para_replace(p, pat, rep):
    """优先 run 级替换；跨 run 时合并到首 run（保留首 run 格式）。返回替换次数。"""
    n = 0
    for r in p.runs:
        if r.text and re.search(pat, r.text):
            new, k = re.subn(pat, rep, r.text)
            if k:
                r.text = new
                n += k
    if re.search(pat, p.text):          # 仍有残留 => 跨 run
        full, k = re.subn(pat, rep, p.text)
        if k:
            if p.runs:
                p.runs[0].text = full
                for r in p.runs[1:]:
                    r.text = ""
            n += k
    return n


def iter_paras(doc):
    for p in doc.paragraphs:
        yield p
    for tb in doc.tables:
        for row in tb.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    yield p


if APPLY and not os.path.isdir(BAK):
    os.makedirs(BAK)

summary = {}
total = 0
for fn, rules in FIX.items():
    path = os.path.join(REP, fn)
    if not os.path.exists(path):
        print(f"❌ 找不到: {fn}")
        continue
    if APPLY:
        shutil.copy2(path, os.path.join(BAK, fn))
    doc = Document(path)
    per = {}
    for pat, rep, why in rules:
        cnt = 0
        for p in iter_paras(doc):
            cnt += para_replace(p, pat, rep)
        per[pat] = {"n": cnt, "to": rep, "why": why}
        total += cnt
    if APPLY:
        doc.save(path)
    summary[fn] = per
    print(f"{'✔ 已改' if APPLY else '· 预演'} {fn[:46]}")
    for pat, v in per.items():
        print(f"      {pat[:24]} → {v['to'][:20]}   {v['n']} 处   ({v['why']})")

print(f"\n合计 {total} 处 / {len(summary)} 份 —— {'已写入' if APPLY else '预演（加 --apply 生效）'}")
if APPLY:
    print(f"备份目录: {BAK}")
json.dump(summary, open("D:/Desktop/shandou/资料库/fix_round5_report.json", "w",
                        encoding="utf-8"), ensure_ascii=False, indent=2)
