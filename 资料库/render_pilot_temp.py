# -*- coding: utf-8 -*-
import os, shutil
import gen_refined_report_zhenrong as g

TMP = r'D:/tmp/zh_rerender'
os.makedirs(TMP, exist_ok=True)
g.OUT = TMP   # 临时输出，避开预览写锁

files = [
    r'D:/Desktop/shandou/资料库/zhenrong_frame_json/率土平民队伍之甘宁碰瓷队.json',
    r'D:/Desktop/shandou/资料库/zhenrong_frame_json/video_月卡配将不一定配的就好，但是免费..._top_0_3.json',
]
for f in files:
    try:
        out, row = g.render(f)
        print('[OK]', os.path.basename(out))
    except Exception as e:
        print('[ERR]', f, '->', repr(e))
