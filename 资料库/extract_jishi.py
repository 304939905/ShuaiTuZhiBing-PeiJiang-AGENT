# -*- coding: utf-8 -*-
"""机势判定辅助：对4个含机势的完整版，抽取机势上下文；并在其1秒版中找击势/金吾飞将/机势出现情况。"""
import sys, os
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

REP = "D:/Desktop/shandou/学习汇报"
full_names = [
 "孟获就是南蛮版张机！ 这个新体系缔造者，你看懂了吗？_完整学习报告.docx",
 "孙权完全不适配张机 ，来看看有哪些常见误区_完整学习报告.docx",
 "全率土最细最全攻略合集攻其篇—粉丝投稿解析 来了!看看粉丝们的奇思妙想吧_完整学习报告.docx",
 "全率土最细最全攻略合集—垒实篇投稿讲解 来了!多多留言，后续会定期抽取评论解析队伍。_完整学习报告.docx",
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

for fn in full_names:
    fp = REP+"/"+fn
    if not os.path.exists(fp):
        print("MISSING full:", fn); continue
    doc = Document(fp)
    paras = text_of(doc)
    print("\n"+"="*72)
    print("完整版:", fn)
    print("--- 含「机势」的段落 (%d) ---" % sum(1 for p in paras if "机势" in p))
    for i,para in enumerate(paras):
        if "机势" in para:
            print(f"[{i}] {para}")
    one = fn.replace("_完整学习报告.docx","_逐帧深度学习报告_1秒版.docx")
    op = REP+"/"+one
    if not os.path.exists(op):
        print("MISSING 1秒版:", one); continue
    odoc = Document(op)
    oparas = text_of(odoc)
    jishi = [p for p in oparas if "击势" in p]
    jinwu = [p for p in oparas if "金吾飞将" in p]
    jishi_self = [p for p in oparas if "机势" in p]
    print("--- 1秒版: 击势出现 %d 段 / 金吾飞将 %d 段 / 机势 %d 段 ---" % (len(jishi),len(jinwu),len(jishi_self)))
    for tag,plist in (("击势",jishi),("金吾飞将",jinwu),("机势(若1秒版也有)",jishi_self)):
        for i,para in enumerate(plist):
            print(f"  [{tag} {i}] {para}")
