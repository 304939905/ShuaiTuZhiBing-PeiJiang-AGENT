# -*- coding: utf-8 -*-
"""阶段0 v2：51份1秒版报告 只读缺陷盘点（不改任何文件）。
在 v1 槽位提取法基础上做两层降噪：
  1) BLACKLIST：游戏黑话/通用词（非专名），即便与专名 hamming1 也不算误识；
  2) 跨报告词频投票：token 在 >=3 份报告中原样出现 => 视为真实术语（假阳性）剔除；
     反之 correct(应为名) 出现频次 > token 频次 => 高置信真实错误。
输出：资料库/PHASE0_DEFECT_REPORT_v2.md + .json
"""
import json, re, os, glob
from docx import Document
from collections import Counter

BASE = r"D:/Desktop/shandou"
LIB = os.path.join(BASE, "资料库")

def jload(p):
    return json.load(open(os.path.join(LIB, p), encoding="utf-8"))

# ---------- 加载白名单 ----------
hn = set(jload("official_hero_names.json")["names"])
je = jload("official_jineng_names_ext.json")
skills = set(je.get("common", [])) | set(je.get("innate_from_hero", []))
gears = set(jload("official_gear_names.json")["names"])
all_names = hn | skills | gears
heroes_star = {h["name"]: int(h["quality"]) for h in jload("hero.json")
               if "name" in h and str(h.get("quality", "")).isdigit()}

names_by_len = {2: set(), 3: set(), 4: set()}
for n in all_names:
    if 2 <= len(n) <= 4:
        names_by_len[len(n)].add(n)

td = jload("threshold_db.json")
td_skills = set()
for c in td["categories"]:
    for e in c["entries"]:
        td_skills.add(e["skill"])

# ---------- 黑话/通用词黑名单（左侧 token 为假阳性，非专名） ----------
BLACKLIST = {
    # 率土黑话/体系名（真实存在，非误识）
    "神赏","法刀","鬼吕","魏智","关妹","双减","机势","强韧","百战","攻其",
    "无心","神赏体系","三势",
    # 通用词/常用短语（非专名）
    "前锋","攻击","自己","大佬","游戏","中军","减伤","增伤","三军","全军",
    "谋略","保护","成功","成立","成略","假设","大补","大火","大幅","重整",
    "陷阵","乱世","藤甲","别名","散射","骑射","猛烈","淬火","棋火","坚忍",
    "坚韧","坚毅","仁心","狗粮","迅锋","神速","楚汉","灵动","马镫","武勋",
    "山寨","小时","陈留","李典","朱桓","王粲","象兵","双封","合纵","分城",
    "戍城","莫言","彦士","掩饰","推断","才军","荣誉","珍宝","修正","游兵",
    "象攻","骨石","白龙","黄金","透胜","远攻","苗刀","纯刀","斩龙","驱卢",
    "驱逻","破敌","破凰","横行","横勒","三军","全军","中军","减伤","增伤",
    "保护","成功","成立","假设","大补","大火","大幅","山寨","小时","灵动",
    "马镫","武勋","关妹","双减","魏智","攻其","无心","百战","神赏","法刀",
    "鬼吕","自己","大佬","游戏","前锋","攻击","中军","三军","全军","谋略",
}

CJK = re.compile(r"[一-鿿]")
def is_cjk(s):
    return bool(s) and bool(re.fullmatch(r"[一-鿿]+", s))
STAR_RE = re.compile(r"(五星|四星|三星|二星|一星|[0-9]星|★[0-9]|[0-9]★)")
# 星级否定语境：这些词出现说明"星"不是指武将稀有度
STAR_NEG = ["材料","升级","实战","内政","版本","Lv","lv","v.",".4","觉醒",
            "进阶","练兵","战法","宝物","避开","评级","难度","养成","白袍"]

def extract_text(path):
    d = Document(path)
    out = []
    for p in d.paragraphs:
        if p.text.strip():
            out.append(p.text)
    for t in d.tables:
        for row in t.rows:
            out.append(" | ".join(c.text for c in row.cells))
    return "\n".join(out)

def parse_star(s):
    s = s.strip()
    for cn, v in [("五", 5), ("四", 4), ("三", 3), ("二", 2), ("一", 1)]:
        if cn in s:
            return v
    m = re.search(r"[0-9]", s)
    return int(m.group(0)) if m else None

def star_scan(text):
    flags = []
    for name in hn:
        if name not in text:
            continue
        for m in re.finditer(re.escape(name), text):
            seg = text[max(0, m.start() - 4): m.end() + 4]   # 收紧到 ±4 字
            if any(k in seg for k in STAR_NEG):
                continue
            sm = STAR_RE.search(seg)
            if sm:
                claimed = parse_star(sm.group(0))
                real = heroes_star.get(name)
                if claimed and real and claimed != real:
                    flags.append({"hero": name, "claimed": claimed, "real": real,
                                  "ctx": text[max(0, m.start()-10): m.end()+10].strip()})
                break
    return flags

def hamming1(a, b):
    if len(a) != len(b):
        return False
    return sum(1 for x, y in zip(a, b) if x != y) == 1

SLOT_PATTERNS = [
    r"[「【“”‘']\s*([一-鿿]{2,4})\s*[」】“”’']",
    r"(?:战法|武将|携\s*带|自\s*带|名\s*称?)\s*[：: ]\s*([一-鿿]{2,4})",
    r"([一-鿿]{2,4})\s*[（(]",
    r"【([一-鿿]{2,4})】",
]

