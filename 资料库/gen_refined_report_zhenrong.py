# -*- coding: utf-8 -*-
"""
阵容新批 精编报告渲染器（文本型，无插图）
输入：资料库/zhenrong_frame_json/*.json （子智能体逐帧真看 + 本地库/联网交叉核验产出）
输出：报告库/阵容新批/精编/<视频名>_精编学习报告.docx
      并导出索引增量到 资料库/zhenrong_index_rows.json
"""
import json, os, re, glob, sys
from hero_version_resolver import resolve_label

BASE = r'D:/Desktop/shandou'
LIB  = os.path.join(BASE, '资料库')
SRC  = os.path.join(LIB, 'zhenrong_frame_json')
# 2026-08-19 物理归置后：精编报告统一落 报告库/阵容新批/精编/（原 学习成果汇总/阵容新批/）
OUT  = os.path.join(BASE, '报告库', '阵容新批', '精编')
import datetime
GEN_DATE = datetime.date.today().isoformat()  # 报告生成日期=实际完成日(2026-08-22 用户规则)
os.makedirs(OUT, exist_ok=True)

def load_json(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)

# ---------- 位置词规整：把「大营吕蒙（」这类「位置+武将」融合写法转成「【大营】吕蒙（」 ----------
# 规则（来自 FRAME_AGENT_BRIEF 第 2 条）：武将标识只用版本标签，位置不并入武将名；
# 若需表达站位，用「【大营】/【中军】/【前锋】/【前排】」作为独立槽位标签。
_POS_RE = re.compile(r'(大营|中军|前锋|前排)([一-龥]{1,5})（')
def bracket_pos(text):
    """将 '大营吕蒙（...）' 形式规整为 '【大营】吕蒙（...）'，使位置与武将名解耦。"""
    if not isinstance(text, str):
        return text
    text = _POS_RE.sub(r'【\1】\2（', text)
    # 母本曾遗留“；；；”等重复分隔符；它们没有语义，不能进入精编成品。
    return re.sub(r'([；，。])\1+', r'\1', text)

# ---------- 精编只渲「最终正确流畅信息」：剔除 OCR/核验纠错过程叙述（审计底稿留 JSON，不进正文）----------
# 2026-08-22 用户规则：精编是消费型成品，纠错过程（画面字作X→官方Y）属审计元数据，只入 JSON 结构化字段，
# 不得写入精编正文/画面要点。下列正则把「画面 0 战法位字作「西乡武劝」A Lv.10，官方 methodName=「西乡武功」白名单收录…」
# 规整为干净的「西乡武功 A Lv.10」，对所有 14 份 + 未来 9 份统一生效。
import re as _re
_PROV_RE1 = _re.compile(r'画面\s*\d+\s*战法位字作「[^」]*」\s*((?:A|S|B)\s*Lv\.\d+)\s*，\s*官方\s*methodName=「([^」]*)」\s*白名单收录[，]?\s*[^）;]*')
_PROV_RE2 = _re.compile(r'画面\s*\d+\s*战法位\s*=\s*([^，]*?(?:A|S|B)\s*Lv\.\d+)\s*匹配官方\s*methodName')
_PROV_RE3 = _re.compile(r'（画面中「[^」]*」字作「[^」]*」为同音误写）')
# 战法列表内嵌纠错：知已知彼(A Lv.10，画面字「知已知彼」官方 methodName=「知己知彼」白名单收录，「己」/「已」疑为…) → 知己知彼(A Lv.10)
# 尾括号兼半/全角（真实数据用全角 ）
_PROV_RE4 = _re.compile(r'([一-鿿]+)\(((?:A|S|B)\s*Lv\.\d+)，画面字「[^」]*」\s*官方\s*methodName=「([^」]*)」\s*白名单收录[^）)]*[）)]')
# 武将头部无「画面字」前缀变体：「计谕废立」A Lv.10，官方 methodName=「计谕废立」白名单收录，「谟」/「谕」字形近）→ 删「，官方…」整段
_PROV_RE6 = _re.compile(r'，?\s*官方\s*methodName=「[^」]*」\s*白名单收录[^）)]*[）)]')
# ---------- 钩子话术过滤（2026-08-24 自检修复 A：投稿/免费配将钩子属冗余，不进精编正文）----------
_HOOK_RE = _re.compile(r'(欢迎评论区留下你的势力名|每期免费为粉丝进行个性化配将|免费为粉丝进行个性化配将|每期免费为粉丝进行|免费为粉丝进行|留下你的势力名)')
def _clean_hook(s):
    if not isinstance(s, str):
        return s
    return _HOOK_RE.sub('', s).strip(' ，。、；')
def _redact_path(s):
    """脱敏本地绝对路径（2026-08-24 复检：来源节曾泄漏 D:/Desktop/shandou/... 绝对路径）。"""
    if not isinstance(s, str):
        return s
    s = re.sub(r'[A-Za-z]:[\\/][^ \n，。；（]+', '', s)
    s = re.sub(r'（frame_[^）]*）', '', s)
    return s.strip(' ，。、；')

