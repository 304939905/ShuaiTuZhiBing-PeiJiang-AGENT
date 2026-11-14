# -*- coding: utf-8 -*-
"""官网数据核对后的最终 OCR 纠正：
   1) 甘宁1秒版：大桐琴→大柯斧（用户已确认），并清除误导性的〔OCR存疑〕标记
   2) 入门攻略完整版+1秒版：腾蛇→螣蛇（官网114宝物名清单为螣蛇）
"""
import sys
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document
from docx.oxml.ns import qn

REP = "D:/Desktop/shandou/学习汇报"

def replace_all_runs(doc, mapping):
    """mapping: {old: new}；按 <w:t> 节点做替换，保格式。"""
    changed = 0
    for p in doc.paragraphs:
        for r in p.runs:
            for old, new in mapping.items():
                if old in r.text:
                    r.text = r.text.replace(old, new)
                    changed += r.text.count(new)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for r in p.runs:
                        for old, new in mapping.items():
                            if old in r.text:
                                r.text = r.text.replace(old, new)
                                changed += r.text.count(new)
    return changed

# ---- 甘宁1秒版 ----
f1 = REP + "/这战法概率也太夸张了！ 也没人说甘宁带及锋概率能到80啊！_逐帧深度学习报告_1秒版.docx"
m1 = {
    "甘宁-大桐琴〔OCR存疑〕(〔词条OCR存疑〕/列阵)": "甘宁-大柯斧(勇毅/列阵)",
    "司马炎-两仪刀(〔词条OCR存疑〕/守备)": "司马炎-两仪刀(勇毅/守备)",
}
d1 = Document(f1)
c1 = replace_all_runs(d1, m1)
d1.save(f1)
print(f"甘宁1秒版 替换次数: {c1}")

# ---- 入门1秒版 ----
f2 = REP + "/全率土最全入门攻略合集!  来了!_逐帧深度学习报告_1秒版.docx"
d2 = Document(f2)
c2 = replace_all_runs(d2, {"腾蛇": "螣蛇"})
d2.save(f2)
print(f"入门1秒版 腾蛇→螣蛇 替换次数: {c2}")

# ---- 入门完整版 ----
f3 = REP + "/全率土最全入门攻略合集!  来了!_完整学习报告.docx"
d3 = Document(f3)
c3 = replace_all_runs(d3, {"腾蛇": "螣蛇"})
d3.save(f3)
print(f"入门完整版 腾蛇→螣蛇 替换次数: {c3}")

print("[完成] 三份报告已纠正并保存")
