# -*- coding: utf-8 -*-
"""Step1 数值断言 × 官方库核对 v2（只读，不改任何文件）

v2 关键改进：
  1. 属性 → **最近战法名** 绑定，且两者之间不得夹入另一个战法名（消除同句串味）
  2. 窗口收紧到 22 字
  3. 发动率排除「战报实测/加成后/调整公告」语境（报告引用的是加成后实际值，与官方基础值本就不同）
  4. 数值必须紧跟属性词，禁止跨越到下一个属性（消除「发动率、140%伤害率」误抓）
"""
import sys, os, re, json, glob

sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

BASE = os.path.dirname(os.path.abspath(__file__))
REP = "D:/Desktop/shandou/学习汇报"
DB = json.load(open(os.path.join(BASE, "official_skill_db.json"), encoding="utf-8"))
SK = DB["skills"]

NAMES = sorted([n for n in SK if len(n) >= 3], key=len, reverse=True)
NAME_RE = re.compile("|".join(re.escape(n) for n in NAMES))

# 数值必须紧跟属性词（≤6 字），且不得跨越顿号后接另一属性
P_PROB = re.compile(r"(?:发动率|发动概率|触发率|触发概率)(?:为|是|达|约|＝|=|：|:)?\s*(\d+(?:\.\d+)?)\s*[%％]")
P_QUAL = re.compile(r"(?<![A-Za-z])([SABC])\s*级")
P_TYPE = re.compile(r"(主动|被动|指挥|突击|阵法|追击|内政)\s*(?:战法|XP)")
P_DIST = re.compile(r"(?:距离|射程)(?:为|是|＝|=|：|:)?\s*([1-8])(?!\d)")

WIN = 22

# 引用语境：报告在复述作者口误/音频转写 → 不判错
CITE = re.compile(r"(?:既有报告|音频转写|音频版|转写|误写|误读|误作|作者(?:口误|说|称)|"
                  r"存疑|待核|无法确认|按视频|据视频|纠错|修正为|更正)")
# 加成/实测语境：战报显示的是加成后实际值，与官方基础值不同 → 不判错
BUFF = re.compile(r"(?:战报|日志|当前发动率|实测|实际|加成|增幅|红圈|提升至|→|>>|调整(?:前|后|公告)|"
                  r"由\s*\d+%|宝物|词条|谋议宏图|侵掠如火|buff|BUFF)")


def read_doc(f):
    doc = Document(f)
    t = "\n".join(p.text for p in doc.paragraphs)
    for tb in doc.tables:
        for r in tb.rows:
            for c in r.cells:
                t += "\n" + c.text
    return t


def bind(pos, names):
    """把属性位置 pos 绑定到最近的战法名，要求 ≤WIN 且中间不夹别的战法名。"""
    best = None
    for (s, e, n) in names:
        if e <= pos:
            d = pos - e
        elif s >= pos:
            d = s - pos
        else:
            d = 0
        if d > WIN:
            continue
        if best is None or d < best[0]:
            best = (d, s, e, n)
    if not best:
        return None
    d, s, e, n = best
    lo, hi = (e, pos) if e <= pos else (pos, s)
    for (s2, e2, n2) in names:
        if n2 == n:
            continue
        if s2 >= lo and e2 <= hi:      # 中间夹了别的战法名 → 绑定不可靠
            return None
    return n


def scan(f):
    text = read_doc(f)
    base = os.path.basename(f)
    names = [(m.start(), m.end(), m.group(0)) for m in NAME_RE.finditer(text)]
    hits = {"prob": [], "qual": [], "type": [], "dist": []}

    def ctx_of(p, w=40):
        return text[max(0, p - w):min(len(text), p + w)].replace("\n", " ")

    def push(kind, pos, name, claim, official):
        c = ctx_of(pos)
        hits[kind].append({"skill": name, "claim": claim, "official": official,
                           "cited": bool(CITE.search(c)), "buff": bool(BUFF.search(c)),
                           "ctx": c})

    for m in P_PROB.finditer(text):
        n = bind(m.start(), names)
        if not n:
            continue
        off = SK[n]["probability"]
        if not off or off == "--":
            continue
        ns = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", off)]
        if not ns:
            continue
        v = float(m.group(1))
        if v < min(ns) - 0.05 or v > max(ns) + 0.05:
            push("prob", m.start(), n, v, off)

    for m in P_QUAL.finditer(text):
        n = bind(m.start(), names)
        if not n:
            continue
        q = SK[n]["quality"]
        if q and m.group(1) != q:
            push("qual", m.start(), n, m.group(1), q)

    for m in P_TYPE.finditer(text):
        n = bind(m.start(), names)
        if not n:
            continue
        ot = SK[n]["type"].replace("战法", "").strip()
        if ot and m.group(1) != ot:
            push("type", m.start(), n, m.group(1), ot)

    for m in P_DIST.finditer(text):
        n = bind(m.start(), names)
        if not n:
            continue
        od = SK[n]["distance"]
        if od and int(m.group(1)) != od:
            push("dist", m.start(), n, int(m.group(1)), od)

    return base, hits


def main():
    sets = {
        "完整版": sorted(glob.glob(REP + "/*_完整学习报告.docx")),
        "一秒版": sorted(glob.glob(REP + "/*_逐帧深度学习报告_1秒版.docx")),
    }
    out = {}
    for label, files in sets.items():
        agg = {"prob": [], "qual": [], "type": [], "dist": []}
        for f in files:
            base, h = scan(f)
            for k in agg:
                for it in h[k]:
                    it["file"] = base
                    agg[k].append(it)
        out[label] = agg
        print("\n" + "=" * 70)
        print("【%s】%d 份" % (label, len(files)))
        for k, cn in (("prob", "发动率"), ("qual", "品质SABC"), ("type", "战法类型"), ("dist", "距离")):
            a = agg[k]
            hard = [x for x in a if not x["cited"] and not x["buff"]]
            print("  %-9s 命中 %3d | 排除引用/加成后 **%3d**" % (cn, len(a), len(hard)))
    json.dump(out, open(os.path.join(BASE, "check_numeric_report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n-> check_numeric_report.json")


if __name__ == "__main__":
    main()
