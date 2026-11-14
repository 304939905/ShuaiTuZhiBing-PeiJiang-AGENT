# -*- coding: utf-8 -*-
"""
通用精编报告渲染器（文本型，无插图）
输入：资料库/frame_json/*.json 等（真实逐帧判读数据）
输出：报告库/<项目>/精编/<视频名>_精编学习报告.docx
附加：自动抽取武将/战法/宝物实体，对照本地官方库交叉核验；
      生成 索引块（关键词+武将版本标签+生成日期+路径）。
注：武将版本标签只出现在①报告开头索引块的「核心武将（版本）」清单
    ②正文阵容表的「武将（阵营-兵种-星级）」列。不再单独生成「武将版本对照表」节
    （与开头清单完全重复，纯冗余，已删除）。
"""
import json, os, re, glob, sys
from hero_version_resolver import HERO_NAMES as RESOLVER_HERO_NAMES, resolve_label

BASE = r'D:/Desktop/shandou'
LIB  = os.path.join(BASE, '资料库')
# 2026-08-19 物理归置后：精编报告统一落 报告库/<子项目>/精编/（原 学习成果汇总/<子项目>/）
OUT_ROOT = os.path.join(BASE, '报告库')
GEN_DATE = '2026-08-18'

# ---------- 加载本地官方库 ----------
def load_json(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)

# ---------- 2026-08-24 试点：来源节清洗（绝对路径脱敏 + 钩子过滤，同阵容新批方式）----------
import re as _re
_HOOK_RE = _re.compile(r'(欢迎评论区留下你的势力名|每期免费为粉丝进行个性化配将|免费为粉丝进行个性化配将|每期免费为粉丝进行|免费为粉丝进行|留下你的势力名)')
def _clean_hook(s):
    if not isinstance(s, str):
        return s
    return _HOOK_RE.sub('', s).strip(' ，。、；')
def _redact_path(s):
    if not isinstance(s, str):
        return s
    # 只脱敏盘符绝对路径；不能把 https:// 中的 "p://" 误识为 "p:" 路径，
    # 否则来源母本中真实的可复现直链会被裁成 "http"。
    s = _re.sub(r'(?i)(?<![a-z])[a-z]:[\\/][^ \n，。；（]+', '', s)
    s = _re.sub(r'（frame_[^）]*）', '', s)
    return s.strip(' ，。、；')
def _norm_terms(s):
    """术语统一：UP主/UP 主 → 作者（2026-08-24 全旧批自检发现母本 desc 残留）。"""
    if not isinstance(s, str):
        return s
    return _re.sub(r'UP\s*主', '作者', s)

_URL_RE = _re.compile(r'https?://[^\s，。；）)]+', _re.I)

def _source_items(value):
    """把母本来源规范成可显示的非空文本项。

    旧母本大多是字符串列表，少数可能是单个字符串；不能把字符串逐字符
    当作来源，也不能在来源缺失时补造“已核验”的外部站点声明。
    """
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        cleaned = _clean_hook(_redact_path(str(item)))
        if cleaned:
            out.append(cleaned)
    return out

def _source_urls(items):
    """只识别母本原文实际给出的可复现 HTTP(S) 直链。"""
    urls = []
    for item in items:
        for url in _URL_RE.findall(item):
            if url not in urls:
                urls.append(url)
    return urls

def _inference_source_notice(source_items):
    """AI 推断章节的证据边界，不以网站名称代替具体可复现链接。"""
    if _source_urls(source_items):
        return (
            '以下为 AI 基于本报告画面证据和本地资料库作出的延伸判断，非视频原话，'
            '不代表作者观点。外部资料仅限来源节实际列出的可复现直链；每条推断仍须结合其自身依据判断。'
        )
    return (
        '以下为 AI 基于本报告画面证据和本地资料库作出的延伸判断，非视频原话，'
        '不代表作者观点。来源节未列出可复现外部帖子直链，本报告不宣称已完成外部网站核验。'
    )

