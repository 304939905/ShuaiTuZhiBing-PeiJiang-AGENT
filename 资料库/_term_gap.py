# -*- coding: utf-8 -*-
import re
from collections import Counter, defaultdict

TERM_FILE = r"D:\Desktop\shandou\资料库\名词概念.md"
REVIEW = r"D:\Desktop\shandou\资料库\_review_all.md"

term_txt = open(TERM_FILE, encoding="utf-8").read()
review = open(REVIEW, encoding="utf-8").read()

# existing term names
term_names = set(re.findall(r"^#{2,3}\s*\d*\.*\s*(.+)$", term_txt, flags=re.M))
# also gather all tokens inside term library to treat as "known"
known_tokens = set()
for line in term_txt.splitlines():
    known_tokens.update(re.findall(r"[\u4e00-\u9fff]{2,4}", line))

# split review into per-report blocks to compute document frequency
blocks = re.split(r"^## \d+\. ", review, flags=re.M)[1:]
# each block may contain multiple reports separated by '## NN.' already split; but our split keeps one report per block
doc_freq = defaultdict(int)
all_tok = Counter()
for blk in blocks:
    toks = set()
    for L in (2,3,4):
        for m in re.findall(r"[\u4e00-\u9fff]{%d}"%L, blk):
            toks.add(m)
    for t in toks:
        doc_freq[t]+=1
        all_tok[t]+=1

# candidate = appears in >=4 distinct reports, length 3 or 4, not a known token, not pure stopword-ish
# we will print for manual review
cands = [(t, doc_freq[t], all_tok[t]) for t in doc_freq if 3<=len(t)<=4 and doc_freq[t]>=4 and t not in known_tokens]
cands.sort(key=lambda x:(-x[1], -x[2]))

# also exclude if token is substring of any known term name (so we don't dup)
def in_known(t):
    for kn in term_names:
        if t in kn:
            return True
    return False
cands = [c for c in cands if not in_known(c[0])]

print("=== CANDIDATE NEW TERMS (doc_freq>=4, len 3-4, not in term库) ===")
print("total candidates:", len(cands))
for t, df, tf in cands:
    print(f"{t}\tdf={df}\ttf={tf}")