# ---------- 2026-08-24 复检：画面要点去冗余（精简，非删除）----------
# 阵容详解表已含 武将/战法/宝物 结构化信息；画面要点只留「视觉观察+字幕语境+作者逻辑」，
# 剥离与表重复的「带 A/S Lv.10 全量枚举」bullet，并去掉前缀时间戳噪声。
_VO_TS_RE = re.compile(r'^\s*\d\d:\d\d(?:\s*[–-]\s*\d\d:\d\d)?\s*')
def _strip_vo_prefix(s):
    return _VO_TS_RE.sub('', s).strip()
def _compress_vo(b):
    """混合型 bullet（枚举+字幕/观察并存）：去掉 大营/中军/前锋 全量枚举段，保留队伍名+字幕/观察尾巴。
    例：「第一队「X」弹窗全屏：大营 荀彧（…）带 驱虎吞狼(S Lv.10) / …；硬字幕「…」」→「第一队「X」弹窗；硬字幕「…」」"""
    b = re.sub(r'(大营|中军|前锋|前排)\s*[一-龥A-Za-z·&]{1,12}（[^）]*）带[^；。]*', '', b)
    b = re.sub(r'(大营|中军|前锋|前排)\s*[一-龥A-Za-z·&]{1,12}（[^）]*）', '', b)
    b = re.sub(r'弹窗全屏?[：:]', '弹窗；', b)
    b = re.sub(r'[，,、]?\s*；\s*', '；', b)
    return b.strip(' ，。、；')
def _is_redundant_vo(b, skill_names):
    """与阵容详解表重复的纯枚举 bullet → True（丢弃）。保留视觉观察/字幕/作者逻辑。"""
    insight = re.search(r'作者推荐|作者指出|作者评价|作者认为|核心|机制|利用|因为|所以|点评|建议|总结|整体|特征|疑|存疑|无法确认|查不到|硬字幕|字幕|聊天|赛季|势力值|武将池|账号', b)
    if insight:
        return False
    if re.search(r'[ABS]\s*Lv\.?\d', b):
        return True
    if re.search(r'（大营）|（中军）|（前锋）', b):
        return True
    if re.search(r'带\s|战法含|队伍|部队', b) and sum(1 for s in skill_names if s in b) >= 2:
        return True
    return False

# ---------- 2026-08-24 复检：AI推断节剥离审计噪声 ----------
# 保留「X疑为Y字形误读」等不确定性结论，剥离 methodName=验证/本地库查证/本视频按画面字面 等审计过程。
_AI_NOISE = [
    re.compile(r'[，。；]?\s*与官方(?:库)?[^，。；）]*?(?:完全一致|一致|相符|核验一致|匹配|字面均不符)[^，。；）]*'),
    re.compile(r'（[^）]*FOUND[^）]*）'),
    re.compile(r'，?\s*确认无误[^。；）]*'),
    re.compile(r'（[^）]*?(?:hero_extra|official_hero|methodName\s*=|id=\d+|quality=|probability=)[^）]*）'),
    re.compile(r'(?:本地\s*)?[（(]?official_hero_names\.json[^，。；）]*'),
    re.compile(r'(?:本地\s*)?[（(]?hero_extra\.json[^，。；）]*'),
    re.compile(r'（official_jineng_names_ext\.json[^）]*）'),
    re.compile(r'本地\s*战法白名单[^，。；）]*'),
    re.compile(r'methodName\d?\s*=?\s*[^，。；）]*'),
    re.compile(r'methodDesc1?\s*=\s*'),
    re.compile(r'官方\s*methodName[^，。；）]*'),
    re.compile(r'官方武将库已收录'),
    re.compile(r'∈\s*白名单|白名单[^，。；）]*收录'),
    re.compile(r'与官方(?:战法|宝物)库「[^」]*」一致'),
    re.compile(r'本视频按画面字面记录[^，。；）]*'),
    re.compile(r'，?\s*标注\s*OCR\s*存疑[^，。；）]*'),
    re.compile(r'[（(]uniqueName[^）)]*[）)]以?\s*'),
    re.compile(r'[（(]详情见本地库[）)]'),
    re.compile(r'hero_extra\s*'),
]
# 验证引用标记：命中即截断（证据/point/来源 的本地库查证尾巴）
_AI_VAL_MARK = re.compile(r'[；;]?\s*(?:官方战法库|官方宝物库|官方锻造词条库|vision_glm|frame_\d+|official_merged_whitelist|forge_traits|本地\s*(?:武将库|英雄库|战法白名单|hero_extra|official_hero))')
def _clean_ai(text):
    if not isinstance(text, str):
        return text
    t = text.strip()
    # ① 纯纠误叙述型 point：只留「画面字X武将疑为Y字形误读」结论+建议
    m = re.match(r'^(画面字「[^」]+」武将疑为「[^」]+」字形误读[：:]?)(.*)$', t)
    if m:
        sugg = re.search(r'建议[^。；]*', m.group(2))
        lead = m.group(1).rstrip('：:')
        return (lead + '。' + sugg.group(0) if sugg else lead).strip()
    # ② 从验证引用标记处截断（含开头「本地/官方战法库/vision_glm」等）
    t = _AI_VAL_MARK.split(t)[0]
    # ③ 战法位验证报告子句（完全匹配/全部与官方/误读 变体）
    t = re.sub(r'；?\s*作者?\s*\d+\s*战法位[^。；]*?(?:完全匹配|全部与官方|匹配|误读)[^。；]*[。；]?', '；', t)
    # ④ 逐项剥离审计噪声
    for rgx in _AI_NOISE:
        t = rgx.sub('', t)
    # ⑤ 垃圾清理
    return _clean_garbage(t)