# 武将白名单（官方名，用于扫描）
ohn = load_json(os.path.join(LIB, 'official_hero_names.json'))
hero_names = set(ohn.get('names', [])) if isinstance(ohn, dict) else set(ohn)
hero_names |= RESOLVER_HERO_NAMES

# 战法白名单（扩展：通用 ∪ 武将自带）
ojx = load_json(os.path.join(LIB, 'official_jineng_names_ext.json'))
skill_names = set()
if isinstance(ojx, dict):
    skill_names |= set(ojx.get('common', []))
    skill_names |= set(ojx.get('innate_from_hero', []))
else:
    skill_names = set(ojx)

# 宝物白名单
gear = load_json(os.path.join(LIB, 'gear_id.json'))
gear_names = set()
if isinstance(gear, list):
    for g in gear:
        if isinstance(g, dict):
            gn = g.get('name') or g.get('gearName') or ''
            if gn:
                gear_names.add(gn.strip())
        elif isinstance(g, str):
            gear_names.add(g.strip())
elif isinstance(gear, dict):
    gear_names = set(gear.get('names', []))

# ---------- 实体提取 ----------
def find_entities(text):
    """返回 (heroes, skills, gears) 去重后的命中名列表。"""
    heroes, skills, gears = [], [], []
    # 武将：按长度降序匹配，避免子串重复
    for n in sorted(hero_names, key=len, reverse=True):
        if len(n) >= 2 and n in text:
            heroes.append(n)
    for n in sorted(skill_names, key=len, reverse=True):
        if len(n) >= 2 and n in text:
            skills.append(n)
    for n in sorted(gear_names, key=len, reverse=True):
        if len(n) >= 2 and n in text:
            gears.append(n)
    # 去子串：若短名是某长名的子串则丢弃
    heroes = dedupe_substr(heroes)
    skills = dedupe_substr(skills)
    gears  = dedupe_substr(gears)
    return heroes, skills, gears

def dedupe_substr(names):
    names = sorted(set(names), key=len, reverse=True)
    keep = []
    for n in names:
        if not any(n != m and n in m for m in keep):
            keep.append(n)
    return keep

def hero_label(name_in_text, evidence=None):
    """只按可回查的自带战法或完整卡面证据输出版本，禁止按姓名猜版本。

    ``evidence`` 来自母本 ``version_evidence``，键为武将名。自带战法优先；
    未见自带战法时，resolver 仅接受同帧的名称、阵营、星级和 SP/XP/无标识
    这四项齐全且唯一的卡面证据。文本中的“SP”字样本身不构成证据。
    """
    base = re.sub(r'(?i)SP|·|•', '', name_in_text).strip()
    evidence = evidence if isinstance(evidence, dict) else {}
    return resolve_label(
        base,
        builtin_skill=str(evidence.get('builtin_skill') or ''),
        visual_evidence=evidence,
    )

# ---------- 文本聚合 ----------
def collect_text(d):
    parts = []
    def add(x):
        if isinstance(x, str) and x.strip():
            parts.append(x)
        elif isinstance(x, list):
            for i in x:
                add(i)
        elif isinstance(x, dict):
            for v in x.values():
                add(v)
    sm = d.get('summary') or {}
    if sm.get('one_line'):
        parts.append(sm['one_line'])
    for x in (sm.get('visual_only') or []):
        add(x)
    add(d.get('timeline'))
    add(d.get('frame_only_value'))
    add(d.get('limitations'))
    add(d.get('glossary'))
    add(d.get('sources'))
    return '\n'.join(parts)

# ---------- 渲染 ----------
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

def set_cjk(doc):
    st = doc.styles['Normal']
    st.font.name = 'Microsoft YaHei'
    st._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')

