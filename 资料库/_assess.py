# -*- coding: utf-8 -*-
"""以攻其篇精编为标杆，扫描旧一批全部报告：结构维度覆盖、杂质残留、星级正确性。"""
import os, re, json, glob
from docx import Document

BASE = r'D:\Desktop\shandou'
REPO = os.path.join(BASE, '报告库')

# ---------- 加载官方星级（hero.json 唯一权威） ----------
hero_all = json.load(open(os.path.join(BASE,'资料库','hero.json'), encoding='utf-8'))
hero_star = {}
for h in hero_all:
    nm = (h.get('name') or '').strip()
    q = h.get('quality')
    if isinstance(q, int) and nm:
        hero_star[nm] = max(hero_star.get(nm,0), q)

# ---------- 标杆文件（3篇精修，用户给定/确认） ----------
BENCHMARK = {
    '攻其': '全率土最细最全攻略合集攻其篇—粉丝投稿解析 来了!看看粉丝们的奇思妙想吧_精编学习报告.docx',
    '神赏': '全率土最细最全攻略合集—神赏篇 来了! 评论投稿，下期解析哦!_精编学习报告.docx',
    # 009焚决：待用户确认具体哪份，先不硬编码
}

# ---------- 杂质正则（保守，避免误伤「粉丝投稿解析/投稿一」等合法内容） ----------
IMPURE = [
    (r'粉丝「[^」]{1,20}」', '粉丝具名(括号)'),
    (r'粉丝\s*ID', '粉丝ID'),
    (r'头像为', '头像为'),
    (r'（头像', '（头像'),
    (r'头像样式', '头像样式'),
    (r'点个关注', '点个关注'),
    (r'关注我贴纸', '关注我贴纸'),
    (r'下期干货不迷路', '下期干货不迷路'),
    (r'UP主「', 'UP主具名'),
    (r'UP主头像', 'UP主头像'),
    (r'手机拍摄屏幕', '手机拍屏'),
    (r'交叉刀剑', '交叉刀剑'),
    (r'纯过渡动画', '纯过渡动画'),
    (r'片尾画面', '片尾画面'),
    (r'片头画面', '片头画面'),
    (r'哆啦A梦', '哆啦A梦装饰'),
]
# 星级问题：hero（阵营-兵种-N星），N<=4 但官方为5星；或 '4-SR' 痕迹
STAR_RE = re.compile(r'([一-鿿]{2,5})（([一-鿿]+)-([一-鿿]+)-(\d)星）')

def scan_doc(path):
    doc = Document(path)
    paras = [p.text for p in doc.paragraphs]
    headings = [p.text.strip() for p in doc.paragraphs if p.style.name.startswith('Heading')]
    full = '\n'.join(paras)
    # 表格文本
    tbl_texts = []
    for t in doc.tables:
        for row in t.rows:
            tbl_texts.append(' | '.join(c.text.strip() for c in row.cells))
    table_full = '\n'.join(tbl_texts)
    alltext = full + '\n' + table_full

    rec = {}
    rec['chars'] = len(full)
    rec['paras'] = len([p for p in paras if p.strip()])
    rec['headings'] = headings
    rec['tables'] = len(doc.tables)

    # 结构维度
    rec['has_index'] = ('报告索引' in full)
    rec['has_hero_version'] = ('核心武将（版本）' in full or '核心武将(版本)' in full)
    rec['has_conclusion'] = any(('结论' in h) for h in headings)
    rec['has_ai'] = ('主动推断' in full)
    rec['has_table'] = (len(doc.tables) > 0)
    rec['has_mechanism'] = bool(re.search(r'体系|机制|原理|讲解|详解', full))
    rec['has_action'] = bool(re.search(r'可执行|建议|怎么(配|用)|如何(配|玩)', full))

    # 杂质
    hits = []
    for pat, lab in IMPURE:
        if re.search(pat, alltext):
            hits.append(lab)
    rec['impurity'] = hits

    # 星级
    star_issues = []
    if '4-SR' in alltext:
        star_issues.append('含4-SR痕迹(hero_extra稀有度误当星级)')
    for m in STAR_RE.finditer(alltext):
        nm, c, b, n = m.group(1), m.group(2), m.group(3), int(m.group(4))
        real = hero_star.get(nm)
        if real is not None and real >= 5 and n <= 4:
            star_issues.append(f'{nm}标{n}星但官方{real}星')
    rec['star_issue'] = star_issues
    return rec

# ---------- 收集文件 ----------
targets = []
for sub in ['旧56项目','开荒','海之呼唤','赛季','阵容新批']:
    for tier in ['精编','逐帧1秒版','完整版']:
        d = os.path.join(REPO, sub, tier)
        if os.path.isdir(d):
            for f in sorted(glob.glob(os.path.join(d,'*.docx'))):
                targets.append((sub, tier, f))

records = []
for sub, tier, f in targets:
    try:
        r = scan_doc(f)
    except Exception as e:
        r = {'error': str(e)}
    base = os.path.basename(f)
    is_bench = any(base == v for v in BENCHMARK.values())
    r['sub'] = sub; r['tier'] = tier; r['file'] = base; r['benchmark'] = is_bench
    records.append(r)

