# -*- coding: utf-8 -*-
"""
修复 frame_json / frame_json_kaihuang 里 timeline 帧引用的两类问题：
  1) frames[i] 缺少 file 字段
  2) file 字段指向不存在的路径（例如子智能体写成了自己的临时目录 _tmp_frames/xxx.jpg）

修复方式：以 ts（MM:SS）为准换算成总秒数 n，目标文件名为 frame_%04d_MM-SS.jpg。
若该文件不存在，则在 n±3 秒范围内就近找一个存在的帧顶上（并记录）。

用法：python fix_frame_refs.py           # 预览
      python fix_frame_refs.py --apply   # 落盘
"""
import json, os, re, sys

APPLY = '--apply' in sys.argv
BASE = os.path.dirname(os.path.abspath(__file__))
FRAMES_ROOT = 'D:/Desktop/shandou/抖音_frames_dense_1s'
DIRS = ['frame_json', 'frame_json_kaihuang']


def name_of(n):
    return 'frame_%04d_%02d-%02d.jpg' % (n, n // 60, n % 60)


def ts_to_sec(ts):
    m = re.match(r'^(\d+):(\d+)$', str(ts).strip())
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


tot_fix = tot_near = tot_fail = 0
for d in DIRS:
    dp = os.path.join(BASE, d)
    if not os.path.isdir(dp):
        continue
    for f in sorted(os.listdir(dp)):
        if not f.endswith('.json'):
            continue
        p = os.path.join(dp, f)
        try:
            data = json.load(open(p, encoding='utf-8'))
        except Exception as e:
            print('SKIP 解析失败 %s: %s' % (f, e))
            continue
        fdir = data.get('frames_dir') or f[:-5]
        base = os.path.join(FRAMES_ROOT, fdir)
        if not os.path.isdir(base):
            print('SKIP 帧目录不存在 %s -> %s' % (f[:30], fdir))
            continue
        exist = set(x for x in os.listdir(base) if x.endswith('.jpg'))

        fix = near = fail = 0
        for seg in data.get('timeline', []):
            for fr in seg.get('frames', []):
                cur = fr.get('file')
                if cur and cur in exist:
                    continue
                sec = ts_to_sec(fr.get('ts'))
                if sec is None:
                    fail += 1
                    continue
                want = name_of(sec)
                if want in exist:
                    fr['file'] = want
                    fix += 1
                    continue
                hit = None
                for off in (1, -1, 2, -2, 3, -3):
                    cand = name_of(sec + off)
                    if sec + off >= 0 and cand in exist:
                        hit = cand
                        break
                if hit:
                    fr['file'] = hit
                    near += 1
                else:
                    fr['file'] = None
                    fail += 1
        # 清掉找不到的帧，避免渲染报错
        if fail:
            for seg in data.get('timeline', []):
                seg['frames'] = [x for x in seg.get('frames', []) if x.get('file')]

        if fix or near or fail:
            print('%-46s 精确=%d 就近=%d 丢弃=%d' % (f[:46], fix, near, fail))
            if APPLY:
                json.dump(data, open(p, 'w', encoding='utf-8'),
                          ensure_ascii=False, indent=2)
        tot_fix += fix
        tot_near += near
        tot_fail += fail

print()
print('%s  精确修复=%d  就近替代=%d  丢弃=%d'
      % ('已应用' if APPLY else '仅预览(加 --apply 生效)', tot_fix, tot_near, tot_fail))
