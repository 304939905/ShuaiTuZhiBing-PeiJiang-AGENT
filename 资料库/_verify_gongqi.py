from docx import Document
p = "D:/Desktop/shandou/学习成果汇总/旧56项目/全率土最细最全攻略合集攻其篇—粉丝投稿解析 来了!看看粉丝们的奇思妙想吧_精编学习报告.docx"
d = Document(p)
full = "\n".join(par.text for par in d.paragraphs)
print("段落数:", len(d.paragraphs))
print("含'凑不齐曹操':", "凑不齐曹操" in full)
print("含'低COST前排':", "低COST" in full)
for par in d.paragraphs:
    if "AI" in par.text and ("推断" in par.text or "主动" in par.text):
        print("AI章节行:", repr(par.text[:60]))