def _clean_light(text):
    """2026-08-24 复检：核心结论/画面要点用的轻量清理——只剥离审计词（_AI_NOISE+垃圾清理），
    不做 _clean_ai 的 ①②③ 截断，保护消费型内容完整性。"""
    if not isinstance(text, str):
        return text
    t = text.strip()
    for rgx in _AI_NOISE:
        t = rgx.sub('', t)
    return _clean_garbage(t)

def _clean_garbage(t):
    t = re.sub(r'[，、；]*[）)]*\s*「[^」]*」\s*是?\s*FOUND[^，。；）]*', '', t)
    t = re.sub(r'[，、；\s]*[）)]+$', '', t)
    t = re.sub(r'[（(]\s*$', '', t)
    t = re.sub(r'[（(][^）)]*$', '', t)
    t = re.sub(r'^[^：]{1,12}核验[：:]\s*$', '', t)
    t = re.sub(r'[；;，]\s*[一-龥]{1,6}\s*[）)]', '）', t)
    t = re.sub(r'（依据：[）)]*）', '', t)
    t = re.sub(r'带自身\s*[，,]\s*', '带自身战法，', t)
    t = re.sub(r'，\s*，', '，', t)
    t = re.sub(r'，[；;]', '；', t)
    t = re.sub(r'（\s*[，,]\s*', '（', t)
    t = re.sub(r'\s*[，,]\s*）', '）', t)
    t = re.sub(r'（\s*）', '', t)
    return t.strip(' ，。、；')
def _norm_ts(s):
    return _re.sub(r'\d\d:\d\d(?:[–-]\d\d:\d\d)?', '', str(s))
def strip_provenance(text):
    """剔除武将头部/画面要点里的 OCR 纠错过程叙述，只留最终正确战法名+等级。"""
    if not isinstance(text, str):
        return text
    text = _PROV_RE1.sub(r'\2 \1', text)   # 「画面字作X...官方Y」→「Y 等级」
    text = _PROV_RE2.sub(r'\1', text)       # 「画面战法位 = Y 匹配官方」→「Y」
    text = _PROV_RE3.sub('', text)          # 删「（画面中X字作Y为同音误写）」括号注
    text = _PROV_RE4.sub(r'\3(\2)', text)   # 战法列表内嵌「画面字X官方Y」→「Y(等级)」
    text = _PROV_RE6.sub('', text)          # 删「，官方 methodName=「X」白名单收录…）」整段
    return text

# ---------- 本地官方库 ----------
hero_extra = load_json(os.path.join(LIB, 'hero_extra.json'))
# 2026-08-21 星级 bug 修复：hero_extra.quality 是「4-SR」稀有度格式且仅含 2-4 星卡（无 5 星，会导致全武将标 4 星）；
# 真实星级以 hero.json 的 quality 字段为准，且同名多条（普通/SP/XP 版）**只取首条**（官方排序=基础版在前，
# 首条星级与画面 desc 吻合，12/12 验证通过；取末条会命中 SP/高级版导致星级虚高）。
hero_json = load_json(os.path.join(LIB, 'hero.json'))
hero_star = {}
# skill_init（自带战法 ID）→ 星级：methodId 精确匹配版本的官方星级（2026-08-21 正解；
# 2026-08-22 修复：同名多版本取**众数**（排除 1 星野怪），setdefault 首条会命中界限版 6 星吕布）
from collections import Counter as _Ctr
si_cnt = {}
for x in hero_json:
    nm = (x.get('name') or '').strip()
    q = x.get('quality')
    si = x.get('skill_init')
    if nm and q is not None and nm not in hero_star:
        hero_star[nm] = str(q)[0]
    if si is not None and q is not None and int(q) >= 2:
        si_cnt.setdefault(str(si), []).append(str(q)[0])
