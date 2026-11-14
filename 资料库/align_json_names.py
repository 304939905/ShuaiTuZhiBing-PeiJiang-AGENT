# -*- coding: utf-8 -*-
"""
把 frame_json/*.json 的文件名与内部 video_title / frames_dir 字段
对齐到 video_meta.json 里的真实源视频文件名。

常见问题：子智能体把全角/半角标点写错（! ↔ ！、? ↔ ？、, ↔ ，），
导致 JSON 文件名与源视频名不一致，渲染出的 Word 文件名也跟着错。

用法：python align_json_names.py            # 只报告
      python align_json_names.py --apply    # 实际改名并改字段
"""
import json, os, sys, unicodedata

APPLY = '--apply' in sys.argv
BASE = os.path.dirname(os.path.abspath(__file__))
JD = os.path.join(BASE, 'frame_json')
SEP = chr(92)

meta = json.load(open(os.path.join(BASE, 'video_meta.json'), encoding='utf-8'))

# 真实名 -> 归一化key
def norm(s):
    # 全角标点统一成半角，去掉所有空格，用于模糊匹配
    tbl = {'！': '!', '？': '?', '，': ',', '：': ':', '；': ';',
           '（': '(', '）': ')', '　': ' ', '。': '.'}
    out = []
    for ch in s:
        out.append(tbl.get(ch, ch))
    return ''.join(out).replace(' ', '').lower()

real = {}   # normkey -> (真实stem, 相对目录)
for v in meta['videos']:
    rp = v['rel_path'].replace(SEP, '/')
    stem = os.path.splitext(os.path.basename(rp))[0]
    sub = os.path.dirname(rp)
    real[norm(stem)] = (stem, sub)

renamed = fixed = miss = ok = 0
for f in sorted(os.listdir(JD)):
    if not f.endswith('.json'):
        continue
    cur = f[:-5]
    k = norm(cur)
    if k not in real:
        print('MISS 无法匹配到源视频: %s' % cur)
        miss += 1
        continue
    rstem, sub = real[k]
    frames_dir = (sub + '/' + rstem) if sub else rstem

    # 1) 文件名
    if cur != rstem:
        src = os.path.join(JD, f)
        dst = os.path.join(JD, rstem + '.json')
        print('RENAME %s' % cur)
        print('    -> %s' % rstem)
        if APPLY:
            os.replace(src, dst)
        f = rstem + '.json'
        renamed += 1

    # 2) 内部字段
    p = os.path.join(JD, f)
    try:
        d = json.load(open(p, encoding='utf-8'))
    except Exception as e:
        print('SKIP 解析失败 %s : %s' % (f, e))
        continue
    ch = []
    if d.get('video_title') != rstem:
        ch.append('video_title')
        d['video_title'] = rstem
    if d.get('frames_dir') not in (frames_dir, rstem):
        ch.append('frames_dir=%s' % d.get('frames_dir'))
        d['frames_dir'] = frames_dir
    if ch:
        print('FIELD %-40s %s' % (rstem[:40], ','.join(ch)))
        if APPLY:
            json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        fixed += 1
    else:
        ok += 1

print()
print('%s  改名=%d  字段修正=%d  无需处理=%d  未匹配=%d'
      % ('已应用' if APPLY else '仅预览(加 --apply 生效)', renamed, fixed, ok, miss))
