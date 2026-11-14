# -*- coding: utf-8 -*-
"""成立→程昱 抽核：对17个曾含"成立"的文件，抽取程昱上下文，判断是否为真·程昱(武将)还是"建立/成立"本义。"""
import sys, os
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

REP = "D:/Desktop/shandou/学习汇报"
files = [
 "两小一大保底说法是否属实？咱们一起长期进行记录验证。_完整学习报告.docx",
 "全率土最全攻略，战法篇! 重磅来袭!_完整学习报告.docx",
 "全率土最细最全攻略合集—垒实篇投稿讲解 来了!多多留言，后续会定期抽取评论解析队伍。_完整学习报告.docx",
 "全率土最细最全攻略合集攻其篇—粉丝投稿解析 来了!看看粉丝们的奇思妙想吧_完整学习报告.docx",
 "全率土最细最强攻略合集 神赏体系粉丝投稿解析，来了_完整学习报告.docx",
 "孙权完全不适配张机 ，来看看有哪些常见误区_完整学习报告.docx",
 "孟获就是南蛮版张机！ 这个新体系缔造者，你看懂了吗？_完整学习报告.docx",
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

def text_of(doc):
    out=[]
    for p in doc.paragraphs:
        if p.text.strip(): out.append(p.text)
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                if c.text.strip(): out.append(c.text)
    return out

for fn in files:
    fp = REP+"/"+fn
    if not os.path.exists(fp):
        print("MISSING:", fn); continue
    doc = Document(fp)
    paras = text_of(doc)
    hits=[(i,para) for i,para in enumerate(paras) if "程昱" in para]
    print("\n"+"="*72)
    print("文件:", fn, "| 程昱段落数:", len(hits))
    for i,para in hits:
        print(f"[{i}] {para}")