si_star = {si: _Ctr(qs).most_common(1)[0][0] for si, qs in si_cnt.items()}

# 星级权威固化表（2026-08-21 用户要求：杜绝本地库启发式读取错误，直接查表）
_FIXED_P = os.path.join(LIB, 'hero_star_fixed.json')
_FIXED_STARS = {}
if os.path.exists(_FIXED_P):
    _fx = load_json(_FIXED_P)
    _FIXED_STARS = {k: str(v.get('star')) for k, v in (_fx.get('stars') or {}).items()}

def _star_of(nm):
    """星级：①固化表 hero_star_fixed.json（2026-08-21 权威）→ ②hero.json skill_init 匹配 → ③hero_extra quality 首字符。"""
    fx = _FIXED_STARS.get(nm)
    if fx:
        return fx
    s = hero_star.get(nm)
    if s:
        return s
    for e in hero_extra:
        if (e.get('name') or '').strip() == nm:
            q = (e.get('quality') or '').strip()
            return q[0] if q else '?'
    return '?'

hero_map = {}
_hero_star_best = {}   # 同名多版本：星级以固化表为准（2026-08-22 修复：max 取法会命中界限版 6 星吕布）
for e in hero_extra:
    nm = (e.get('name') or '').strip()
    if not nm: continue
    if nm not in _hero_star_best:
        fx = _FIXED_STARS.get(nm)
        _hero_star_best[nm] = fx if fx else (_star_of(nm) if '_star_of' in globals() else '?')
    hero_map[nm] = {'country': (e.get('country') or '').strip(),
                    'arms': (e.get('type') or '').strip(),
                    'star': _hero_star_best[nm],
                    'sp': bool(e.get('group')=='SP' or 'SP' in (e.get('groupName') or ''))}

ohn = load_json(os.path.join(LIB, 'official_hero_names.json'))
hero_names = set(ohn.get('names', [])) if isinstance(ohn, dict) else set(ohn)
hero_names |= set(hero_map.keys())

ojx = load_json(os.path.join(LIB, 'official_jineng_names_ext.json'))
skill_names = set()
if isinstance(ojx, dict):
    skill_names |= set(ojx.get('common', [])); skill_names |= set(ojx.get('innate_from_hero', []))
else:
    skill_names = set(ojx)
# 补充白名单：本地主库漏收的典藏/兑换战法（已联网核实）
sup_p = os.path.join(LIB, 'official_jineng_supplement.json')
if os.path.exists(sup_p):
    sup = load_json(sup_p)
    skill_names |= set(sup.get('names', []))

gear = load_json(os.path.join(LIB, 'gear_id.json'))
gear_names = set()
if isinstance(gear, list):
    for g in gear:
        if isinstance(g, dict):
            gn = g.get('name') or g.get('gearName') or ''
            if gn: gear_names.add(gn.strip())
        elif isinstance(g, str): gear_names.add(g.strip())
elif isinstance(gear, dict):
    gear_names = set(gear.get('names', []))

def hero_label(name):
    base = re.sub(r'(?i)SP|·|•', '', name).strip()
    return resolve_label(base)

# 自带战法 -> 武将精确版本（解决同名多星数问题）
# 2026-08-21 星级正解：hero_extra.methodId -> hero.json.skill_init -> quality（自带战法 ID 精确匹配版本）。
# 此前用 hero_extra.quality(4-SR 品质非星级) 或 hero.json 同名首条/末条（普通/SP/XP 多版本）都会取错，
# 用户肉眼核验 064/066/067 全员 5 星，methodId 匹配 12/12 一致。
method_map = {}
for e in hero_extra:
    mn = e.get('methodName')
    if isinstance(mn, str) and mn.strip():
        star = si_star.get(str(e.get('methodId'))) if e.get('methodId') is not None else None
        method_map[mn.strip()] = {
            'name': (e.get('name') or '').strip(),
            'country': (e.get('country') or '').strip(),
            'arms': (e.get('type') or '').strip(),
            'star': star or _star_of((e.get('name') or '').strip()),
            'sp': bool(e.get('group') == 'SP' or 'SP' in (e.get('groupName') or '')),
        }

def hero_label_by_skill(skill, fallback_name=''):
    """统一走版本解析器：自带战法优先，缺战法时不再按同名武将猜版本。"""
    name = (fallback_name or '').strip()
    if not name:
        info = method_map.get((skill or '').strip()) or {}
        name = (info.get('name') or '').strip()
    return resolve_label(name, builtin_skill=(skill or '').strip())

def _star_override_map(d):
    """读取 JSON entities.heroes 的 star_override（如「陈寿·敏学」升星特例：4星卡升5星但自带战法不变）
    → {武将名: 星级}。2026-08-22 用户核验宁元刀16队后确立。"""
    ovr = {}
    for h in (d.get('entities') or {}).get('heroes') or []:
        if isinstance(h, dict):
            s = h.get('star_override')
            nm = h.get('name')
            if s and nm:
                ovr[nm.strip()] = str(s)
    return ovr

