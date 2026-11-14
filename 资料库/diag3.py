# -*- coding: utf-8 -*-
import sys, glob, re, os
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document
REP="D:/Desktop/shandou/学习汇报"
ASSERT_T = re.compile(
    r"(?:实为|实际为|确认为|逐帧确认为|明确为|画面确认为|画面显示为|画面明确为|画面可读为|"
    r"应为|正确名称[为是]?|更正为|订正为|正名为|全名为|战法全名为|纠正为|即|名为|叫做|称为|叫)\s*[「『【]?"
)
files={
 "垒实篇评论抢点评":"垒实迎虚",
 "文鸯程昱":"豹文刀",
 "纯刀":"豹文刀",
}
for kw,tok in files.items():
    for f in glob.glob(REP+"/*"+kw+"*_逐帧深度学习报告_1秒版.docx"):
        doc=Document(f); text="\n".join(p.text for p in doc.paragraphs)
        for tbl in doc.tables:
            for row in tbl.rows:
                for c in row.cells: text+="\n"+c.text
        for m in re.finditer(re.escape(tok),text):
            pre=text[max(0,m.start()-16):m.start()]
            if ASSERT_T.search(pre):
                ctx=text[max(0,m.start()-50):m.end()+20].replace("\n"," ")
                print(f"[{tok}] {os.path.basename(f)[:26]}\n   {ctx}\n")
