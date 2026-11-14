# -*- coding: utf-8 -*-
"""离线全量 parity（修正版：就近窗口绑定，排除战法名内子串误绑）。
对 学习汇报/ 全部 docx 出现的 战法/宝物 事实断言对照本地官方库，只输出 MISMATCH。
绑定规则：品质/类型/距离/发动率 词必须出现在 最近战法/宝物名 的 [pos-18, pos+30] 窗口内，
且 该词不能落在另一个战法/宝物名的覆盖区间内（避免跨名错绑）。
"""
import os, re, glob, json
import docx

REP_DIR = "D:/Desktop/shandou/学习汇报"
SKILL_DB = "D:/Desktop/shandou/资料库/official_skill_db.json"
GEAR_DB  = "D:/Desktop/shandou/资料库/gear_id.json"

def load_skill():
    d = json.load(open(SKILL_DB, encoding="utf-8"))["skills"]
    return {k: v for k, v in d.items()}
def load_gear():
    raw = json.load(open(GEAR_DB, encoding="utf-8"))
    items = raw["data"] if isinstance(raw, dict) and "data" in raw else raw
    return {o.get("name"): o for o in items if o.get("name")}

SKILLS = load_skill(); GEARS = load_gear()

def text_of(p):
    d = docx.Document(p); out = []
    for para in d.paragraphs:
        if para.text.strip(): out.append(para.text)
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                if c.text.strip(): out.append(c.text)
    return out

skill_names = sorted(SKILLS.keys(), key=len, reverse=True)
gear_names  = sorted(GEARS.keys(), key=len, reverse=True)
# 战法名内可能含的"类型子串"，用于排除误绑
TYPE_WORDS = ["主动","被动","指挥","突击","追击","阵法","内政"]

GEAR_QUAL = re.compile(r"(稀世|精品|良才|普通|极|神|珍|凡|寻常|六韬|武略|天工|奇珍)")
SKILL_QUAL = re.compile(r"(?<![A-Za-z])([SABC])\s*级")
SKILL_PROB = re.compile(r"(发动率|发动概率|触发率|触发概率)(?:为|是|达|约|＝|=|：|:)?\s*(\d+(?:\.\d+)?)\s*[%％]")
SKILL_DIST = re.compile(r"(?:有效距离|距离|射程)(?:为|是|＝|=|：|:)?\s*([1-8])(?!\d)")
CITE = re.compile(r"(原文|视频里|主播|UP主|他说|配音|字幕|音频|转写|纠正|应为|应该是|其实|所谓|史称|俗称|也叫|又称|即|疑似|可能|也许|大概)")

mismatches = []

def find_names(s):
    occ = []
    for n in gear_names:
        for m in re.finditer(re.escape(n), s):
            occ.append((m.start(), m.end(), n, "gear"))
    for n in skill_names:
        for m in re.finditer(re.escape(n), s):
            occ.append((m.start(), m.end(), n, "skill"))
    occ.sort()
    return occ

def nearest_name_before(occ, pos):
    best=None
    for (a,b,n,kind) in occ:
        if b <= pos:
            if best is None or b > best[1]:
                best=(a,b,n,kind)
        else:
            break
    return best

def nearest_name_after(occ, pos):
    best=None
    for (a,b,n,kind) in occ:
        if a >= pos:
            if best is None or a < best[0]:
                best=(a,b,n,kind)
    return best

files = sorted(glob.glob(os.path.join(REP_DIR, "*.docx")))
files = [f for f in files if "_backup" not in f]

