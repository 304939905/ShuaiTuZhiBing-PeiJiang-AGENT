"""Save hand-authored cards after each full reading batch."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '资料库/策略知识库/精编全量学习_20261011'


def read(p):
    return json.loads(p.read_text('utf-8-sig'))


def save(group, specs, lessons=(), questions=()):
    manifest = read(OUT / '阅读清单.json')
    meta = {r['no']: r for r in manifest['records']}
    db = read(ROOT / '资料库/official_skill_db.json')
    target = OUT / f'{group}.json'
    obj = read(target) if target.exists() else dict(group=group, report_ids=[],
        scope='正文与表格逐篇全文阅读；保存库交叉核对，未重新验证线上参数或退役源视频。',
        records=[], cross_report_lessons=[], open_questions=[])
    cards = {r['no']: r for r in obj['records']}
    evpath = OUT / '补充本地核对证据.json'
    ev = read(evpath) if evpath.exists() else {'verified_date': '2026-10-12', 'scope': 'Saved local files only',
        'source_hashes': {}, 'saved_records': {}}
    for rel in ['资料库/official_skill_db.json','资料库/hero_extra.json','资料库/hero.json',
                '资料库/skill_extra.json','资料库/gear_forge_pool.json','资料库/threshold_db.json']:
        path = ROOT / rel
        if path.is_file():
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            if rel in ev['source_hashes'] and sha != ev['source_hashes'][rel]:
                raise ValueError(f'Source changed: {rel}')
            ev['source_hashes'][rel] = sha
    for no, s in specs.items():
        m = meta[no]
        assert m['group'] == group
        assert hashlib.sha256((ROOT / m['rel']).read_bytes()).hexdigest() == m['source_sha256']
        # check = (claim, [(db_section, name)], result, inspected comparison, impact, paragraph IDs)
        claim, names, result, evidence, impact, ps = s['check']
        refs = []
        for section, name in names:
            assert name in db[section], f'Missing local lookup: {section}/{name}'
            key = f'{section}/{name}'
            ev['saved_records'][key] = db[section][name]
            refs.append(key)
        cards[no] = dict(no=no, title=m['title'], rel=m['rel'], source_sha256=m['source_sha256'],
            reading_status='full_text_read', paragraph_count=m['paragraph_count'], tags=s['tags'],
            transferable_rules=[dict(zip(['condition','decision','reason','failure_mode','evidence_paragraphs'], r))
                                for r in s['rules']],
            resource_dependencies=s['resources'], version_and_season_limits=s['limits'],
            non_transferable_claims=s['excluded'], local_checks=[dict(claim=claim,
                source='资料库/official_skill_db.json；补充本地核对证据.json:'+','.join(refs),
                result=result, evidence=evidence, impact=impact, evidence_paragraphs=ps)],
            application_questions=s['questions'], related_report_ids=s['related'])
    obj['records'] = [cards[n] for n in sorted(cards)]
    obj['report_ids'] = sorted(cards)
    if lessons: obj['cross_report_lessons'] = list(lessons)
    if questions: obj['open_questions'] = list(questions)
    target.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n','utf-8')
    evpath.write_text(json.dumps(ev,ensure_ascii=False,indent=2)+'\n','utf-8')
    lines = [f'# {group[3:]}逐篇学习', '', obj['scope'], '',
             'P为DOCX全部段落顺序（包含表格），不是页码。数值与效果均仅核对本地保存版本。', '']
    for r in obj['records']:
        lines += [f"## {r['no']} {r['title']}", '', f"[全文](阅读材料/{r['no']}.txt)", '']
        for x in r['transferable_rules']:
            anchors='、'.join(f'P{p:03}' for p in x['evidence_paragraphs'])
            lines += [f"- 条件：{x['condition']}。判断：{x['decision']}。理由：{x['reason']}。失效风险：{x['failure_mode']}。证据：{anchors}。"]
        c=r['local_checks'][0]
        lines += ['',f"本地核对（{c['result']}）：{c['evidence']} {c['impact']}",
                  '资源：'+'；'.join(r['resource_dependencies'])+'。',
                  '边界：'+'；'.join(r['version_and_season_limits'])+'。',
                  '不直接迁移：'+'；'.join(r['non_transferable_claims'])+'。',
                  '先问：'+'；'.join(r['application_questions']),
                  '关联报告：'+'、'.join(f'[{n}](阅读材料/{n}.txt)' for n in r['related_report_ids']), '']
    if obj['cross_report_lessons']:
        lines += ['## 跨报告认识', '']+[f'- {s}' for s in obj['cross_report_lessons']]+['']
    if obj['open_questions']:
        lines += ['## 待复核', '']+[f'- {s}' for s in obj['open_questions']]+['']
    (OUT/f'{group}.md').write_text('\n'.join(lines),'utf-8')
    print(group, 'saved', len(cards))
