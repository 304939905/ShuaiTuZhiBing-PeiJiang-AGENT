from docx import Document

targets = {
    "009_宝物焚决": r"D:/Desktop/shandou/报告库/旧56项目/精编/从零开始，宝物养成焚决，来了！ 刚进征服看见宝物系统，摸不着头脑？老是乱打一堆毫不适配的残品？别着急，北冥让你一篇看懂！_精编学习报告.docx",
    "013_神赏篇": r"D:/Desktop/shandou/报告库/旧56项目/精编/全率土最全攻略合集—神赏篇 来了! 评论投稿，下期解析哦!_精编学习报告.docx",
}

for label, path in targets.items():
    d = Document(path)
    print("="*60); print(label, "表数:", len(d.tables)); print("="*60)
    for ti, tb in enumerate(d.tables):
        hdr = [c.text.strip() for c in tb.rows[0].cells]
        print(f"T{ti} 表头={hdr}  行数={len(tb.rows)}")
    print()
