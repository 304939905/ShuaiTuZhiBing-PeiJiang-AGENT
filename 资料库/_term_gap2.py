# -*- coding: utf-8 -*-
import re
from collections import defaultdict

TERM_FILE = r"D:\Desktop\shandou\资料库\名词概念.md"
REVIEW = r"D:\Desktop\shandou\资料库\_review_all.md"

term_txt = open(TERM_FILE, encoding="utf-8").read()
review = open(REVIEW, encoding="utf-8").read()

# known term names (normalize: strip numbering, spaces)
known = set()
for line in term_txt.splitlines():
    m = re.match(r"^#{2,3}\s*\d*\.*\s*(.+)$", line)
    if m:
        nm = m.group(1)
        # split on / and ，
        for part in re.split(r"[/，、]", nm):
            part = part.strip().strip("（）()")
            if part:
                known.add(part)
# also add all multi-char tokens from term library text
for t in re.findall(r"[\u4e00-\u9fff]{2,6}", term_txt):
    known.add(t)

# extract bracketed terms from review
brackets = re.findall(r"[「【『]([\u4e00-\u9fffA-Za-z0-9]+)[」】』]", review)
# also patterns: 战法「X」 体系「X」 宝物「X」 武将「X」 词条「X」 自带战法X
pats = re.findall(r"(?:战法|体系|宝物|武将|词条|自带|拆解为?|拆解战法|概念|机制|系统|队伍|黑话|流派|打法)[「『]?[\s]*([\u4e00-\u9fffA-Za-z0-9]{2,6})[」』]?", review)

from collections import Counter
cnt = Counter(brackets)
cnt2 = Counter(pats)

# candidate = bracketed term appearing >=2 times, not in known
def is_known(t):
    if t in known:
        return True
    # substring of known
    for k in known:
        if t in k or k in t:
            return True
    return False

cand = [(t,c) for t,c in cnt.items() if c>=2 and not is_known(t) and len(t)>=2]
cand.sort(key=lambda x:-x[1])
print("=== bracketed terms NOT in term库 (count>=2) ===")
print("count:", len(cand))
for t,c in cand:
    print(f"{t}\t{c}")
print()
cand2 = [(t,c) for t,c in cnt2.items() if c>=2 and not is_known(t) and len(t)>=2]
cand2.sort(key=lambda x:-x[1])
print("=== pattern-extracted terms NOT in term库 (count>=2) ===")
print("count:", len(cand2))
for t,c in cand2:
    print(f"{t}\t{c}")