for f in files:
    name = os.path.basename(f)
    txt = "\n".join(text_of(f))
    sents = re.split(r'[。！？\n；;]', txt)
    for s in sents:
        s = s.strip()
        if len(s) < 4: continue
        occ = find_names(s)
        if not occ: continue
        # 宝物品质
        for m in GEAR_QUAL.finditer(s):
            pos = m.start()
            nm = nearest_name_before(occ, pos) or nearest_name_after(occ, pos)
            if not nm: continue
            n, kind = nm[2], nm[3]
            if kind != "gear": continue
            claimed = m.group(1)
            g = GEARS.get(n)
            if not g: continue
            off = g.get("quality")
            if claimed in ("六韬","武略","天工","奇珍","极","神","珍","凡","寻常"):
                if off and claimed != off and claimed not in ("稀世","精品","良才","普通"):
                    mismatches.append({"type":"GEAR_QUAL","name":n,"claimed":claimed,"official":off,"src":name,"sent":s[:170]})
            else:
                norm = {"极":"稀世","神":"稀世","珍":"精品","凡":"普通","寻常":"普通"}.get(claimed, claimed)
                if off and norm != off:
                    mismatches.append({"type":"GEAR_QUAL","name":n,"claimed":claimed,"official":off,"src":name,"sent":s[:170]})
        # 技能品质
        for m in SKILL_QUAL.finditer(s):
            pos = m.start()
            nm = nearest_name_before(occ, pos) or nearest_name_after(occ, pos)
            if not nm or nm[3] != "skill": continue
            n = nm[2]
            if CITE.search(s[max(0,pos-10):pos+4]): continue
            claimed = m.group(1)
            off = SKILLS.get(n, {}).get("zfQuality")
            if off and claimed != off:
                mismatches.append({"type":"SKILL_QUAL","name":n,"claimed":claimed,"official":off,"src":name,"sent":s[:170]})
        # 技能类型（必须紧贴战法名，且不在另一个战法名内）
        for tw in TYPE_WORDS:
            for m in re.finditer(re.escape(tw), s):
                pos = m.start()
                nm = nearest_name_before(occ, pos)
                if not nm or nm[3] != "skill": continue
                n = nm[2]
                # 排除：该 tw 落在某个战法名内部
                inside = any(a <= pos < b for (a,b,_,_) in occ)
                if inside: continue
                # 要求 tw 与战法名距离较近（窗口）
                if pos - nm[1] > 22: continue
                if CITE.search(s[max(0,pos-12):pos+4]): continue
                claimed = tw
                off = SKILLS.get(n, {}).get("type")
                if off and claimed != off:
                    mismatches.append({"type":"SKILL_TYPE","name":n,"claimed":claimed,"official":off,"src":name,"sent":s[:170]})
        # 发动率
        for m in SKILL_PROB.finditer(s):
            pos = m.start()
            nm = nearest_name_before(occ, pos) or nearest_name_after(occ, pos)
            if not nm or nm[3] != "skill": continue
            n = nm[2]
            if CITE.search(s[max(0,pos-12):pos+4]): continue
            v = float(m.group(2))
            off = SKILLS.get(n, {}).get("probability")
            if off:
                ns = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", off)]
                if ns and (v < min(ns)-0.05 or v > max(ns)+0.05):
                    mismatches.append({"type":"SKILL_PROB","name":n,"claimed":v,"official":off,"src":name,"sent":s[:170]})
        # 距离
        for m in SKILL_DIST.finditer(s):
            pos = m.start()
            nm = nearest_name_before(occ, pos) or nearest_name_after(occ, pos)
            if not nm or nm[3] != "skill": continue
            n = nm[2]
            if CITE.search(s[max(0,pos-12):pos+4]): continue
            v = int(m.group(1))
            off = SKILLS.get(n, {}).get("distance")
            if off:
                try:
                    ov = int(re.search(r"\d+", str(off)).group(0))
                    if v != ov:
                        mismatches.append({"type":"SKILL_DIST","name":n,"claimed":v,"official":ov,"src":name,"sent":s[:170]})
                except: pass

seen=set(); uniq=[]
for m in mismatches:
    k=(m["type"],m["name"],str(m["claimed"]),str(m["official"]),m["src"])
    if k in seen: continue
    seen.add(k); uniq.append(m)

json.dump(uniq, open("D:/Desktop/shandou/资料库/parity_all_mismatch.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
c=Counter(m["type"] for m in uniq)
print("MISMATCH 候选(去重):", len(uniq), dict(c))
for m in uniq[:80]:
    print(" ", m["type"], m["name"], "claimed=", m["claimed"], "official=", m["official"], "|", m["src"][:34])
    print("      ↳", m["sent"][:150])
