# -*- coding: utf-8 -*-
"""验证机势/程昱修复：机势=0；程昱仅剩真·武将名；无establish误改残留；0损坏。"""
import sys, os, glob
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

REP = "D:/Desktop/shandou/学习汇报"
jishi = [
 "孟获就是南蛮版张机！ 这个新体系缔造者，你看懂了吗？_完整学习报告.docx",
 "孙权完全不适配张机 ，来看看有哪些常见误区_完整学习报告.docx",
 "全率土最细最全攻略合集攻其篇—粉丝投稿解析 来了!看看粉丝们的奇思妙想吧_完整学习报告.docx",
 "全率土最细最全攻略合集—垒实篇投稿讲解 来了!多多留言，后续会定期抽取评论解析队伍。_完整学习报告.docx",
]
chengyu = [
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
EST = ["是否程昱","不程昱","才程昱","都程昱","仍程昱","同时程昱","能否程昱","稳定程昱","规律程昱","程昱的前提","不能同时程昱","保护组合程昱","前提下程昱"]
broken = []

def full_text(doc):
    t = "\n".join(p.text for p in doc.paragraphs)
    for tbl in doc.tables:
        for row in tbl.rows:
            for c in row.cells:
                t += "\n" + c.text
    return t

print("=== 机势检查（应全=0，击势>0）===")
for fn in jishi:
    doc = Document(REP+"/"+fn); txt = full_text(doc)
    print(f"  {fn[:18]}... 机势={txt.count('机势')} 击势={txt.count('击势')}")

print("\n=== 程昱 establish 误改残留（应全=0）===")
bad = 0
for fn in chengyu:
    doc = Document(REP+"/"+fn); txt = full_text(doc)
    hits = [e for e in EST if e in txt]
    if hits:
        bad += 1
        print(f"  [残留] {fn[:18]}...: {hits}")
print(f"  含establish残留的文件数: {bad}")

print("\n=== 真·武将程昱 保留检查（应>0）===")
for fn in ["徐庶能玩吗？ 当然可以，平民极佳的战磐选择，来了！_完整学习报告.docx",
          "率土最细最全攻略合集—垒实篇 评论抢点评! 把你们的垒实配队放在评论区哦!下期抽取点评别错过!_完整学习报告.docx"]:
    doc = Document(REP+"/"+fn); txt = full_text(doc)
    print(f"  {fn[:18]}... 程昱={txt.count('程昱')} (中军换程昱出现={txt.count('中军换')})")

print("\n=== 文件可打开性 ===")
for f in sorted(glob.glob(REP+"/*_完整学习报告.docx")):
    try: Document(f)
    except Exception as e:
        broken.append((os.path.basename(f), str(e)))
print("  损坏文件:", broken if broken else "无（0 损坏）")
