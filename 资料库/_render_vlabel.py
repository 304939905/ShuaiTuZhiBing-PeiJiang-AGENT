# -*- coding: utf-8 -*-
"""渲染来来来兄弟们+配将点评双版报告（vlabel 定案后），并按 title 替换索引行。"""
import io, sys, json, importlib.util
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

spec = importlib.util.spec_from_file_location('g', 'gen_refined_report_zhenrong.py')
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

TARGETS = [
    'zhenrong_frame_json/video_来来来兄弟们，继续配将，免费粉丝..._top_0_3.json',
    'zhenrong_frame_json/配将点评.json',
]
rows = json.load(open('zhenrong_index_rows.json', encoding='utf-8'))

for p in TARGETS:
    op, row = G.render(p)
    print('精编:', op.split('/')[-1][:60])
    # 索引行替换
    hit = False
    for i, r in enumerate(rows):
        if r['title'] == row['title']:
            rows[i] = row
            hit = True
    if not hit:
        rows.append(row)
        print('  (索引行新增)')
    # 1秒版
    import subprocess
    r = subprocess.run([sys.executable, 'gen_frame_report_1s_zhenrong.py', p],
                       capture_output=True, text=True, encoding='utf-8')
    print('1秒版 exit:', r.returncode, r.stdout.strip()[-80:] if r.stdout else r.stderr[-200:])

json.dump(rows, open('zhenrong_index_rows.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('索引行总数:', len(rows))

# 索引标签复核
for r in rows:
    if any(k in r['title'] for k in ['来来来，继续配将', '配将点评']):
        print('==', r['title'][:36])
        print('  ', [x for x in r['hero_labels'] if any(n in x for n in ['刘备', '王异', '荀彧', '卫瓘', '华雄'])])