def _apply_star_override(lab, hero_name, ovr):
    """画面星级覆盖：lab 形如「吴-弓-4星」，若武将命中 star_override 则替换星级。"""
    if hero_name in ovr:
        lab = re.sub(r'\d星', ovr[hero_name] + '星', lab)
    return lab

def _vlabel_map(d):
    """entities.heroes[].version_label 优先生效（仅标准格式 阵营-兵种-星级，兵种允许 弓/步 组合）：
    覆盖 method_map 对同名多版本武将的任意单选——如姜维列营守险有 蜀-弓/蜀-步 双版本、
    画面兵种图标不可判时 JSON 判定为「蜀-弓/步-5星」，method_map 会错误单选其一（2026-08-22 索引关键词核查发现）。
    非标格式（「群-?-5星」「5星极」「A & B」等）不覆盖，保持 method_map 回退。"""
    pat = re.compile(r'^(汉|魏|蜀|吴|群|晋)-(骑|步|弓|弓/步|步/弓)-[45]星(?:\((?:SP|XP|S2)\))?$')
    m = {}
    for h in (d.get('entities') or {}).get('heroes') or []:
        if not isinstance(h, dict) or not h.get('name'):
            continue
        if h.get('version_pending'):
            m[h['name'].strip()] = '版本待核实'
            continue
        # 画面已能锁定卡面标识、但需要同时保留升星/资料库缺项等限定语时，
        # 由审计母本显式给出展示标签。禁止在渲染器中再补猜版本。
        if h.get('version_display_label'):
            m[h['name'].strip()] = str(h['version_display_label']).strip()
            continue
        if h.get('version_label'):
            v = str(h['version_label']).strip()
            if pat.match(v):
                m[h['name'].strip()] = v
    return m

def skill_ok(n):  return n in skill_names

# 体系/玩法黑话（关键词提取词表：视频核心结论高频出现的体系词）
STYLE_WORDS = ['撸铁', '网红', '魏智', '核弹', '螃蟹', '流氓', '斩龙刀', '钢板', '神赏', '法刀',
               '蜀骑', '菜刀', '形兵', '双减', '肉队', '爆破', '顶配', '降配', '配将', '平民',
               '垒石', '开荒']

def extract_keywords(d):
    """关键词从「核心结论」提取（2026-08-21 用户规则：不再全并 glossary 108 词）：
    体系黑话（队伍名/ai_inference/summary 文本命中）+ 核心武将（每队首将）。限 12 个。"""
    teams = (d.get('entities') or {}).get('teams') or []
    ai = d.get('ai_inference') or []
    sm = d.get('summary') or {}
    parts = []
    for t in teams:
        parts.append(str(t.get('name') or ''))
    for x in ai:
        parts.append(str(x.get('point', '')) if isinstance(x, dict) else str(x))
    if isinstance(sm, dict):
        parts.append(str(sm.get('one_line') or ''))
    text = ' '.join(parts)
    kws = []
    for w in STYLE_WORDS:
        if w in text and w not in kws:
            kws.append(w)
    # 核心武将：每队首位武将名（队伍名首段 '+' 分隔，先去「（）」队名注解如 核弹（李儒…）→核弹）
    for t in teams:
        nm = str(t.get('name') or '').strip()
        nm = re.sub(r'（[^）]*）', '', nm)
        first = re.split(r'[+＋]', nm)[0].strip()
        if first and first not in kws and len(first) <= 6:
            kws.append(first)
    return kws[:12]
def gear_ok(n):    return n in gear_names

# ---------- 渲染 ----------
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from zhenrong_core_integrity import assert_complete_core

def set_cjk(doc):
    st = doc.styles['Normal']
    st.font.name = 'Microsoft YaHei'
    st._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')

def _trim_dangle(s):
    """去除尾部悬空/未闭合括号片段（写入截断防护，2026-08-24 复检发现母本多处 key_points 截断）。
    例：「③ 撸铁/螃蟹替代（华雄+木鹿大」→「③ 撸铁/螃蟹替代」；「9 个（避其锋芒/…/众」→「9 个」"""
    if not isinstance(s, str):
        return s
    s = s.strip()
    s = re.sub(r'[（(]\s*$', '', s)
    s = re.sub(r'[（(][^）)]*$', '', s)
    return s.strip(' ，。、；')
def H(doc, text, lvl=1):
    h = doc.add_heading(text, level=lvl)
    return h

def P(doc, text, bold=False):
    p = doc.add_paragraph()
    r = p.add_run(bracket_pos(text))
    r.bold = bold
    return p

def bullets(doc, items):
    for it in items:
        p = doc.add_paragraph(bracket_pos(str(it)), style='List Bullet')
        # 单条要点可容纳时不要跨页拆开；超过一页的段落仍由排版引擎自然分页。
        p.paragraph_format.keep_together = True

