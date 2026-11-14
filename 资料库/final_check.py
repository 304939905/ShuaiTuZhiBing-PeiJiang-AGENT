# -*- coding: utf-8 -*-
"""最终交付校验：51 份 1 秒/帧报告与 56 个源视频的一一对应关系。"""
import json, os
from docx import Document

BASE = 'D:/Desktop/shandou'
REP = os.path.join(BASE, '学习汇报')
SUF = '_逐帧深度学习报告_1秒版.docx'
SEP = chr(92)

meta = json.load(open(os.path.join(BASE, '资料库/video_meta.json'), encoding='utf-8'))
root, kg = [], []
for v in meta['videos']:
    rp = v['rel_path'].replace(SEP, '/')
    stem = os.path.splitext(os.path.basename(rp))[0]
    (kg if rp.startswith('开荒/') else root).append(stem)

have = set()
for f in os.listdir(REP):
    if f.endswith(SUF):
        have.add(f[:-len(SUF)])

print('源视频：根目录 %d + 开荒 %d = %d' % (len(root), len(kg), len(root) + len(kg)))
print('报告数：%d' % len(have))
print()

miss = [s for s in root if s not in have]
print('根目录未覆盖：%d 个' % len(miss))
for s in miss:
    print('   MISS %s' % s)

extra = [s for s in have if s not in root and '开荒专题' not in s]
print('非源视频报告：%d 个' % len(extra))
for s in extra:
    print('   EXTRA %s' % s)

kgrep = [s for s in have if '开荒专题' in s]
print('开荒专题报告：%d 个 -> %s' % (len(kgrep), kgrep))
print()

# 内容体检
print('--- 内容体检（章节数/插图数/字数）---')
bad = 0
rows = []
for f in sorted(os.listdir(REP)):
    if not f.endswith(SUF):
        continue
    p = os.path.join(REP, f)
    try:
        d = Document(p)
        imgs = len(d.inline_shapes)
        h1 = sum(1 for x in d.paragraphs if x.style.name == 'Heading 1')
        chars = sum(len(x.text) for x in d.paragraphs)
        flag = ''
        if imgs < 10 or h1 < 5 or chars < 1500:
            flag = '  <<< 内容偏少'
            bad += 1
        rows.append((imgs, h1, chars, f[:44], flag))
    except Exception as e:
        print('  ERR %s : %s' % (f[:40], e))
        bad += 1

rows.sort()
for imgs, h1, chars, name, flag in rows[:6]:
    print('  最少 图%3d 章%2d 字%6d  %s%s' % (imgs, h1, chars, name, flag))
print('   ...')
for imgs, h1, chars, name, flag in rows[-3:]:
    print('  最多 图%3d 章%2d 字%6d  %s%s' % (imgs, h1, chars, name, flag))

print()
print('异常报告数：%d' % bad)
print('平均：图 %.0f 张 / 章 %.1f 个 / 字 %.0f' % (
    sum(r[0] for r in rows) / len(rows),
    sum(r[1] for r in rows) / len(rows),
    sum(r[2] for r in rows) / len(rows)))
print('总插图 %d 张，总字数 %d' % (sum(r[0] for r in rows), sum(r[2] for r in rows)))
