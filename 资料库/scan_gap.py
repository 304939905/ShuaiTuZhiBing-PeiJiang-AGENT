# -*- coding: utf-8 -*-
"""白名单缺口定位：抽取报告中"明确被当作战法名使用"的 token，
按频次列出不在官方白名单中的，用于判断是"报告错名"还是"官方库不全"。
判据：跨文件高频 + 结构规整(3-5字) => 大概率是库不全（典藏/新赛季战法）。
      单文件低频 + 生僻字   => 大概率是报告 OCR 错名。
"""
import sys, glob, re, os, json, collections
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

BASE = "D:/Desktop/shandou/资料库"
REP = "D:/Desktop/shandou/学习汇报"

jin = set(json.load(open(BASE + "/official_jineng_names_ext.json", encoding="utf-8"))["names"])
hero = set(json.load(open(BASE + "/official_hero_names.json", encoding="utf-8"))["names"])
gear = set(json.load(open(BASE + "/official_gear_names.json", encoding="utf-8"))["names"])
baowu = set(json.load(open(BASE + "/official_baowu_names.json", encoding="utf-8")))
h = json.load(open(BASE + "/hero.json", encoding="utf-8"))
hall = set()
if isinstance(h, list):
    for e in h:
        if isinstance(e, dict):
            for k in ("name", "heroName", "hero_name"):
                if e.get(k):
                    hall.add(str(e[k]))
WHITE = jin | hero | gear | baowu | hall

# 战法名语境：token 紧邻 战法/携带/自带/等级标记
PATS = [
    re.compile(r"[「『【]([\u4e00-\u9fff]{3,6})[」』】]\s*[（(](?:S2?级?|A级|B级|C级|G2|XP|典藏)"),
    re.compile(r"(?:战法|携带|自带|拆解)[^。\n]{0,6}[「『【]([\u4e00-\u9fff]{3,6})[」』】]"),
    re.compile(r"[「『【]([\u4e00-\u9fff]{3,6})[」』】][^。\n]{0,4}(?:战法|Lv\.|发动率|有效距离)"),
    re.compile(r"(?:^|[／/+＋、])([\u4e00-\u9fff]{3,6})(?=[／/+＋、][\u4e00-\u9fff]{3,6})"),
]
# 明显非战法的通用词
SKIP = set("""战法体系 队伍配置 逐帧确认 既有报告 音频转写 画面确认 无法确认 兵种特性 宝物词条
攻击距离 有效距离 语音转写 内政政策 战法经验 逐帧判读 时间点 可信度 证据来源 截图附录
垒实体系 战磐体系 神赏体系 百战体系 攻其体系 法刀体系 开荒专题 学习报告 深度学习""".split())

cnt = collections.Counter()
files = collections.defaultdict(set)
for f in sorted(glob.glob(REP + "/*_逐帧深度学习报告_1秒版.docx")) + \
         sorted(glob.glob(REP + "/*_完整学习报告.docx")):
    bn = os.path.basename(f)
    d = Document(f)
    t = "\n".join(p.text for p in d.paragraphs)
    for tb in d.tables:
        for r in tb.rows:
            for c in r.cells:
                t += "\n" + c.text
    for pat in PATS:
        for m in pat.finditer(t):
            tok = m.group(1)
            if tok in WHITE or tok in SKIP:
                continue
            cnt[tok] += 1
            files[tok].add(bn)

rows = [(tok, n, len(files[tok])) for tok, n in cnt.items() if n >= 2]
rows.sort(key=lambda x: (-x[2], -x[1]))
print(f"库外候选（出现>=2次）共 {len(rows)} 个\n")
print(f"{'token':<10}{'次数':>5}{'文件数':>7}   判定倾向")
print("-" * 60)
for tok, n, nf in rows[:45]:
    tend = "★ 疑官方库不全" if nf >= 3 else ("? 待核" if nf == 2 else "· 疑报告错名")
    print(f"{tok:<10}{n:>5}{nf:>7}   {tend}")
json.dump({t: {"n": n, "files": sorted(files[t])} for t, n, _ in rows},
          open(BASE + "/scan_gap.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\n[完成] scan_gap.json")