# ---------- 聚合 ----------
def agg(group_pred):
    items = [r for r in records if group_pred(r)]
    n = len(items)
    out = {'n': n}
    for dim in ['has_index','has_hero_version','has_conclusion','has_ai','has_table','has_mechanism','has_action']:
        out[dim] = sum(1 for r in items if r.get(dim))
    out['impure'] = sum(1 for r in items if r.get('impurity'))
    out['star_bad'] = sum(1 for r in items if r.get('star_issue'))
    return out

groups = {
    '精编-全部': lambda r: r['tier']=='精编',
    '精编-批量(非标杆)': lambda r: r['tier']=='精编' and not r['benchmark'],
    '1秒版-全部': lambda r: r['tier']=='逐帧1秒版',
    '旧56项目精编': lambda r: r['tier']=='精编' and r['sub']=='旧56项目',
    '旧56项目1秒版': lambda r: r['tier']=='逐帧1秒版' and r['sub']=='旧56项目',
}
aggs = {k: agg(p) for k,p in groups.items()}

# 杂质清单
impure_files = [(r['sub'],r['tier'],r['file'],r['impurity']) for r in records if r.get('impurity')]
star_files = [(r['sub'],r['tier'],r['file'],r['star_issue']) for r in records if r.get('star_issue')]

summary = {
    'total_files': len(records),
    'benchmark_files': [r['file'] for r in records if r['benchmark']],
    'aggregates': aggs,
    'impure_files': impure_files,
    'star_files': star_files,
}
with open(os.path.join(BASE,'资料库','_assess.json'),'w',encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=1)

# ---------- 写 markdown ----------
lines = []
lines.append('# 旧一批报告 vs 攻其篇精编标杆 · 评估报告')
lines.append('')
lines.append('> 标杆：攻其篇精编（用户给定副本）。评估维度取自该标杆 + 通用精编渲染器模板。')
lines.append('> 扫描时间：2026-08-20。范围：报告库下全部 精编/逐帧1秒版/完整版。')
lines.append('')
lines.append('## 1. 标杆质量维度（攻其篇精编具备）')
lines.append('- 报告索引块（关键词 + 核心武将版本标签 + 生成日期 + 路径）')
lines.append('- 一、视频核心结论（要点式）')
lines.append('- 二、体系核心讲解（机制深讲，非逐帧罗列）')
lines.append('- 三、阵容/投稿逐一点评')
lines.append('- 四、平民可执行建议')
lines.append('- 五、AI 主动推断（非视频原话，物理隔离，带证据）')
lines.append('- 对比表（多阵容/多方案时）')
lines.append('- 无杂质（无粉丝ID/头像/片头片尾过渡/纯战报堆叠）')
lines.append('')
lines.append('## 2. 总览（维度覆盖份数 / 该组总份数）')
lines.append('')
lines.append('| 分组 | 份数 | 索引块 | 武将版本标签 | 核心结论 | AI推断 | 有表 | 体系讲解 | 可执行建议 | 含杂质 | 星级问题 |')
lines.append('|---|---|---|---|---|---|---|---|---|---|---|')
for k,a in aggs.items():
    n=a['n']
    if n==0: continue
    lines.append('| {} | {} | {}/{} | {}/{} | {}/{} | {}/{} | {}/{} | {}/{} | {}/{} | {}/{} | {}/{} |'.format(
        k, n,
        a['has_index'],n, a['has_hero_version'],n, a['has_conclusion'],n,
        a['has_ai'],n, a['has_table'],n, a['has_mechanism'],n, a['has_action'],n,
        a['impure'],n, a['star_bad'],n))
lines.append('')
lines.append('## 3. 杂质残留清单（文件 → 命中模式）')
if impure_files:
    for sub,tier,fn,imps in impure_files:
        lines.append('- [{}] {} `{}` → {}'.format(sub, tier, fn, '、'.join(imps)))
else:
    lines.append('- 无（全部通过）')
lines.append('')
lines.append('## 4. 星级问题清单（标错星或含4-SR痕迹）')
if star_files:
    for sub,tier,fn,ss in star_files:
        lines.append('- [{}] {} `{}` → {}'.format(sub, tier, fn, '；'.join(ss)))
else:
    lines.append('- 无')
lines.append('')
lines.append('## 5. 标杆文件识别')
lines.append('- 攻其精修：`{}`'.format(BENCHMARK['攻其']))
lines.append('- 神赏精修：`{}`'.format(BENCHMARK['神赏']))
lines.append('- 009焚决精修：待用户确认对应哪份焚决报告（候选：从零开始宝物养成焚决 / 平民种地焚决 / 玉符分配焚决）')
lines.append('')
lines.append('## 6. 结论与建议（待合成）')
lines.append('见正文。')

with open(os.path.join(BASE,'资料库','ASSESS_vs_benchmark.md'),'w',encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('SCAN DONE. files=', len(records))
print('impure=', len(impure_files), 'star_bad=', len(star_files))
for k,a in aggs.items():
    print(k, a)
