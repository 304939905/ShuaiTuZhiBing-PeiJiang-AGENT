import json, re, glob, os

BASE = r'D:\Desktop\shandou\资料库'
def load(p): return json.load(open(p, encoding='utf-8'))

m = load(os.path.join(BASE, 'official_merged_whitelist.json'))
skills = set(m['skills']); gears = set(m['gears']); heroes = set(m['heroes'])

neg_kw = ['未收录', 'NOT FOUND', '无此名', '查无', '均未收录', '未更新', '库无']
files = sorted(glob.glob(os.path.join(BASE, 'zhenrong_frame_json', '*.json')))
print(f'扫描 {len(files)} 份，基准=合并白名单(战法{len(skills)}/宝物{len(gears)}/武将{len(heroes)})')
print('判定规则：仅抓「未收录/NOT FOUND/无此名」附近「名」括起来的真正负面主张\n')

total = 0
report = []
for f in files:
    d = load(f)
    name = os.path.basename(f)[:36]
    bad = []
    for field, key in (('limitations', 'lim'), ('sources', 'src')):
        for i, s in enumerate(d.get(field, [])):
            for kw in neg_kw:
                idx = s.find(kw)
                if idx < 0:
                    continue
                # 取该 neg 词前 80 字内所有「X」括起来的名
                window = s[max(0, idx-80):idx]
                for c in re.findall(r'「([一-鿿]{2,6})」', window):
                    if c in gears: bad.append((f'{key}[{i}]', c, '宝物'))
                    elif c in skills: bad.append((f'{key}[{i}]', c, '战法'))
                    elif c in heroes: bad.append((f'{key}[{i}]', c, '武将'))
                # 也抓 neg 词后紧跟「X」/「Y」清单（sources[3] 风格）
                after = s[idx:idx+120]
                for c in re.findall(r'「([一-鿿]{2,6})」', after):
                    if c in gears: bad.append((f'{key}[{i}]', c, '宝物'))
                    elif c in skills: bad.append((f'{key}[{i}]', c, '战法'))
                    elif c in heroes: bad.append((f'{key}[{i}]', c, '武将'))
    if bad:
        total += len(bad)
        report.append((name, bad))

print(f'含误判「查无」的报告: {len(report)} 份，误判条目合计: {total}\n')
for name, bad in report:
    print(f'▸ {name}  ({len(bad)} 条)')
    for pos, c, t in bad:
        print(f'    {pos}  {t}「{c}」实际存在于合并白名单')
    print()
