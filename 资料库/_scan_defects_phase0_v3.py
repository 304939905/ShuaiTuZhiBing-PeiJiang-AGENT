# -*- coding: utf-8 -*-
"""阶段0 v3：在 v2 基础上修复白名单缺口 + 改进"应为名"选择。
修复点：
  1) 武将白名单改用 hero.json 全量（428 名），减少漏召真实武将；
  2) 引入 宝物词条白名单（骁锐/天资/英勇/筹算/勇毅/列阵…），这些真实术语不再误报；
  3) 大营 等阵位术语加入黑名单；
  4) "应为名" 不再取第一个 hamming1 命中，而是取在所有报告中出现频次最高的候选
     （司马X→司马师、王越→王朗、曹彭→曹丕 等更符合实际）。
输出：资料库/PHASE0_DEFECT_REPORT_v3.md + .json
"""
import json, re, os, glob
from docx import Document
from collections import Counter

BASE = r"D:/Desktop/shandou"
LIB = os.path.join(BASE, "资料库")

def jload(p):
    return json.load(open(os.path.join(LIB, p), encoding="utf-8"))

# ---------- 白名单 ----------
heroes = [h for h in jload("hero.json") if "name" in h]
hn = set(h["name"] for h in heroes)                       # 全量武将
heroes_stars = {}
for hero in heroes:
    quality = hero.get("quality", "")
    if str(quality).isdigit():
        heroes_stars.setdefault(hero["name"], set()).add(int(quality))
je = jload("official_jineng_names_ext.json")
skills = set(je.get("common", [])) | set(je.get("innate_from_hero", []))
gears = set(jload("official_gear_names.json")["names"])
all_names = hn | skills | gears
ocr_misreads = jload("ocr_misread_map.json").get("misreads", {})
# 反向索引：误读字串 -> 已有人审/证据链确认的标准词。映射优先于字形猜测。
MISREAD_TO_CANONICAL = {
    variant: canonical
    for canonical, variants in ocr_misreads.items()
    for variant in variants
}

# 宝物词条（真实术语，非武将/战法/宝物名）：不应被判为误识
GEAR_WORDS = {"骁锐", "天资", "英勇", "筹算", "勇毅", "列阵", "果敢",
              "天资", "骁锐", "雄才", "灵动", "敏锐", "坚毅", "骁勇",
              "天禄", "璀璨", "清玄", "破敌", "陷阵", "齐射", "冲阵"}

# 真实武将但 hero.json 未收录（白名单缺口补丁）：命中即视为正确名，不报误识
REAL_NAME_SUPPLEMENT = {"春华"}

# 已由报告正文明确作为“旧音频误识”解释的词，不能再被当作当前报告的
# 名称错误。这里不是白名单改写事实，而是按段落语义排除历史错误引文。
HISTORICAL_CONTEXT_MARKERS = {
    "既有报告", "旧报告", "音频转写", "音频中的", "音频将", "误听",
    "误写", "误作", "误读", "转写为", "转写中", "非「", "非\"",
    "音近猜测",
}

# 游戏黑话、兵种简称、宝物效果或通用配将表达；它们并非武将/战法正式名，
# 不应被“一字相近”规则强行改成数据库中的某个专名。
CONTEXTUALLY_VALID_TERMS = {
    "长弓", "斩龙刀", "护主", "归心", "民望", "降配", "扰后",
}

names_by_len = {2: set(), 3: set(), 4: set()}
for n in all_names:
    if 2 <= len(n) <= 4:
        names_by_len[len(n)].add(n)

td = jload("threshold_db.json")
td_skills = set()
for c in td["categories"]:
    for e in c["entries"]:
        td_skills.add(e["skill"])

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
    "驱逻","破敌","破凰","横行","横勒","大营","三军","全军","中军","减伤",
    "增伤","保护","成功","成立","假设","大补","大火","大幅","山寨","小时",
    "灵动","马镫","武勋","关妹","双减","魏智","攻其","无心","百战","神赏",
    "法刀","鬼吕","自己","大佬","游戏","前锋","攻击","中军","三军","全军",
    "谋略",
    # 常见非专名词（v3 复核剔除）
    "犹豫","禁卫","官媒","募兵","擒贼",
}

CJK = re.compile(r"[一-鿿]")
def is_cjk(s):
    return bool(s) and bool(re.fullmatch(r"[一-鿿]+", s))
STAR_RE = re.compile(r"(五星|四星|三星|二星|一星|[0-9]星|★[0-9]|[0-9]★)")

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
        # 只接受“武将名（X星）”这一明确归属；绝不以相邻文字猜归属。
        # 例如“主城 Lv.4（3/4★），关银屏…”不会再被归到关银屏。
        pat = re.compile(re.escape(name) + r"\s*[（(]\s*" + STAR_RE.pattern)
        for m in pat.finditer(text):
            claimed = parse_star(m.group(1))
            reference_stars = heroes_stars.get(name, set())
            if claimed and reference_stars and claimed not in reference_stars:
                flags.append({"hero": name, "claimed": claimed,
                              "reference_stars": sorted(reference_stars),
                              "ctx": text[max(0, m.start()-10): m.end()+24].strip()})
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
                toks.append((tok, m.start(1)))
    return toks

def is_historical_reference(text, pos):
    """判断命中是否位于“旧转写错误的说明”这一段，而非当前事实陈述。"""
    left = text.rfind("\n", 0, pos) + 1
    right = text.find("\n", pos)
    if right < 0:
        right = len(text)
    ctx = text[left:right]
    return any(marker in ctx for marker in HISTORICAL_CONTEXT_MARKERS)