def extract_slots(text):
    toks = []
    for pat in SLOT_PATTERNS:
        for m in re.finditer(pat, text):
            tok = m.group(1).strip()
            if 2 <= len(tok) <= 4 and is_cjk(tok):
                toks.append(tok)
    return toks

def threshold_opportunity(text):
    kw = ["增伤","减伤","易伤","伤害提升","加成","阈值","提高","下降"]
    if not any(k in text for k in kw):
        return []
    return [s for s in td_skills if s in text]

# ---------- 第一遍：收集每份报告的 slot token + 出现的专名 ----------
files = (glob.glob(os.path.join(BASE, "报告库/旧56项目/逐帧1秒版/*.docx")) +
         glob.glob(os.path.join(BASE, "报告库/开荒/逐帧1秒版/*.docx")))
print("扫描报告数:", len(files))

report_texts = {}
present_names_all = {}      # file -> set of present official names
slot_tokens_all = {}        # file -> list of slot tokens
for f in sorted(files):
    text = extract_text(f)
    report_texts[f] = text
    pres = {nm for nm in all_names if len(nm) >= 2 and nm in text}
    present_names_all[f] = pres
    slot_tokens_all[f] = extract_slots(text)

# 跨报告词频
token_global = Counter()
for toks in slot_tokens_all.values():
    for t in set(toks):
        token_global[t] += 1
name_global = Counter()
for pres in present_names_all.values():
    for nm in pres:
        if 2 <= len(nm) <= 4:
            name_global[nm] += 1

# ---------- 第二遍：判定 ----------
FREQ_CUTOFF = 3   # token 在 >=3 份报告出现 => 真实术语
total_star = total_name = total_thr = 0
reports_out = []
for f in sorted(files):
    text = report_texts[f]
    pres = present_names_all[f]
    sf = star_scan(text)
    # name 判定
    nf = []
    seen = set()
    for tok in slot_tokens_all[f]:
        if tok in seen:
            continue
        seen.add(tok)
        if tok in all_names:
            continue
        if tok in BLACKLIST:
            continue
        if token_global[tok] >= FREQ_CUTOFF:
            continue   # 跨报告常见术语 => 假阳性
        # 找 1 字差异的官方名（且正确名本报告未出现）
        cand = None
        for nm in names_by_len[len(tok)]:
            if hamming1(tok, nm):
                cand = nm
                break
        if cand and cand not in pres:
            conf = "high" if name_global[cand] > token_global[tok] else "mid"
            nf.append({"token": tok, "likely": cand, "conf": conf,
                       "ctx": text.find(tok) if text.find(tok) >= 0 else -1})
    thr = threshold_opportunity(text)
    total_star += len(sf); total_name += len(nf); total_thr += len(thr)
    if sf or nf or thr:
        reports_out.append({"file": os.path.basename(f),
                             "text_len": len(text),
                             "star_flags": sf, "name_flags": nf,
                             "threshold_opportunities": thr})

# ---------- 写出 ----------
md = []
md.append("# 阶段0 缺陷盘点报告 v2（只读，未改动任何文件）\n")
md.append(f"- 扫描报告：{len(files)} 份（北冥56视频的1秒版）")
md.append(f"- 星级疑似错误（已收紧语境）：{total_star} 处")
md.append(f"- 武将/战法名 OCR·音译疑似误识（降噪后）：{total_name} 处")
md.append(f"- 阈值库可注入机会：{total_thr} 处提及（覆盖 {sum(1 for r in reports_out if r['threshold_opportunities'])} 份报告）\n")
md.append("---\n")
for r in reports_out:
    md.append(f"## {r['file']}")
    md.append(f"（字数 {r['text_len']}）\n")
    if r["star_flags"]:
        md.append("**🔴 星级疑似错误（建议逐帧核实）**")
        for x in r["star_flags"]:
            md.append(f"- {x['hero']}：报告写 {x['claimed']}星，官方真实 {x['real']}星 ｜ {x['ctx']}")
    if r["name_flags"]:
        md.append("**🟠 武将/战法名疑似误识（token→应为｜置信）**")
        for x in r["name_flags"]:
            md.append(f"- 「{x['token']}」→ 可能应为「{x['likely']}」 ｜ 置信={x['conf']}")
    if r["threshold_opportunities"]:
        md.append("**🟢 阈值库可注入**（提及且阈值库有数据）：" + "、".join(r["threshold_opportunities"]))
    md.append("")

md_path = os.path.join(LIB, "PHASE0_DEFECT_REPORT_v2.md")
json_path = os.path.join(LIB, "PHASE0_DEFECT_REPORT_v2.json")
open(md_path, "w", encoding="utf-8").write("\n".join(md))
json.dump({"total_reports": len(files), "reports": reports_out},
          open(json_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("写出:", md_path)
print(f"汇总：星级疑似 {total_star} ｜ 名误识疑似 {total_name} ｜ 阈值机会 {total_thr} 处")

# 置信分布
high = sum(1 for r in reports_out for x in r["name_flags"] if x["conf"] == "high")
mid = sum(1 for r in reports_out for x in r["name_flags"] if x["conf"] == "mid")
print(f"名误识置信分布：high={high} ｜ mid={mid}")
defective = [r["file"] for r in reports_out if (r["star_flags"] or r["name_flags"])]
print(f"含星级/名缺陷的报告：{len(defective)} 份")
