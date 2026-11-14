from docx import Document

REPORTS = {
    "009_宝物焚决": r"D:/Desktop/shandou/报告库/旧56项目/精编/从零开始，宝物养成焚决，来了！ 刚进征服看见宝物系统，摸不着头脑？老是乱打一堆毫不适配的残品？别着急，北冥让你一篇看懂！_精编学习报告.docx",
    "013_神赏篇": r"D:/Desktop/shandou/报告库/旧56项目/精编/全率土最全攻略合集—神赏篇 来了! 评论投稿，下期解析哦!_精编学习报告.docx",
}

# 精确章节标题：旧 -> 新（顺移编号）
RENUMBER = {
    "五、涉及实体清单（官方库核验命中）": "四、涉及实体清单（官方库核验命中）",
    "六、局限与无法确认项": "五、局限与无法确认项",
    "七、AI 智能体主动推断内容（非视频原话，供参考）": "六、AI 智能体主动推断内容（非视频原话，供参考）",
}

for label, path in REPORTS.items():
    d = Document(path)
    # 1) 删对照表标题段
    for p in list(d.paragraphs):
        if p.text.strip() == "四、武将版本对照表（阵营-兵种-星级）":
            p._element.getparent().remove(p._element)
    # 2) 删唯一表格（T0 = 武将|版本标签）
    if d.tables:
        tbl = d.tables[0]
        tbl._element.getparent().remove(tbl._element)
    # 3) 顺移编号
    for p in d.paragraphs:
        t = p.text.strip()
        if t in RENUMBER:
            p.text = RENUMBER[t]
    d.save(path)
    print(f"[done] {label}")
