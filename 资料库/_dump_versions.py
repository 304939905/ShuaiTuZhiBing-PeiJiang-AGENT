import sys
from docx import Document

targets = {
    "009_宝物焚决": r"D:/Desktop/shandou/报告库/旧56项目/精编/从零开始，宝物养成焚决，来了！ 刚进征服看见宝物系统，摸不着头脑？老是乱打一堆毫不适配的残品？别着急，北冥让你一篇看懂！_精编学习报告.docx",
    "013_神赏篇": r"D:/Desktop/shandou/报告库/旧56项目/精编/全率土最全攻略合集—神赏篇 来了! 评论投稿，下期解析哦!_精编学习报告.docx",
}

def scan(path, label):
    print("="*70)
    print(label)
    print("="*70)
    d = Document(path)
    # paragraphs
    for i, p in enumerate(d.paragraphs):
        t = p.text.strip()
        if not t: 
            continue
        if ("武将" in t) or ("版本" in t) or ("对照" in t) or ("索引" in t) or ("核心" in t):
            print(f"[P{i}] {t[:90]}")
    # tables
    for ti, tb in enumerate(d.tables):
        for ri, row in enumerate(tb.rows):
            cells = [c.text.strip() for c in row.cells]
            joined = " | ".join(cells)
            if ("武将" in joined) or ("版本" in joined) or ("对照" in joined) or ("阵营" in joined) or ("自带" in joined):
                print(f"[T{ti}R{ri}] {joined[:120]}")
    print()

for k, v in targets.items():
    scan(v, k)
