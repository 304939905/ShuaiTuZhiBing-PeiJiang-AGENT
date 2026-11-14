from docx import Document
p = "D:/Desktop/shandou/学习成果汇总/旧56项目/全率土最细最全攻略合集攻其篇—粉丝投稿解析 来了!看看粉丝们的奇思妙想吧_精编学习报告.docx"
d = Document(p)
for i, par in enumerate(d.paragraphs):
    t = par.text.strip()
    if not t:
        continue
    print(f"[{i}] {t}")