def render(video_json_path, out_subdir, project_label):
    d = load_json(video_json_path)
    title = d.get('video_title') or os.path.splitext(os.path.basename(video_json_path))[0]
    text = collect_text(d)
    source_items = _source_items(d.get('sources'))
    heroes, skills, gears = find_entities(text)
    # 队伍简称、标题缩写等可能包含真实武将名（如“大张鲁”中的“张鲁”），
    # 只有母本明确列出实体排除项时才过滤，避免把简称拆成实际出阵武将。
    entity_exclusions = set(d.get('entity_exclusions') or [])
    heroes = [h for h in heroes if h not in entity_exclusions]
    version_evidence = d.get('version_evidence') or {}

    # 索引关键词
    kw = list(d.get('glossary') or [])
    kw += heroes[:6]
    kw += skills[:6]
    kw = [k for k in kw if k]
    kw_uniq = []
    for k in kw:
        if k not in kw_uniq:
            kw_uniq.append(k)
    kw_str = '、'.join(kw_uniq[:14])

    # 武将版本标签（按出现顺序去重）
    hero_labels = []
    seen = set()
    for h in heroes:
        lab = hero_label(h, version_evidence.get(h))
        key = h + lab
        if key not in seen:
            seen.add(key)
            hero_labels.append('{}（{}）'.format(h, lab))
    hero_label_str = '、'.join(hero_labels) if hero_labels else '（本报告未明确提及具体武将）'

    out_name = title + '_精编学习报告.docx'
    out_path = os.path.join(OUT_ROOT, out_subdir, '精编', out_name)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    doc = Document()
    set_cjk(doc)
    h = doc.add_heading('《{}》'.format(title), level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph('精编学习报告 · 基于逐帧画面判读 + 本地资料库交叉核验')
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.runs[0].font.size = Pt(10)
    sub.runs[0].font.color.rgb = RGBColor(110,110,110)

    # ===== 索引块 =====
    doc.add_paragraph()
    doc.add_heading('报告索引（检索用）', level=2)
    p = doc.add_paragraph(); p.add_run('关键词：').bold = True; p.add_run(kw_str)
    p = doc.add_paragraph(); p.add_run('核心武将（版本）：').bold = True; p.add_run(hero_label_str)
    p = doc.add_paragraph(); p.add_run('报告生成日期：').bold = True; p.add_run(d.get('report_date') or GEN_DATE)
    rel = '报告库/{}/精编/{}'.format(out_subdir, out_name)
    p = doc.add_paragraph(); p.add_run('报告路径：').bold = True; p.add_run(rel)

    # ===== 一、核心结论 =====
    doc.add_heading('一、视频核心结论', level=2)
    one_line = (d.get('summary') or {}).get('one_line') or '（无一句话结论）'
    doc.add_paragraph(one_line)
    vo = (d.get('summary') or {}).get('visual_only') or []
    if vo:
        doc.add_paragraph('画面要点（逐帧判读确认）：', style='Intense Quote')
        for x in vo:
            doc.add_paragraph(x, style='List Bullet')
    # ===== 二、逐帧要点 =====
    doc.add_heading('二、逐帧要点（时间轴）', level=2)
    tl = d.get('timeline') or []
    for seg in tl:
        rng = seg.get('range', '')
        ttl = seg.get('title', '')
        ph = doc.add_paragraph()
        ph.add_run('【{}】{}'.format(rng, ttl)).bold = True
        for fr in seg.get('frames', []):
            ts = fr.get('ts', '')
            desc = fr.get('desc', '')
            line = doc.add_paragraph(style='List Bullet')
            line.add_run('{} '.format(ts)).bold = True
            line.add_run(_norm_terms(desc))

    # ===== 三、逐帧独有价值 =====
    fov = d.get('frame_only_value') or []
    if fov:
        doc.add_heading('三、逐帧独有价值（仅画面可得）', level=2)
        for x in fov:
            doc.add_paragraph(x, style='List Bullet')

    # ===== 四、涉及实体清单 =====
    doc.add_heading('四、涉及实体清单（官方库核验命中）', level=2)
    doc.add_paragraph('武将 {} 名、战法 {} 个、宝物 {} 件。'.format(len(heroes), len(skills), len(gears)))
    if skills:
        doc.add_paragraph('涉及战法：' + '、'.join(skills[:40]), style='List Bullet')
    if gears:
        doc.add_paragraph('涉及宝物：' + '、'.join(gears), style='List Bullet')

    # ===== 五、局限 / 查不到 =====
    META_KW = ['转写','失真','无法还原','谐音','失帧','无法读取画面','旧报告','返工','初版']
    lim = d.get('limitations') or []
    lim = [x for x in lim if not any(k in x for k in META_KW)]
    if lim:
        doc.add_heading('五、局限与无法确认项', level=2)
        for x in lim:
            doc.add_paragraph(x, style='List Bullet')

    # ===== 六、AI 主动推断（物理隔离，单独成章） =====
    ai = d.get('ai_inference') or []
    if ai:
        doc.add_heading('六、AI 智能体主动推断内容（非视频原话，供参考）', level=2)
        doc.add_paragraph(_inference_source_notice(source_items), style='Intense Quote')
        for x in ai:
            if isinstance(x, dict):
                pt = x.get('point', '')
                ev = x.get('evidence', '')
                cf = x.get('confidence', '')
                line = doc.add_paragraph(style='List Bullet')
                line.add_run('推断：').bold = True
                line.add_run(pt)
                if ev:
                    sub = doc.add_paragraph(style='List Bullet')
                    sub.add_run('依据：').bold = True
                    sub.add_run(ev)
                if cf:
                    sub2 = doc.add_paragraph(style='List Bullet')
                    sub2.add_run('置信度：').bold = True
                    sub2.add_run(cf)
            else:
                doc.add_paragraph(str(x), style='List Bullet')

    # ===== 来源 =====
    doc.add_paragraph()
    p = doc.add_paragraph(); p.add_run('来源：').bold = True
    p.add_run('；'.join(source_items) if source_items else '未提供可追溯来源；不能据此主张外部核验。')
    p.runs[0].font.size = Pt(9)
    if len(p.runs) > 1:
        p.runs[1].font.size = Pt(9)
        p.runs[1].font.color.rgb = RGBColor(110,110,110)

    doc.save(out_path)
    return {
        'title': title, 'out': out_path, 'rel': rel,
        'kw': kw_str, 'hero_labels': hero_labels,
        'n_hero': len(heroes), 'n_skill': len(skills), 'n_gear': len(gears),
    }

if __name__ == '__main__':
    # 处理多个项目： (frame_json目录, 输出子目录, 项目标签)
    jobs = [
        (os.path.join(LIB, 'frame_json'),        '旧56项目', '旧56项目'),
        (os.path.join(LIB, 'frame_json_kaihuang'),'旧56项目', '旧56项目(开荒)'),
        (os.path.join(LIB, 'hzh_frame_json'),    '海之呼唤', '海之呼唤'),
        (os.path.join(LIB, 'saiji_frame_json'),  '赛季',     '赛季'),
    ]
    index_rows = []
    for src_dir, sub, label in jobs:
        if not os.path.isdir(src_dir):
            print('SKIP (no dir):', src_dir); continue
        files = sorted(glob.glob(os.path.join(src_dir, '*.json')))
        print('=== 项目 {} : {} 个 JSON ==='.format(label, len(files)))
        for fp in files:
            try:
                r = render(fp, sub, label)
                index_rows.append(r)
                print('  OK  {} | 武将{} 战法{} 宝物{}'.format(
                    r['title'][:30], r['n_hero'], r['n_skill'], r['n_gear']))
            except Exception as e:
                print('  FAIL {} -> {}'.format(os.path.basename(fp), e))
    # 写出索引数据（JSON），由独立步骤重建 reports_index.md，避免破坏既有结构
    if index_rows:
        dump = os.path.join(LIB, 'reports_index_rows.json')
        with open(dump, 'w', encoding='utf-8') as f:
            json.dump(index_rows, f, ensure_ascii=False, indent=1)
        print('=== 索引数据已写出: {} 条 -> {} ==='.format(len(index_rows), dump))
    print('DONE')
