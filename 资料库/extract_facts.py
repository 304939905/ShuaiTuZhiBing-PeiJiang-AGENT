# -*- coding: utf-8 -*-
"""从 51 份 1 秒版报告中提取「可核实事实项」：战法/武将 + 百分比数值，形成待核清单"""
import os, re, json, collections
from docx import Document

ROOT = r"D:\Desktop\shandou"
REP = os.path.join(ROOT, "学习汇报")

docs = sorted(f for f in os.listdir(REP)
              if f.endswith("_逐帧深度学习报告_1秒版.docx") and not f.startswith("~$"))

# 句子中含百分比 & 含"发动率/几率/概率/伤害率/恢复率/减伤/提高/降低"的，视为事实项
KEY = re.compile(r"(发动率|发动几率|触发率|概率|几率|伤害率|恢复率|减伤|增伤|提高|降低|提升|无视|免疫)")
PCT = re.compile(r"\d+(?:\.\d+)?%")

facts = []
name_hits = collections.Counter()

# 疑似 OCR/听写可疑词（繁体混入、罕见字）
SUSPECT = re.compile(r"[勞駮騎級聲畫戰將軍術鐵劍嚴顏權關張趙雲呂佈]")

for f in docs:
    d = Document(os.path.join(REP, f))
    stem = f[: -len("_逐帧深度学习报告_1秒版.docx")]
    for par in d.paragraphs:
        t = par.text.strip()
        if not t:
            continue
        # 按句切
        for s in re.split(r"[。；\n]", t):
            s = s.strip()
            if not s:
                continue
            if PCT.search(s) and KEY.search(s):
                facts.append({"report": stem, "sent": s})
        # 繁体/可疑字统计
        for m in SUSPECT.finditer(t):
            # 取上下文 6 字
            i = m.start()
            name_hits[t[max(0, i-4): i+5]] += 1

print(f"报告数 {len(docs)}，提取事实句 {len(facts)} 条")

# 按「战法名」聚合：抓中文书名号/引号内的名字
TERM = re.compile(r"[「『【\"]([^」』】\"]{2,8})[」』】\"]")
by_term = collections.defaultdict(list)
for it in facts:
    for m in TERM.finditer(it["sent"]):
        by_term[m.group(1)].append(it)

print(f"涉及带名术语 {len(by_term)} 个")
top = sorted(by_term.items(), key=lambda kv: -len(kv[1]))[:40]
print("\n【高频事实项术语 TOP40】")
for k, v in top:
    print(f"  {len(v):>3}  {k}")

print("\n【疑似繁体/OCR 可疑片段 TOP30】")
for k, c in name_hits.most_common(30):
    print(f"  {c:>3}  {k}")

with open(os.path.join(ROOT, "资料库", "facts_index.json"), "w", encoding="utf-8") as fp:
    json.dump({"facts": facts,
               "by_term": {k: [x["sent"] for x in v] for k, v in by_term.items()},
               "suspect": name_hits.most_common(200)},
              fp, ensure_ascii=False, indent=2)
print("\n已写出 资料库/facts_index.json")
