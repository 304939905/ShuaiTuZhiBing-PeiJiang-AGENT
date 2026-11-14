# -*- coding: utf-8 -*-
"""按用户确认执行：机势14处→击势（4文件）；程昱19处逻辑连词误改→回退成立（17文件，保留真·武将程昱）。
   先备份到 _backup_before_errata/20260809_jishi_chengyu/，再 run 级替换（段落+表格）。"""
import sys, os, glob, shutil, json
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

REP = "D:/Desktop/shandou/学习汇报"
BAK = REP + "/_backup_before_errata/20260809_jishi_chengyu"
os.makedirs(BAK, exist_ok=True)

jishi_files = [
 "孟获就是南蛮版张机！ 这个新体系缔造者，你看懂了吗？_完整学习报告.docx",
 "孙权完全不适配张机 ，来看看有哪些常见误区_完整学习报告.docx",
 "全率土最细最全攻略合集攻其篇—粉丝投稿解析 来了!看看粉丝们的奇思妙想吧_完整学习报告.docx",
 "全率土最细最全攻略合集—垒实篇投稿讲解 来了!多多留言，后续会定期抽取评论解析队伍。_完整学习报告.docx",
]
chengyu_files = [
 "两小一大保底说法是否属实？咱们一起长期进行记录验证。_完整学习报告.docx",
 "全率土最全攻略，战法篇! 重磅来袭!_完整学习报告.docx",
 "全率土最细最全攻略合集攻其篇—粉丝投稿解析 来了!看看粉丝们的奇思妙想吧_完整学习报告.docx",
 "全率土最细最强攻略合集 神赏体系粉丝投稿解析，来了_完整学习报告.docx",
 "孙权完全不适配张机 ，来看看有哪些常见误区_完整学习报告.docx",
 "平民种地焚决来了 10天必过两万五势力，无限套娃开分法，全赛季稳定过势力值任务，丝滑过渡金币期，稳扎稳打步步为营。_完整学习报告.docx",
 "徐庶能玩吗？ 当然可以，平民极佳的战磐选择，来了！_完整学习报告.docx",
 "杜预垒实队，战报来了！ 一起来看看实战表现如何吧！_完整学习报告.docx",
 "率土最细最全攻略合集—垒实篇 评论抢点评! 把你们的垒实配队放在评论区哦!下期抽取点评别错过!_完整学习报告.docx",
 "纯刀居然还有上升空间？ 一个改动，拉高强度_完整学习报告.docx",
 "装糖队到底糖不糖 一支拉满细节的队伍，非常值得推敲。  原创队伍。_完整学习报告.docx",
 "距离思路究极细节 ，普攻距离和战法距离，真的是越远越好吗？_完整学习报告.docx",
 "这战法概率也太夸张了！ 也没人说甘宁带及锋概率能到80啊！_完整学习报告.docx",
 "配将焚决来了 全体系队伍搭建思路最后一期，真焚决—宏观配将法，来了! 跟合集内容全部融会贯通，你也能成配将大手子!_完整学习报告.docx",
 "高顺领衔群骑，来了！ 8回合高频解控，四重增伤，非常均衡的一队。_完整学习报告.docx",
]

# 程昱 回退模式（仅逻辑连词用法；真·武将程昱 如「中军换程昱」/武将列表 不匹配）
CHENGYU_PATTERNS = [
 ("是否程昱", "是否成立"), ("不程昱", "不成立"), ("才程昱", "才成立"),
 ("都程昱", "都成立"), ("仍程昱", "仍成立"), ("同时程昱", "同时成立"),
 ("能否程昱", "能否成立"), ("稳定程昱", "稳定成立"), ("规律程昱", "规律成立"),
 ("程昱的前提", "成立的前提"), ("不能同时程昱", "不能同时成立"),
 ("保护组合程昱", "成立"), ("保护程昱", "保护成立"), ("前提下程昱", "前提下成立"),
]

def replace_runs(doc, mappings):
    counts = {}
    def do(paras):
        for p in paras:
            for r in p.runs:
                t = r.text
                for old, new in mappings:
                    if old in t:
                        c = t.count(old); t = t.replace(old, new)
                        counts[old] = counts.get(old, 0) + c
                if t != r.text:
                    r.text = t
    do(doc.paragraphs)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                do(cell.paragraphs)
    return counts

# 备份受影响文件（去重并集）
all_files = list(dict.fromkeys(jishi_files + chengyu_files))
for fn in all_files:
    src = REP + "/" + fn
    if os.path.exists(src):
        shutil.copy2(src, BAK + "/" + fn)
print(f"[备份] {len(all_files)} 个文件 → {BAK}")

log = []
# 机势 → 击势
for fn in jishi_files:
    fp = REP + "/" + fn
    if not os.path.exists(fp): continue
    doc = Document(fp)
    c = replace_runs(doc, [("机势", "击势")])
    if c:
        doc.save(fp)
        log.append(f"[机势→击势] {fn}: {c}")

# 程昱 逻辑连词误改 → 回退成立
for fn in chengyu_files:
    fp = REP + "/" + fn
    if not os.path.exists(fp): continue
    doc = Document(fp)
    c = replace_runs(doc, CHENGYU_PATTERNS)
    if c:
        doc.save(fp)
        log.append(f"[程昱→成立] {fn}: {c}")

print("\n".join(log))
json.dump({"jishi": jishi_files, "chengyu": chengyu_files, "log": log},
          open("D:/Desktop/shandou/资料库/fix_jishi_chengyu_log.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n[完成] 机势替换 {sum(1 for l in log if '机势' in l)} 文件；程昱回退 {sum(1 for l in log if '程昱' in l)} 文件")
