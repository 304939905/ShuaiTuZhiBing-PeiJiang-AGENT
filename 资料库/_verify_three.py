import os
from docx import Document

base = "D:/Desktop/shandou/报告库/旧56项目/精编/"

def full_text(p):
    d = Document(p)
    parts = [par.text for par in d.paragraphs]
    for tbl in d.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for par in cell.paragraphs:
                    parts.append(par.text)
    return "\n".join(parts)

checks = {
    "攻其篇（粉丝投稿解析）": "全率土最细最全攻略合集攻其篇—粉丝投稿解析 来了!看看粉丝们的奇思妙想吧_精编学习报告.docx",
    "009 宝物焚决": "从零开始，宝物养成焚决，来了！ 刚进征服看见宝物系统，摸不着头脑？老是乱打一堆毫不适配的残品？别着急，北冥让你一篇看懂！_精编学习报告.docx",
    "013 神赏篇": "全率土最全攻略合集—神赏篇 来了! 评论投稿，下期解析哦!_精编学习报告.docx",
}

for name, fn in checks.items():
    p = base + fn
    t = full_text(p)
    print("="*60)
    print(name, "| 字节:", os.path.getsize(p), "| 字符:", len(t))
    if "攻其篇" in name:
        print("  AI推断章存在:", "AI 智能体主动推断" in t)
        print("  无 钜黍（吕布）:", "钜黍（吕布）" not in t)
        print("  无 钜黍(吕布)无括号:", "钜黍(吕布)" not in t)
    if "009" in name:
        print("  含 宝物系统:", "宝物系统" in t or "宝物" in t)
    if "013" in name:
        print("  含 神赏体系:", "神赏体系" in t)