def threshold_opportunity(text):
    kw = ["增伤","减伤","易伤","伤害提升","加成","阈值","提高","下降"]
    if not any(k in text for k in kw):
        return []
    return [s for s in td_skills if s in text]

# ---------- 第一遍 ----------
files = (glob.glob(os.path.join(BASE, "报告库/旧56项目/逐帧1秒版/*.docx")) +
         glob.glob(os.path.join(BASE, "报告库/开荒/逐帧1秒版/*.docx")))
print("扫描报告数:", len(files))

report_texts = {}
present_names_all = {}
slot_tokens_all = {}
for f in sorted(files):
    text = extract_text(f)
    report_texts[f] = text
    pres = {nm for nm in all_names if len(nm) >= 2 and nm in text}
    present_names_all[f] = pres
    slot_tokens_all[f] = extract_slots(text)

token_global = Counter()
for toks in slot_tokens_all.values():
    for t in {tok for tok, _ in toks}:
        token_global[t] += 1
name_global = Counter()
for pres in present_names_all.values():
    for nm in pres:
        if 2 <= len(nm) <= 4:
            name_global[nm] += 1

# ---------- 第二遍 ----------
FREQ_CUTOFF = 3
total_star = total_name = total_thr = 0
reports_out = []
for f in sorted(files):
    text = report_texts[f]
    pres = present_names_all[f]
    sf = star_scan(text)
    nf = []
    seen = set()
    for tok, pos in slot_tokens_all[f]:
        if tok in seen:
            continue
        seen.add(tok)
        if is_historical_reference(text, pos):
            continue
        if (tok in all_names or tok in GEAR_WORDS or tok in REAL_NAME_SUPPLEMENT
                or tok in CONTEXTUALLY_VALID_TERMS):
            continue
        if tok in BLACKLIST:
            continue
        if token_global[tok] >= FREQ_CUTOFF:
            continue
        # 已有人审映射的误读直接给出可追溯候选；没有映射才使用字形相近提示。
        mapped = MISREAD_TO_CANONICAL.get(tok)
        if mapped:
            cand, basis = mapped, "ocr_map"
        else:
            # 取所有 hamming1 候选中：优先 武将 > 战法 > 宝物，其次"在全报告出现频次最高"
            cands = [nm for nm in names_by_len[len(tok)] if hamming1(tok, nm)]
            if not cands:
                continue
            def cand_key(nm):
                tp = 3 if nm in hn else (2 if nm in skills else (1 if nm in gears else 0))
                return (tp, name_global.get(nm, 0))
            cand, basis = max(cands, key=cand_key), "hamming1"
        if cand and cand not in pres:
            conf = "mapped" if basis == "ocr_map" else ("high" if name_global[cand] > token_global[tok] else "mid")
            nf.append({"token": tok, "likely": cand, "conf": conf, "basis": basis})
    thr = threshold_opportunity(text)
    total_star += len(sf); total_name += len(nf); total_thr += len(thr)
    if sf or nf or thr:
        reports_out.append({"file": os.path.basename(f), "text_len": len(text),
                             "star_flags": sf, "name_flags": nf,
                             "threshold_opportunities": thr})

# ---------- 写出 ----------
md = []
md.append("# 阶段0 缺陷盘点报告 v3（只读，未改动任何文件）\n")
md.append(f"- 扫描报告：{len(files)} 份（北冥56视频的1秒版）")
md.append(f"- 与本地参考库星级不一致（明确武将归属，仍须原帧核验）：{total_star} 处")
md.append(f"- 武将/战法名 OCR·音译疑似误识（降噪后）：{total_name} 处")
md.append(f"- 阈值库可注入机会：{total_thr} 处提及（覆盖 {sum(1 for r in reports_out if r['threshold_opportunities'])} 份报告）\n")
md.append("---\n")
for r in reports_out:
    md.append(f"## {r['file']}")
    md.append(f"（字数 {r['text_len']}）\n")
    if r["star_flags"]:
        md.append("**🔴 明确星级归属但与本地参考库不一致（建议逐帧核实）**")
        for x in r["star_flags"]:
            refs = "、".join(f"{v}星" for v in x['reference_stars'])
            md.append(f"- {x['hero']}：报告写 {x['claimed']}星，本地参考库记录 {refs} ｜ {x['ctx']}")
    if r["name_flags"]:
        md.append("**🟠 武将/战法名疑似误识（token→应为｜置信）**")
        for x in r["name_flags"]:
            md.append(f"- 「{x['token']}」→ 可能应为「{x['likely']}」 ｜ 置信={x['conf']} ｜ 依据={x.get('basis', 'unknown')}")
    if r["threshold_opportunities"]:
        md.append("**🟢 阈值库可注入**（提及且阈值库有数据）：" + "、".join(r["threshold_opportunities"]))
    md.append("")

md_path = os.path.join(LIB, "PHASE0_DEFECT_REPORT_v3.md")
json_path = os.path.join(LIB, "PHASE0_DEFECT_REPORT_v3.json")
open(md_path, "w", encoding="utf-8").write("\n".join(md))
json.dump({"total_reports": len(files), "reports": reports_out},
          open(json_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("写出:", md_path)
print(f"汇总：星级疑似 {total_star} ｜ 名误识疑似 {total_name} ｜ 阈值机会 {total_thr} 处")
high = sum(1 for r in reports_out for x in r["name_flags"] if x["conf"] == "high")
mid = sum(1 for r in reports_out for x in r["name_flags"] if x["conf"] == "mid")
print(f"名误识置信分布：high={high} ｜ mid={mid}")
defective = [r["file"] for r in reports_out if (r["star_flags"] or r["name_flags"])]
print(f"含星级/名缺陷的报告：{len(defective)} 份")
