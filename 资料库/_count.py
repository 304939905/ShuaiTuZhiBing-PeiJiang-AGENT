# -*- coding: utf-8 -*-
import os, glob
BASE = r'D:\Desktop\shandou\报告库'
NEW_BATCH = {'阵容新批'}  # 新一批，用户明确不动
OLD_DEF = {'旧56项目','开荒','海之呼唤','赛季'}  # 08-20 旧一批定义（87视频）
rows = []
tot_all = 0; tot_old = 0; tot_new = 0
for sub in sorted(os.listdir(BASE)):
    sp = os.path.join(BASE, sub)
    if not os.path.isdir(sp): continue
    for tier in ['精编','逐帧1秒版','完整版']:
        d = os.path.join(sp, tier)
        if not os.path.isdir(d): continue
        n = len(glob.glob(os.path.join(d,'*.docx')))
        if n == 0: continue
        tag = '新一批' if sub in NEW_BATCH else ('旧一批' if sub in OLD_DEF else '?')
        rows.append((sub, tier, n, tag))
        tot_all += n
        if tag == '旧一批': tot_old += n
        if tag == '新一批': tot_new += n
print(f"{'子项目':<10}{'层级':<12}{'份数':<6}{'归属'}")
for sub,tier,n,tag in rows:
    print(f"{sub:<10}{tier:<12}{n:<6}{tag}")
print('-'*40)
print(f"报告库总计: {tot_all}")
print(f"  其中 旧一批(87视频): {tot_old}")
print(f"  其中 新一批(阵容): {tot_new}")
# 视频数核对
print('\n视频数(旧一批定义): 北冥50 + 开荒6 + 海之呼唤27 + 赛季4 = 87')
print('报告数≠视频数: 每视频最多3份(精编/1秒版/完整版)')
