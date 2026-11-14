# -*- coding: utf-8 -*-
"""2026-08-22 索引关键词核查修复：重渲 五队+第十一期 双版本（version_label 优先 + STYLE_WORDS 补垒石/开荒）"""
import importlib.util, io, sys, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(r'D:/Desktop/shandou/资料库')

spec = importlib.util.spec_from_file_location('gr', 'gen_refined_report_zhenrong.py')
gr = importlib.util.module_from_spec(spec); spec.loader.exec_module(gr)

JOBS = [
    'zhenrong_frame_json/video_五队并三队，三队并两队，样样通样..._top_0_3.json',
    'zhenrong_frame_json/video_免费粉丝配将第十一期，继续配将。..._top_0_2.json',
]
for p in JOBS:
    op, row = gr.render(p)
    print('精编OK:', os.path.basename(op)[:50])

import subprocess
for p in JOBS:
    r = subprocess.run([sys.executable, '-X', 'utf8', 'gen_frame_report_1s_zhenrong.py', p],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('1秒版 rc=', r.returncode, (r.stdout or r.stderr or '').strip()[-120:])

# ---- 终验 ----
from docx import Document
CHECKS = {
    '五队精编': (r'D:/Desktop/shandou/报告库/阵容新批/精编/五队并三队，三队并两队，样样通样...（抖音标题被文件名截断）_精编学习报告.docx',
        {'must': ['姜维（蜀-弓/步-5星）'], 'ban': ['姜维（蜀-步-5星）']}),
    '五队1秒': (r'D:/Desktop/shandou/报告库/阵容新批/逐帧1秒版/五队并三队，三队并两队，样样通样...（抖音标题被文件名截断）_逐帧深度学习报告_1秒版.docx',
        {'must': ['姜维（蜀-弓/步-5星）'], 'ban': ['姜维（蜀-步-5星）']}),
    '十一精编': (r'D:/Desktop/shandou/报告库/阵容新批/精编/video_免费粉丝配将第十一期，继续配将。..._top_0_2_精编学习报告.docx',
        {'must': ['垒石'], 'ban': []}),
    '十一1秒': (r'D:/Desktop/shandou/报告库/阵容新批/逐帧1秒版/video_免费粉丝配将第十一期，继续配将。..._top_0_2_逐帧深度学习报告_1秒版.docx',
        {'must': [], 'ban': []}),
}
for tag, (p, ck) in CHECKS.items():
    d = Document(p)
    txt = '\n'.join(x.text for x in d.paragraphs)
    for t in d.tables:
        for r_ in t.rows:
            for c in r_.cells: txt += '\n' + c.text
    kws = [l for l in txt.split('\n') if l.startswith('关键词：')]
    print('==', tag, '字符:', len(txt), '图:', len(d.inline_shapes), '|', kws[0][:60] if kws else '无关键词行')
    for m in ck['must']:
        print('   must', m, txt.count(m))
    for b in ck['ban']:
        n = txt.count(b)
        print('   ban ', b, n, '⚠' if n else 'OK')
