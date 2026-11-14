from docx import Document
p = "D:/Desktop/shandou/学习成果汇总/旧56项目/全率土最细最全攻略合集攻其篇—粉丝投稿解析 来了!看看粉丝们的奇思妙想吧_精编学习报告.docx"
d = Document(p)

para = "\n".join(par.text for par in d.paragraphs)
tbl = []
for t in d.tables:
    for r in t.rows:
        for c in r.cells:
            tbl.append(c.text)
table_text = "\n".join(tbl)
alltext = para + "\n" + table_text

checks = {
    "钜黍（吕布）": "钜黍（吕布）" in alltext,
    "中军位的兀突骨": "中军位的兀突骨" in alltext,
    "兀突骨为中线将": "兀突骨为中线将" in alltext,
    "需确认其站位为「中军」": "需确认其站位为" in alltext,
    "凑不齐曹操…低COST独立建议段": ("凑不齐曹操" in alltext and "低COST" in alltext),
    "群-木鹿大王-骑-5星(内嵌名)": "群-木鹿大王-骑-5星" in alltext,
    "群-祝融夫人-骑-5星(内嵌名)": "群-祝融夫人-骑-5星" in alltext,
    "群-兀突骨-步-5星(内嵌名)": "群-兀突骨-步-5星" in alltext,
}
print("=== 残留检查（应为 False）===")
for k,v in checks.items():
    print(f"  [{ 'FAIL' if v else 'OK  '}] {k}: {v}")

print("\n=== 关键内容存在性 ===")
print("  投稿三 takeaway=吕布转长弓即可；张辽配大将 :", "吕布转长弓即可；张辽配大将" in table_text)
print("  替换表述 用兀突骨替换大营位置的祝融 :", "用兀突骨替换大营位置的祝融" in alltext)
print("  AI推断章标题 :", "六、AI 智能体主动推断内容（非视频原话，供参考）" in para)
print("  位置非强制说明 :", "推荐站位只是系统建议" in alltext)
print("  开头版本清单(祝融夫人（群-骑-5星）) :", "祝融夫人（群-骑-5星）" in para)
# 表格武将列是否仍带版本(应为 True，作为参考结构保留)
print("  表格武将列带版本(参考结构,应True) :", "吕布（群-弓-5星）" in table_text)
