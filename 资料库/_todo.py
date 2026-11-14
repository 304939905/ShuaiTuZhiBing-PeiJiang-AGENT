import json, os

meta = json.load(open('video_meta.json', encoding='utf-8'))
vids = meta['videos']

done_json = set()
for f in os.listdir('frame_json'):
    if f.endswith('.json'):
        done_json.add(f[:-5])

rep_dir = 'D:/Desktop/shandou/学习汇报'
SUF = '_逐帧深度学习报告_1秒版.docx'
done_doc = set()
for f in os.listdir(rep_dir):
    if f.endswith(SUF):
        done_doc.add(f[:-len(SUF)])

SEP = chr(92)  # backslash
root, kg = [], []
for v in vids:
    rp = v['rel_path'].replace(SEP, '/')
    stem = os.path.splitext(os.path.basename(rp))[0]
    if rp.startswith('开荒/'):
        kg.append((stem, v['duration_s']))
    else:
        root.append((stem, v['duration_s']))

print('总视频 %d  根目录 %d  开荒 %d' % (len(vids), len(root), len(kg)))
print('已有JSON %d  已有1秒版docx %d' % (len(done_json), len(done_doc)))
print()
todo = [(s, d) for s, d in root if s not in done_json and s not in done_doc]
print('=== 根目录待办 %d 个 ===' % len(todo))
for i, (s, d) in enumerate(todo, 1):
    print('%2d. [%6.1fs] %s' % (i, d, s))
print()
print('=== 开荒待办 %d 个 ===' % len(kg))
for i, (s, d) in enumerate(kg, 1):
    print('%2d. [%6.1fs] %s' % (i, d, s))
print()
tot = sum(d for _, d in todo) + sum(d for _, d in kg)
print('待办总时长 %.0f 秒 = %.1f 分钟' % (tot, tot / 60))
