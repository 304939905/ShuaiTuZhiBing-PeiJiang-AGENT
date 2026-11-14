"""Record the completed reading of inherited methods without changing source files."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '资料库/策略知识库/迁移方法学习_20261012'

GROUPS = {
    '规则与项目记忆': [
        '.workbuddy/memory/RULES/01_卡面识别.md',
        '.workbuddy/memory/RULES/02_实体核验.md',
        '.workbuddy/memory/RULES/03_表述规范.md',
        '.workbuddy/memory/RULES/04_数据源.md',
        '.workbuddy/memory/RULES/05_流程.md',
        '.workbuddy/memory/MEMORY.md',
    ],
    '开发日志': [f'.workbuddy/memory/2026-08-{n:02d}.md' for n in
                 [7, 8, 9, 10, 18, 19, 20, 21, 22, 23, 24, 25]] +
                ['.workbuddy/memory/2026-09-01.md'],
    '交接与使用手册': [
        'HANDOFF_20261004.md', 'HANDOFF_轻量版_20260828.md',
        '迁移交接_20260928.md', 'USAGE_MANUAL_20260825.md',
        'USAGE_GUIDE.md', 'HANDOFF_PROMPT_20260825.md',
    ],
    '资料查询与概念': [
        '资料库/核验基准使用说明.md', '资料库/AA率土补充库说明.md',
        '资料库/official_db_index.md', '资料库/threshold_db_INDEX.md',
        '资料库/名词概念.md',
    ],
    '机制与战报方法': [
        '资料库/官方机制库/基础机制判断规则_20260901.md',
        '资料库/官方机制库/战法冲突判定规则_20260901.md',
        '资料库/官方机制库/战报阅读与配将反馈规则_20260921.md',
        '资料库/官方机制库/玩家实测机制参考_伤害恢复与战法阅读_20260921.md',
        '资料库/官方机制库/网易官网策略目录_机制学习与目录索引_20260901.md',
    ],
    '账号咨询入口': ['工具/配将服务/README.md', '资料库/账号信息获取教程.md'],
    '报告制作与取证规范': [
        '资料库/当前精编报告标杆.md', '资料库/REPORT_CONVENTIONS.md',
        '资料库/frame_report_schema.md', '资料库/report_schema.md',
        '资料库/FRAME_AGENT_BRIEF.md', '资料库/FRAME_AGENT_BRIEF_ZHENRONG.md',
        '资料库/FRAME_AGENT_BRIEF_赛季.md', '资料库/赛季报告独立学习材料审查.md',
        '资料库/视觉复盘_PoC_攻其篇粉丝投稿.md',
        '.workbuddy/skills/rate-earth-report/SKILL.md',
    ],
    '验收与退役记录': [
        '资料库/SOURCE_PROVENANCE_CHECK_20260826.md',
        '资料库/ZHENRONG_CORE_INTEGRITY_20260825.md',
        '资料库/REVIEW_PLAN.md',
        '资料库/audit_work/20260913_source_retirement_manifest/SOURCE_RETIREMENT_MANIFEST.md',
        '资料库/audit_work/20260913_source_retirement_manifest/DELETE_EXECUTION_RESULT.md',
        '资料库/audit_work/20260913_source_retirement_manifest/清理执行验收.md',
        '资料库/audit_work/20260913_source_retirement_manifest/二次精简执行验收.md',
        '接手审计_20261004/资料证据审计.md',
        '接手审计_20261004/工具服务审计.md',
        '资料库/README.md',
    ],
}

CODE = [f'工具/配将服务/{n}.py' for n in [
    'parse_account', 'validate_lineup', 'audit_consultation',
    'analyze_battle_reports', 'season_gate', 'test_service',
]] + [f'资料库/{n}.py' for n in [
    'hero_version_resolver', 'legacy_version_evidence',
    'source_provenance_check', 'zhenrong_core_integrity',
]]

DATA = [f'资料库/{n}.json' for n in [
    'hero', 'hero_extra', 'skill_extra', 'official_skill_db',
    'official_merged_whitelist', 'aa_rate_supplement',
    'gear_forge_pool', 'ocr_misread_map', 'threshold_db', 'reports_index_rows',
]]

# Fingerprints supplied after the agents' full reading, checked again by the primary agent.
READ_FINGERPRINTS = {
    '.workbuddy/memory/2026-08-07.md': '2D7E5E1C980FD0200656DA97848BF787F856D716865FB0A4D41A6A69A4477375',
    '.workbuddy/memory/2026-08-08.md': '08A7B35031AD63965E6145F2CC68BF5BA43ED93F07F1CE579E7D94EBB26CFC26',
    '.workbuddy/memory/2026-08-09.md': 'FE2776652E366C29D8A3C5821D1CC4FFEA8A4BAED492149BBD5B58996095090E',
    '.workbuddy/memory/2026-08-10.md': '7950A94AD7068F9B90860D51A9A28DF44F5A5A0D9084126E25B2014B32F44F93',
    '.workbuddy/memory/2026-08-18.md': '68FE230F85D6C6C723732F52A9483F12BDD51C8ED35387D371C022A635374732',
    '.workbuddy/memory/2026-08-19.md': '0FE470E03CD5DAF00DB5CFF7F3AF327C4D85AC4C0F2FC1739DEEFE8D63598E88',
    '.workbuddy/memory/2026-08-20.md': '897FEF72394F10160C908D9E1DEA3D0F6D1DDD7F4E3203F74EDE1CA03F455143',
    '.workbuddy/memory/2026-08-21.md': '47660AE8D92FBFB0D0B81802D25E0FFDED2AB922385B20B8428ECE1893E6B375',
    '.workbuddy/memory/2026-08-22.md': 'F5423B71306849B5E32154A657D779B350B598F18639ABD2B63F2890636EA9E6',
    '资料库/名词概念.md': '602997A5F4E1F693169CAA47333D050286474C6D1404D867D3B4A44C5888F39B',
    '.workbuddy/memory/RULES/01_卡面识别.md': '07757853D209CE9C497EAD0016EB8259C2664D11E91886BCD4F82FCE50B36C44',
    '.workbuddy/memory/RULES/02_实体核验.md': 'B3E023D0FCF13508A569100F6229569B309B8821807A1B8570472BD499A467ED',
    '.workbuddy/memory/RULES/03_表述规范.md': '1F7F16ABD4CCFB114318AFF533C5C4FE9D96AB4088AA9A562B82EC0D50C5DA96',
    '.workbuddy/memory/RULES/04_数据源.md': 'A65B0C770285127729D6960761ECB6C528042A106AB9B5E29FA0BD571CCE8C11',
    '.workbuddy/memory/RULES/05_流程.md': '9AE9DB7817D9504192DF06F16D251C9D60697B749B4DA0A0AD5FC2B17500659F',
}

NOTES = {
    '规则与项目记忆': '继承原规则与偏好；按明确后续定案处理内部旧句冲突，不把旧进度当现状。',
    '开发日志': '全文学习事件、最终决策与失败经验；数量、旧账号、当年挂起任务不自动续作。',
    '交接与使用手册': '学习零上下文接手和资产路由；旧路径、旧命令及旧格式只作历史记录。',
    '资料查询与概念': '学习字段结构、分层查询与唯一性；词库、阈值表及索引中的矛盾另查证据。',
    '机制与战报方法': '采用结构检查、逐效果判冲突和首次异常复盘；历史系数与同源实测不能升格。',
    '账号咨询入口': '按本次账号取证、前三主力、全局验收、施政、战报反馈执行；程序与人工职责分开。',
    '报告制作与取证规范': '新标杆和制作闭环优先；旧取证格式、已退役输入及旧环境不可照抄执行。',
    '验收与退役记录': '学习范围、证据和完成状态核验；区分预演、实际执行与源退役模式测试。',
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    for group, names in GROUPS.items():
        for name in names:
            path = ROOT / name
            source = path.read_text('utf-8-sig')
            fingerprint = sha(path)
            if name in READ_FINGERPRINTS:
                assert fingerprint == READ_FINGERPRINTS[name].lower(), f'Read source changed: {name}'
            records.append(dict(path=name, group=group, reading_status='full_text_read',
                lines=len(source.splitlines()), characters=len(source), sha256=fingerprint,
                use=NOTES[group], scope='学习保存文本；未重新认证线上参数或历史原图'))
    assert len(records) == len({r['path'] for r in records}) == 57
    assert len(GROUPS['开发日志']) == 13
    code = []
    for name in CODE:
        path = ROOT / name
        code.append(dict(path=name, reading_status='full_source_read',
                         lines=len(path.read_text('utf-8-sig').splitlines()), sha256=sha(path)))
    data = []
    for name in DATA:
        path = ROOT / name
        obj = json.loads(path.read_text('utf-8-sig'))
        shape = dict(type=type(obj).__name__, count=len(obj))
        if isinstance(obj, dict):
            shape['sections'] = {k: dict(type=type(v).__name__,
                count=len(v) if isinstance(v, (dict, list)) else None) for k, v in obj.items()}
        data.append(dict(path=name, reading_status='schema_and_selected_records_reviewed',
                         sha256=sha(path), shape=shape,
                         scope='核对用途、结构、ID关联和选定记录；未逐条宣称数据当前有效'))

    read_paths = {r['path'] for r in records}
    inventories = []
    for path in sorted(ROOT.rglob('*.md')):
        rel = path.relative_to(ROOT).as_posix()
        if '策略知识库' in path.parts or '.codex_tmp' in path.parts or path.parent.name.startswith('_tmp_'):
            continue
        inventories.append(dict(path=rel,
            status='full_text_read' if rel in read_paths else 'inventory_only',
            scope='核心全文学习' if rel in read_paths else '仅定位；按问题进一步阅读，不计入全文完成数'))

    environment = dict(
        packages={n: importlib.util.find_spec(n) is not None for n in
                  ['docx', 'PIL', 'numpy', 'cv2', 'fitz', 'faster_whisper', 'requests']},
        path_commands={n: shutil.which(n) for n in ['ffmpeg', 'ffprobe', 'soffice']},
        missing_source_directories={n: not (ROOT / n).exists() for n in
            ['抖音', '抖音_frames_dense_1s', '抖音_transcripts', '资料库/frame_json',
             '资料库/zhenrong_frame_json', '资料库/zhenrong_recon', 'AA率土']},
        scope='当前解释器与PATH；不代表整机无其他安装；未发起视觉/API调用')
    result = dict(study_date='2026-10-12', full_text_documents=len(records),
        full_source_files=len(code), data_structures_reviewed=len(data),
        inherited_daily_memories=13, project_long_term_memory_read=True,
        records=records, code_records=code, data_records=data,
        other_markdown_inventory=inventories, environment=environment,
        separate_completed_report_study='资料库/策略知识库/精编全量学习_20261011/逐篇学习索引.md',
        scope='迁移知识与成熟方法学习；不自动恢复历史任务或升级游戏事实/账号证据。')
    (OUT / '学习登记.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', 'utf-8')

    import os
    lines = ['# 迁移方法学习文件索引', '',
             '2026-10-12：57份文档全文、10份源码全文；10个资料文件核对结构和选定记录。',
             '原项目长期记忆及13份开发日志均包含在57份中。未计入全文阅读的其他文件明确标为仅定位。',
             '角色与适用范围见[学习登记](学习登记.json)；方法与优先关系见[接手入口](../../../迁移知识与流程接手_20261012.md)。', '']
    for group in GROUPS:
        lines += [f'## {group}', '', NOTES[group], '', '| 文件 | 行数 | 状态 |', '|---|---:|---|']
        for r in records:
            if r['group'] != group:
                continue
            target = os.path.relpath(ROOT / r['path'], OUT).replace('\\', '/')
            lines.append(f"| [{r['path']}](<{target}>) | {r['lines']} | 全文已读 |")
        lines.append('')
    lines += ['## 实现与资料结构', '',
              '源码全文覆盖：配将服务5脚本与测试、版本解析、旧版证据兼容、来源检查、核心结论守卫。',
              '资料结构覆盖：武将主库/补充、战法、规范库、五类白名单、AA补充、锻造池、误读映射、阈值与活动报告索引。',
              '这些检查不证明资料每条当前有效。结构测试不替代当前文本、真实账号和完整事件证据。', '']
    (OUT / '文件索引.md').write_text('\n'.join(lines), 'utf-8')
    print(json.dumps({k: result[k] for k in ['full_text_documents', 'full_source_files',
          'data_structures_reviewed', 'inherited_daily_memories']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
