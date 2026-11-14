from docx import Document
p = "D:/Desktop/shandou/学习成果汇总/旧56项目/全率土最细最全攻略合集攻其篇—粉丝投稿解析 来了!看看粉丝们的奇思妙想吧_精编学习报告.docx"
d = Document(p)
for ti, table in enumerate(d.tables):
    print(f"=== TABLE {ti} ===")
    for ri, row in enumerate(table.rows):
        for ci, cell in enumerate(row.cells):
            txt = cell.text.strip().replace("\n", " | ")
            if "钜黍" in txt or "吕布" in txt or "兀突骨" in txt or "中军" in txt or "大营" in txt:
                print(f"  [{ri},{ci}] {txt[:240]}")
