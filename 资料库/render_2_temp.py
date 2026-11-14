# -*- coding: utf-8 -*-
import sys, os, shutil, glob
LIB = r'D:/Desktop/shandou/资料库'
sys.path.insert(0, LIB)
import gen_refined_report_zhenrong as G
TMP = r'D:/tmp/zh_rerender'
G.OUT = TMP
os.makedirs(TMP, exist_ok=True)
targets = [
  r'D:/Desktop/shandou/资料库/zhenrong_frame_json/video_月卡配将不一定配的就好，但是免费..._top_0_3.json',
  r'D:/Desktop/shandou/资料库/zhenrong_frame_json/率土平民队伍之甘宁碰瓷队.json',
]
CANON = r'D:/Desktop/shandou/报告库/阵容新批/精编'
for p in targets:
    op, row = G.render(p)
    print('RENDER_OK ->', op)
    base = os.path.basename(op)
    dst = os.path.join(CANON, base)
    try:
        shutil.copy2(op, dst)
        print('COPY_OK ->', dst)
    except PermissionError:
        print('LOCKED ->', dst, '(预览占用，关闭预览后可由本文件覆盖)')