def _repeat_header(row):
    """让跨页阵容表重复表头，避免续页失去列含义。"""
    tr_pr = row._tr.get_or_add_trPr()
    tag = OxmlElement('w:tblHeader')
    # 空标签即表示启用；比显式 w:val 更兼容 Office/OpenXML 校验器。
    tr_pr.append(tag)

def _keep_table_row_intact(row):
    """禁止一条阵容记录被拆到两页；每行均小于一页，拆行只会产生孤立单元格。"""
    tr_pr = row._tr.get_or_add_trPr()
    tag = OxmlElement('w:cantSplit')
    tr_pr.append(tag)

def render(jpath):
    d = load_json(jpath)
    title = d.get('video_title') or os.path.splitext(os.path.basename(jpath))[0]
    doc = Document(); set_cjk(doc)
    doc.add_heading(title, level=0)

    # ---- 报告索引块 ----
    kw_list = extract_keywords(d)
    kw = '、'.join(kw_list) if kw_list else '—'
    teams = (d.get('entities') or {}).get('teams') or []
    star_ovr = _star_override_map(d)
    vovr = _vlabel_map(d)
    hero_seen = []
    hero_builtin = {h.get('name'): h.get('built_in_skill') for h in (d.get('entities') or {}).get('heroes') or [] if isinstance(h, dict)}
    # 2026-08-24 复检修复：跨队补全自带战法（部分队伍位置 skills 为空 → 从同 JSON 其他队伍同名武将继承 skills[0]，
    # 避免 hero_label 回退取 hero_extra 首个同名条目（如 经验之谈 曹操 skills=[] 时误取 汉·曹操 → 汉-骑-5星 错误标签））
    for _t in teams:
        for _pos in (_t.get('positions') or []):
            _h = (_pos.get('hero') or '').strip()
            _sk = _pos.get('skills') or []
            if _h and _sk and _h not in hero_builtin:
                hero_builtin[_h] = _sk[0]
    for t in teams:
        for pos in (t.get('positions') or []):
            h = (pos.get('hero') or '').strip()
            if h and h not in [x[0] for x in hero_seen]:
                sk = (pos.get('skills') or [])
                # 2026-08-22：战报对方武将 skills 常为空（画面仅卡面无战法位），
                # 回退 entities.heroes 已核验 built_in_skill 反查 method_map，避免 hero_label 名字查表对同名多版本取错兵种（如大乔弓/步）。
                innate = sk[0] if sk else (hero_builtin.get(h) or '')
                lab = vovr.get(h) or _apply_star_override(hero_label_by_skill(innate, h), h, star_ovr)
                hero_seen.append((h, lab))
    hero_labels = ['{}（{}）'.format(h, lab) for h, lab in hero_seen] if hero_seen else ['—']
    rel = '报告库/阵容新批/精编/' + title + '_精编学习报告.docx'
    P(doc, '【报告索引块】', bold=True)
    P(doc, '关键词：' + kw)
    P(doc, '核心武将（版本标签）：' + '、'.join(hero_labels))
    P(doc, '报告生成日期：' + GEN_DATE)
    P(doc, '本文件相对路径：' + rel)

    # ---- 一、核心结论与画面要点（2026-08-22 用户规则：删散文摘要，以 AI 阅读为唯一标准，冗余即删）----
    H(doc, '一、核心结论与画面要点', 1)
    sm = d.get('summary') or {}
    if isinstance(sm, dict):
        # 2026-08-21 用户建议：核心结论单独成节（攻其篇式），corrections 移入「四、视觉vs音频纠正」
        # 2026-08-22 用户规则：去除 one_line 散文摘要（与核心结论重复，AI 阅读无增量），仅保留结构化结论+画面要点
        # 优先采用母本中已人工复核的精编结论；旧 key_points 仅作兼容回退。
        # 不以 _trim_dangle 掩盖母本残句。核心结论缺失或截断时必须拒绝渲染，
        # 由人工补母本后再出成品，避免“看起来完整、实际缺信息”的精编报告。
        assert_complete_core(d, os.path.basename(jpath))
        kp = sm.get('refined_key_points') or sm.get('key_points') or []
        if kp:
            H(doc, '一·核心结论', 2)
            for k in kp:
                # 2026-08-24 复检：核心结论剥离审计括号 + 审计词（id=/methodName/与官方一致 等），不截断
                _k = re.sub(r'（[^）]*\bid=\d+[^）]*）', '', str(k))
                _k = _clean_light(_trim_dangle(_k))
                if _k:
                    # _clean_light/_trim_dangle 会剥离尾部标点；核心结论必须保留完整句界，
                    # 否则虽不再截断，成品仍会呈现为残句。
                    if _k[-1] not in '。！？':
                        _k += '。'
                    doc.add_paragraph(bracket_pos(_k), style='List Bullet')
        vo_raw = [str(v) for v in (sm.get('visual_only') or [])]
        if vo_raw:
            H(doc, '一·画面要点', 2)
            for v in vo_raw:
                vt = _clean_hook(strip_provenance(v))
                if not vt:
                    continue
                # 2026-08-24 复检去冗余：去前缀时间戳 + 先丢纯枚举 bullet，再压缩混合型枚举段
                vt = _strip_vo_prefix(vt)
                if _is_redundant_vo(vt, skill_names):
                    continue
                vt = _compress_vo(vt)
                vt = _clean_light(_trim_dangle(vt))
                if not vt:
                    continue
                doc.add_paragraph(bracket_pos(vt), style='List Bullet')
    else:
        P(doc, bracket_pos(str(sm)))

    # ---- 二、阵容详解 ----
    H(doc, '二、阵容详解（逐帧核实）', 1)
    if teams:
        # 2026-08-21 用户建议：阵容展示改用攻其篇式表格（原纯文本列表一行塞战法+宝物+词条，阅读差）
        from docx.shared import Inches
        tbl = doc.add_table(rows=1, cols=5)
        tbl.style = 'Light Grid Accent 1'
        hdr = tbl.rows[0].cells
        hdr[0].text = '队伍 / 定位'
        hdr[1].text = '武将（阵营-兵种-星级）'
        hdr[2].text = '战法配置（已核对画面）'
        hdr[3].text = '宝物 / 词条'
        hdr[4].text = '备注'
        _repeat_header(tbl.rows[0])
        for t in teams:
            name = t.get('name') or '未命名'
            slot = t.get('slot') or ''
            # 「不推荐」包含「推荐」子串，必须先判否定词，避免把作者明示否定的方案渲染为推荐。
            mark = '不推荐' if '不推荐' in name else ('推荐' if '推荐' in name else ('舍弃' if '舍弃' in name else '—'))
            clean_name = re.sub(r'[（(]UP[^）)]*[）)]|[（(][^）)]*队[^）)]*[）)]', '', name).strip()
            table_row = tbl.add_row()
            _keep_table_row_intact(table_row)
            row = table_row.cells
            row[0].text = '第{}队\n{}\n{}'.format(slot, clean_name, mark)
            heroes, skills_lines, gear_lines = [], [], []
            for pos in (t.get('positions') or []):
                hero = pos.get('hero') or '?'
                sk = (pos.get('skills') or [])
                # 2026-08-24 复检修复：表格段与索引块同源——空 skills 回退 hero_builtin（跨队补全），
                # 避免回退 hero_label 名字查表取 hero_extra 首个同名条目（经验之谈 曹操 → 汉·曹操 错误标签）
                innate = sk[0] if sk else (hero_builtin.get(hero) or '')
                # 队内同名武将可因自带战法对应不同版本；母本已给出画面锁定标签时，
                # 必须优先使用该位置标签，不能再由同名全局标签或资料库 season 字段补推 SP/XP。
                lab = pos.get('version_display_label') or vovr.get(hero) or _apply_star_override(hero_label_by_skill(innate, hero), hero, star_ovr)
                heroes.append('{} {}（{}）'.format(pos.get('pos'), hero, lab))
                skills_lines.append('{}：{}'.format(hero, ' / '.join(sk) if sk else '—'))
                g = pos.get('gear')
                tr = (pos.get('traits') or [])
                ut = (pos.get('unit_traits') or [])
                parts = []
                if g: parts.append('宝物 ' + str(g))
                if tr: parts.append('词条 ' + ' / '.join(tr))
                if ut: parts.append('兵种 ' + ' / '.join(ut))
                gear_lines.append('{}：{}'.format(hero, '；'.join(parts) if parts else '—'))
            row[1].text = '\n'.join(heroes)
            row[2].text = '\n'.join(skills_lines)
            row[3].text = '\n'.join(gear_lines)
            row[4].text = mark
        for i, w in enumerate([Inches(1.2), Inches(1.6), Inches(1.9), Inches(1.7), Inches(0.7)]):
            tbl.columns[i].width = w
    else:
        P(doc, '（本视频未结构化提取阵容，详见下方逐帧要点。）')

    # ---- 三、关键战法与宝物 ----
    ents = d.get('entities') or {}
    skills_all = ents.get('skills') or []
    gears_all = ents.get('gears') or []
    if skills_all or gears_all:
        H(doc, '三、关键战法与宝物', 1)
        if skills_all:
            names = []
            for s in skills_all:
                nm = s.get('name') if isinstance(s, dict) else str(s)
                mark = '⚠(未在本地库)' if (isinstance(s, dict) and not s.get('in_whitelist')) else ''
                names.append(nm + mark)
            P(doc, '战法：' + '、'.join(names))
        if gears_all:
            names = []
            for g in gears_all:
                nm = g.get('name') if isinstance(g, dict) else str(g)
                lv = '（已本地核验）' if (isinstance(g, dict) and g.get('local_verified')) else ''
                names.append(nm + lv)
            P(doc, '宝物：' + '、'.join(names))

    # ---- 四、视觉 vs 音频 纠正（2026-08-22 起从精编移除）----
    # 用户规则：精编是消费型成品，纠错过程（音频误读→画面实读）属审计元数据，不再渲进正文；
    # 审计底稿保留在 JSON 的 comparison / summary.corrections 字段，溯源可查。若需审计版单独呈现可另建渲染分支。
    # corr = d.get('comparison') or (sm.get('corrections') or [])
    # if corr:
    #     H(doc, '四、视觉判读对音频转写的纠正（体现逐帧真看价值）', 1)
    #     for c in corr:
    #         ...

    # ---- 五、术语与黑话 ----
    glossary = d.get('glossary') or []
    if glossary:
        H(doc, '四、术语与黑话', 1)
        P(doc, '、'.join(str(g) for g in glossary))

    # ---- 六、来源与证据索引 ----
    src = d.get('sources') or []
    if src:
        H(doc, '五、来源与证据索引', 1)
        src_items = []
        for s in src:
            v = _clean_hook(strip_provenance(_redact_path(_clean_ai(str(s)))))
            if v:
                src_items.append(v)
        bullets(doc, src_items)

    # ---- 七、局限与无法确认 ----
    lim = d.get('limitations') or []
    if lim:
        H(doc, '六、局限与无法确认（查不到/存疑）', 1)
        bullets(doc, [_clean_hook(strip_provenance(str(x))) for x in lim])

    # ---- 八、AI 智能体主动推断内容（非视频原话）----
    ai = d.get('ai_inference') or []
    if ai:
        H(doc, '七、AI 智能体主动推断内容（非视频原话，供参考）', 1)
        P(doc, '以下为我（AI 智能体）基于本报告的画面证据与本地官方资料库所作的延伸判断。这些内容不是视频原话、不代表作者观点；若来源节未给出可复现的外部帖子直链，不宣称已完成网易大神核验。')
        for it in ai:
            if isinstance(it, dict):
                txt = bracket_pos(_clean_hook(strip_provenance(_clean_ai(it.get('point') or ''))))
                ev = bracket_pos(_clean_hook(strip_provenance(_clean_ai(it.get('evidence') or ''))))
                cf = it.get('confidence') or ''
                # List Bullet 已提供项目符号；正文再写「·」会形成双重项目符号。
                line = str(txt)
                if ev: line += '（依据：' + str(ev) + '）'
                if cf: line += ' [置信度：' + str(cf) + ']'
                # LibreOffice 会把相邻的长 List Bullet 在同一视觉行上挤连；
                # AI 推断是短论证段，使用普通段落可保留清晰的段间边界。
                p = doc.add_paragraph(line)
                p.paragraph_format.keep_together = True
                p.paragraph_format.space_after = Pt(6)
            else:
                p = doc.add_paragraph(bracket_pos(str(it)))
                p.paragraph_format.keep_together = True
                p.paragraph_format.space_after = Pt(6)

    # 2026-08-24 全库统一（阵容新批 21 份精编）：精编定位「去冗余精华版」，
    # 逐帧时间线细节交 1 秒版，故删除第八节「逐帧时间线要点」整节——
    # 与第一节「画面要点」系统性重复且占全文近半（自检问题 D）；
    # C 的方法论重复（核心结论条 vs 逐帧 P110–114）随删节自动消除，仅留核心结论方法论条。
    # AI 智能体主动推断章节保持「七、」为末节，章节编号一~七连续无跳号。

    # 注：武将版本标签只出现在①报告开头索引块的「核心武将（版本）」清单
    #     ②正文阵容表的「武将（阵营-兵种-星级）」列。不再单独生成「武将版本对照表」节
    #     （与开头清单完全重复，纯冗余，已删除）。
    # 报告生成日期已写入开头索引块；页尾重复写入会在长报告中形成孤页，故不再重复输出。

    out_path = os.path.join(OUT, title + '_精编学习报告.docx')
    doc.save(out_path)
    # 索引增量
    row = {'title': title, 'kw': kw, 'hero_labels': hero_labels, 'rel': rel}
    return out_path, row

# ---------- 主流程 ----------
if __name__ == '__main__':
    paths = sorted(glob.glob(os.path.join(SRC, '*.json')))
    print('待渲染:', len(paths))
    rows = []
    for p in paths:
        try:
            op, row = render(p)
            rows.append(row)
            print('OK ->', op)
        except Exception as e:
            print('FAIL', p, e)
    with open(os.path.join(LIB, 'zhenrong_index_rows.json'), 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print('INDEX_ROWS=', len(rows))
    print('DONE')
