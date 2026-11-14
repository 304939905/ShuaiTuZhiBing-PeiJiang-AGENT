# -*- coding: utf-8 -*-
"""试点渲染驱动：只渲染 argv 指定的 video_title（不含 .json），避免触发全量重渲。
用法：<managed-python> render_pilot.py "视频名1" "视频名2" ...
渲染器：gen_refined_report.render(fp, '旧56项目', '旧56项目')
"""
import importlib.util, os, sys

BASE = r'D:/Desktop/shandou'
LIB = os.path.join(BASE, '资料库')
FJ = os.path.join(LIB, 'frame_json')

spec = importlib.util.spec_from_file_location("gr", os.path.join(LIB, 'gen_refined_report.py'))
gr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gr)

titles = sys.argv[1:]
if not titles:
    print('用法: render_pilot.py "视频名" ...')
    sys.exit(1)

for t in titles:
    fp = os.path.join(FJ, t + '.json')
    if not os.path.exists(fp):
        print('SKIP (no json):', t); continue
    try:
        r = gr.render(fp, '旧56项目', '旧56项目')
        print('OK |', r['title'][:40], '| 武将', r['n_hero'], '战法', r['n_skill'], '宝物', r['n_gear'], '|', r['out'])
    except Exception as e:
        print('FAIL', t, '->', repr(e))
print('PILOT DONE')
