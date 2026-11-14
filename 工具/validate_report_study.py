"""Validate complete, traceable study coverage; do not change source assets."""
from __future__ import annotations

import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

from prepare_report_study import paragraph_text, NS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '资料库/策略知识库/精编全量学习_20261011'
RESULTS = {'supported_locally', 'conditional', 'conflict', 'missing', 'not_checked'}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    manifest = read(OUT / '阅读清单.json')
    index_rows = read(ROOT / '资料库/reports_index_rows.json')
    indexed = {str(r['no']).zfill(3): r for r in index_rows}
    source_records = {r['no']: r for r in manifest['records']}
    require(len(indexed) == len(index_rows) == len(source_records) == len(manifest['records']) == manifest['source_count'],
            'Duplicate or missing source/index IDs')
    require(set(indexed) == set(source_records), 'Active index changed after study preparation')
    all_records, summaries, group_counts, reading_hashes = [], {}, {}, {}
    paragraphs = {}
    for no, m in source_records.items():
        path = (ROOT / m['rel']).resolve()
        require(path.is_relative_to(ROOT.resolve()), f'{no}: source outside workspace')
        require(indexed[no]['rel'] == m['rel'], f'{no}: source path changed')
        require(sha(path) == indexed[no]['content_sha256'] == m['source_sha256'],
                f'{no}: DOCX source hash mismatch')
        with zipfile.ZipFile(path) as archive:
            require(archive.testzip() is None, f'{no}: invalid DOCX archive')
            xml = ET.fromstring(archive.read('word/document.xml'))
            ps = [paragraph_text(p) for p in xml.findall('.//' + NS + 'p')]
            media = [n for n in archive.namelist() if n.startswith('word/media/')]
            sides = [n for n in archive.namelist()
                     if n.startswith(('word/footnote', 'word/endnote', 'word/header', 'word/footer'))
                     and n.endswith('.xml')]
        require(len(ps) == m['paragraph_count'], f'{no}: paragraph metadata mismatch')
        require(sum(len(p) for p in ps) == m['character_count'], f'{no}: character metadata mismatch')
        require(sum(bool(p.strip()) for p in ps) == m['nonempty_paragraphs'],
                f'{no}: nonempty paragraph mismatch')
        require(len(xml.findall('.//' + NS + 'tbl')) == m['table_count'], f'{no}: table mismatch')
        require(media == m['media'] and sides == m['sideparts'], f'{no}: undisclosed DOCX content parts')
        require(not media and not sides, f'{no}: this text-only study needs supplemental reading')
        header = [f"报告 {no}：{m['title']}", f"源文件：{m['rel']}",
                  f"SHA-256：{m['source_sha256']}", 'P为原DOCX全部w:p的顺序编号，包含表格及空段；不是页码。', '']
        expected_text = '\n'.join(header + [f'P{i:03d} {p}' for i, p in enumerate(ps, 1) if p.strip()]) + '\n'
        txt = OUT / m['text_file']
        require(txt.read_text('utf-8') == expected_text, f'{no}: extracted reading text does not match DOCX')
        reading_hashes[m['text_file']] = sha(txt)
        paragraphs[no] = ps
        require(indexed[no].get('reliability_grade') == m['saved_reliability_grade'] and
                indexed[no].get('p0_audit_status') == m['saved_p0_status'],
                f'{no}: saved audit status changed during learning')

    for group, ids in manifest['group_assignments'].items():
        obj = read(OUT / f'{group}.json')
        require(obj['group'] == group, f'{group}: wrong group name')
        required_ids = {f'{n:03d}' for n in ids}
        group_records = obj['records']
        require({r['no'] for r in group_records} == required_ids and
                len(group_records) == len(required_ids), f'{group}: incomplete or duplicate coverage')
        require({str(n).zfill(3) for n in obj['report_ids']} == required_ids,
                f'{group}: report_ids inconsistent')
        require((OUT / f'{group}.md').is_file(), f'{group}: missing readable notes')
        readable = (OUT / f'{group}.md').read_text('utf-8')
        require(readable.strip() and all(f"## {r['no']} {r['title']}" in readable for r in group_records),
                f'{group}: readable notes missing report coverage')
        group_counts[group] = len(group_records)
        summaries[group] = {k: obj.get(k, []) for k in ['scope', 'cross_report_lessons', 'open_questions']}
        for r in group_records:
            no, m = r['no'], source_records[r['no']]
            require(r['title'] == m['title'] and r['rel'] == m['rel'], f'{no}: source identity mismatch')
            require(r['source_sha256'] == m['source_sha256'], f'{no}: card source hash mismatch')
            require(r['reading_status'] == 'full_text_read', f'{no}: incomplete declared reading')
            require(r['paragraph_count'] == m['paragraph_count'], f'{no}: card paragraph mismatch')
            require(len(r['transferable_rules']) >= 2, f'{no}: insufficient authored decisions')
            require(len(r['local_checks']) >= 1, f'{no}: missing local comparison')
            require(any(c.get('result') != 'not_checked' for c in r['local_checks']),
                    f'{no}: no completed specific local comparison')
            for key in ['tags', 'version_and_season_limits', 'non_transferable_claims', 'application_questions']:
                require(isinstance(r[key], list) and r[key] and all(isinstance(s, str) and s.strip() for s in r[key]),
                        f'{no}: missing/nontext {key}')
            require(isinstance(r['resource_dependencies'], list), f'{no}: resources must be list')
            require(set(r['related_report_ids']).issubset(source_records), f'{no}: invalid related report')
            for x in r['transferable_rules'] + r['local_checks']:
                require(x.get('evidence_paragraphs'), f'{no}: missing evidence anchors')
                for p in x['evidence_paragraphs']:
                    require(type(p) is int and 1 <= p <= len(paragraphs[no]) and paragraphs[no][p-1].strip(),
                            f'{no}: invalid/nonexistent evidence paragraph {p}')
            for x in r['transferable_rules']:
                for key in ['condition', 'decision', 'reason', 'failure_mode']:
                    require(isinstance(x.get(key), str) and x[key].strip(), f'{no}: blank rule {key}')
            for x in r['local_checks']:
                require(x['result'] in RESULTS, f'{no}: invalid check result')
                for key in ['claim', 'source', 'evidence', 'impact']:
                    require(isinstance(x.get(key), str) and x[key].strip(), f'{no}: blank check {key}')
            r['group'] = group
            r['saved_reliability_grade'] = m['saved_reliability_grade']
            r['saved_p0_status'] = m['saved_p0_status']
            all_records.append(r)
    all_records.sort(key=lambda x: x['no'])
    require({r['no'] for r in all_records} == set(indexed) and len(all_records) == len(indexed),
            'Consolidated reading coverage incomplete')

    local_evidence = read(OUT / '01_本地交叉核对证据.json')
    for rel, expected in local_evidence['source_hashes'].items():
        require(sha(ROOT / rel) == expected, f'Local check source changed: {rel}')
    supplemental = read(OUT / '补充本地核对证据.json')
    for rel, expected in supplemental['source_hashes'].items():
        require(sha(ROOT / rel) == expected, f'Supplemental check source changed: {rel}')
    saved_db = read(ROOT / '资料库/official_skill_db.json')
    for ref, saved in supplemental['saved_records'].items():
        section, name = ref.split('/', 1)
        require(saved_db[section].get(name) == saved, f'Local evidence record mismatch: {ref}')
    counts = Counter(c['result'] for r in all_records for c in r['local_checks'])
    validation = {
        'validation_date': '2026-10-12', 'study_started': manifest['study_date'],
        'status': 'pass', 'reports': len(all_records), 'group_reports': group_counts,
        'source_characters': manifest['total_characters'],
        'nonempty_source_paragraphs': manifest['total_nonempty_paragraphs'],
        'authored_decision_rules': sum(len(r['transferable_rules']) for r in all_records),
        'local_comparisons': sum(len(r['local_checks']) for r in all_records),
        'comparison_results': dict(counts),
        'current_online_parameters_verified': False,
        'source_docx_hashes_unchanged': True, 'saved_audit_grades_unchanged': True,
        'reading_text_hashes': reading_hashes,
        'validated_card_hashes': {f'{g}.json': sha(OUT / f'{g}.json') for g in group_counts},
        'local_check_source_hashes': local_evidence['source_hashes'],
        'limitations': [
            'Coverage, source fidelity and references are checked mechanically; reading quality was reviewed by the main agent.',
            'Full text reading is not a re-verification of retired upstream videos/frames.',
            'Saved local descriptions do not establish current online parameters, account holdings, or lineup strength.']}
    (OUT / '全量学习卡.json').write_text(json.dumps({
        'schema_version': 1, 'study_started': manifest['study_date'], 'study_completed': '2026-10-12',
        'scope': manifest['scope'], 'records': all_records, 'group_summaries': summaries,
        'validation': {k: v for k, v in validation.items() if not k.endswith('_hashes')}},
        ensure_ascii=False, indent=2) + '\n', 'utf-8')
    (OUT / '覆盖与溯源验收.json').write_text(json.dumps(validation, ensure_ascii=False, indent=2) + '\n', 'utf-8')

    lines = ['# 逐篇学习索引', '',
             '共67份活动报告。P为原DOCX段落编号，表格段落已包含；编号不是页码。', '',
             '| 编号 | 报告 | 主题 | 判断条数 | 核对条数 | 原存审计状态 |',
             '|---|---|---|---:|---:|---|']
    for r in all_records:
        m = source_records[r['no']]
        note = f"{r['group']}.md"
        lines.append(f"| {r['no']} | [{r['title']}]({m['text_file']}) | [专题笔记]({note}) | "
                     f"{len(r['transferable_rules'])} | {len(r['local_checks'])} | "
                     f"{m['saved_reliability_grade']} / {m['saved_p0_status']} |")
    lines += ['', '结构化检索见[全量学习卡](全量学习卡.json)；覆盖、源哈希与锚点核验见[验收记录](覆盖与溯源验收.json)。', '']
    (OUT / '逐篇学习索引.md').write_text('\n'.join(lines), 'utf-8')
    print(json.dumps({k: validation[k] for k in ['status', 'reports', 'group_reports',
          'authored_decision_rules', 'local_comparisons', 'comparison_results']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
