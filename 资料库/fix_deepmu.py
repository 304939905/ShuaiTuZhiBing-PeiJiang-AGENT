# -*- coding: utf-8 -*-
"""修复 深谋远虑 类型笔误：A主动 -> A被动（官方 stzb.163.com 2018-04-03 公告 + newton 双源确认）。"""
import docx, os
f = "D:/Desktop/shandou/学习汇报/全率土最全攻略，战法篇! 重磅来袭!_逐帧深度学习报告_1秒版.docx"
d = docx.Document(f)
cnt = 0
old = "深谋远虑（A主动）"
new = "深谋远虑（A被动）"
for para in d.paragraphs:
    if old in para.text:
        para.text = para.text.replace(old, new)
        cnt += 1
        print("paragraph fixed:", para.text[:80])
for t in d.tables:
    for r in t.rows:
        for c in r.cells:
            if old in c.text:
                c.text = c.text.replace(old, new)
                cnt += 1
                print("table fixed")
d.save(f)
print("total replaced:", cnt)
