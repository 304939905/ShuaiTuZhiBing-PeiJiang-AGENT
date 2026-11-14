# -*- coding: utf-8 -*-
import sys, os, random, glob
LIB = r'D:/Desktop/shandou/资料库'
sys.path.insert(0, LIB)
import gen_refined_report_zhenrong as G

jsons = sorted(glob.glob(os.path.join(G.SRC, '*.json')))
print('总JSON数:', len(jsons))
random.seed()
chosen = random.sample(jsons, 2)
print('随机抽中2份:')
for c in chosen:
    print('  -', os.path.basename(c))
rows = []
for p in chosen:
    op, row = G.render(p)
    rows.append(row)
    print('已生成 ->', op)
print('DONE')
