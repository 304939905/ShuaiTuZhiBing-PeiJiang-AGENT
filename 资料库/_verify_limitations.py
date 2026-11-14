import json, re

def load(p):
    return json.load(open(p, encoding='utf-8'))

def collect(d):
    out = set()
    if isinstance(d, dict):
        for k, v in d.items():
            if k in ('names', 'common', 'innate_from_hero', 'skills'):
                if isinstance(v, list):
                    for x in v:
                        if isinstance(x, str):
                            out.add(x)
                        elif isinstance(x, dict) and 'name' in x:
                            out.add(x['name'])
                elif isinstance(v, dict):
                    for kk, x in v.items():
                        if isinstance(x, str):
                            out.add(x)
                        elif isinstance(x, dict) and 'name' in x:
                            out.add(x['name'])
            elif isinstance(v, list):
                for x in v:
                    if isinstance(x, str):
                        out.add(x)
    return out

gear = collect(load('official_gear_names.json')) | collect(load('gear_id.json'))
skills = collect(load('official_jineng_names_ext.json')) | collect(load('official_skill_db.json')) | collect(load('official_jineng_names_full.json'))
heroes = collect(load('official_hero_names.json'))
print('真实库规模: 宝物', len(gear), '| 战法', len(skills), '| 武将', len(heroes))

P = r'D:\Desktop\shandou\资料库\zhenrong_frame_json\video_来人配将，免费粉丝配将第十三期 ..._top_0_3.json'
d = json.load(open(P, encoding='utf-8'))
lims = d.get('limitations', [])
print('局限条数:', len(lims))

neg_kw = ['未收录', 'NOT FOUND', '无此名', '查无', '均未收录', '未更新']
print('=== 逐条核验 查无类 主张（误判=实际存在却报查无） ===')
bad_all = []
for i, lim in enumerate(lims):
    if any(k in lim for k in neg_kw):
        cands = set(re.findall(r'[一-鿿]{2,6}', lim))
        bad = []
        for c in cands:
            if c in gear:
                bad.append(('宝物', c))
            elif c in skills:
                bad.append(('战法', c))
            elif c in heroes:
                bad.append(('武将', c))
        if bad:
            bad_all.append(i)
            print(f'[{i}] 误判为查无但实际存在: {bad}')
            print('     原文:', lim[:110])

print('=== 汇总: 误判条数', len(bad_all), '索引', bad_all)
