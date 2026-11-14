from docx import Document

REPORTS = {
    "009_宝物焚决": r"D:/Desktop/shandou/报告库/旧56项目/精编/从零开始，宝物养成焚决，来了！ 刚进征服看见宝物系统，摸不着头脑？老是乱打一堆毫不适配的残品？别着急，北冥让你一篇看懂！_精编学习报告.docx",
    "013_神赏篇": r"D:/Desktop/shandou/报告库/旧56项目/精编/全率土最全攻略合集—神赏篇 来了! 评论投稿，下期解析哦!_精编学习报告.docx",
}

for label, path in REPORTS.items():
    d = Document(path)
    full = "\n".join(p.text for p in d.paragraphs)
    heads = [p.text.strip() for p in d.paragraphs if p.text.strip()[:1] in "一二三四五六七八九十" and p.text.strip()[1:2] in "、．."]
    print("="*60); print(label); print("="*60)
    print("含『武将版本对照表』标题:", "武将版本对照表" in full)
    print("表格数:", len(d.tables))
    print("含『核心武将（版本）』开篇清单:", "核心武将（版本）" in full)
    print("章节序列:", heads)
    # 期望: 一、二、三、四(涉及实体)、五(局限)、六(AI推断)
    expect = ["一、","二、","三、","四、","五、","六、"]
    ok = all(h[:2]==e for h,e in zip(heads, expect))
    print("章节连续且编号正确(一至六):", ok)
    print()
