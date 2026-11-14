# -*- coding: utf-8 -*-
"""阶段0：51份1秒版报告 只读缺陷盘点（不改任何文件）。
输出：资料库/PHASE0_DEFECT_REPORT.md + .json
"""
import json, re, os, glob
from docx import Document

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

# ---------- 工具 ----------
CJK = re.compile(r"[一-鿿]")
def is_cjk(s):
    return bool(s) and bool(re.fullmatch(r"[一-鿿]+", s))
STAR_RE = re.compile(r"(五星|四星|三星|二星|一星|[0-9]星|★[0-9]|[0-9]★)")
CONTEXT_KW = ["武将", "战法", "携带", "自带", "阵容", "队伍", "核心", "搭配", "宝物", "技能", "将领", "体系"]

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
            seg = text[max(0, m.start() - 10): m.end() + 10]
            sm = STAR_RE.search(seg)
            if sm:
                claimed = parse_star(sm.group(0))
                real = heroes_star.get(name)
                if claimed and real and claimed != real:
                    flags.append({"hero": name, "claimed": claimed, "real": real, "ctx": seg.strip()})
                break
    return flags

def hamming1(a, b):
    if len(a) != len(b):
        return False
    return sum(1 for x, y in zip(a, b) if x != y) == 1

def name_scan(text):
    """槽位提取法：只抽取被引号/战法:/武将:/括号框住的名字串，再比对白名单。
    避免对散文整段做模糊编辑距离（噪声巨大）。"""
    present_names = set()
    for nm in all_names:
        if len(nm) >= 2 and nm in text:
            present_names.add(nm)
    # 提取"名字槽"中的候选 token
    slot_patterns = [
        r"[「【“”‘']\s*([一-鿿]{2,4})\s*[」】“”’']",          # 引号框住
        r"(?:战法|武将|携\s*带|自\s*带|名\s*称?)\s*[：: ]\s*([一-鿿]{2,4})",  # X战法/X武将
        r"([一-鿿]{2,4})\s*[（(]",                                  # 名字后接括号
        r"【([一-鿿]{2,4})】",                                      # 书名号框住
    ]
    tokens = []
    for pat in slot_patterns:
        for m in re.finditer(pat, text):
            tok = m.group(1).strip()
            if 2 <= len(tok) <= 4 and is_cjk(tok):
                tokens.append((tok, m.group(0)))
    flags = []
    seen = set()
    for tok, raw in tokens:
        if tok in seen:
            continue
        seen.add(tok)
        if tok in all_names:
            continue  # 正确名，跳过
        # 找 1 字差异的官方名，且官方名在本报告未出现（即"写错名、正确名反不在"）
        cand = None
        for nm in names_by_len[len(tok)]:
            if hamming1(tok, nm):
                cand = nm
                break
        if cand and cand not in present_names:
            flags.append({"token": tok, "likely": cand, "ctx": raw.strip()})
    return flags[:30]

def threshold_opportunity(text):
    kw = ["增伤", "减伤", "易伤", "伤害提升", "加成", "阈值", "提高", "下降"]
    if not any(k in text for k in kw):
        return []
    mentioned = [s for s in td_skills if s in text]
    return mentioned

# ---------- 主循环 ----------
files = (glob.glob(os.path.join(BASE, "报告库/旧56项目/逐帧1秒版/*.docx")) +
         glob.glob(os.path.join(BASE, "报告库/开荒/逐帧1秒版/*.docx")))
print("扫描报告数:", len(files))

report = {"generated_by": "PHASE0 read-only defect scan",
          "total_reports": len(files),
          "reports": []}
total_star = total_name = total_thr = 0
for f in sorted(files):
    text = extract_text(f)
    sf = star_scan(text)
    nf = name_scan(text)
    thr = threshold_opportunity(text)
    total_star += len(sf); total_name += len(nf); total_thr += len(thr)
    report["reports"].append({
        "file": os.path.basename(f),
        "text_len": len(text),
        "star_flags": sf,
        "name_flags": nf,
        "threshold_opportunities": thr,
    })

# ---------- 写出 ----------
md = []
md.append("# 阶段0 缺陷盘点报告（只读，未改动任何文件）\n")
md.append(f"- 扫描报告：{len(files)} 份（北冥56视频的1秒版）")
md.append(f"- 星级疑似错误：{total_star} 处")
md.append(f"- 武将/战法名 OCR·音译疑似误识：{total_name} 处")
md.append(f"- 阈值库可注入机会：{total_thr} 份报告提及阈值库战法\n")
md.append("---\n")

for r in report["reports"]:
    if not (r["star_flags"] or r["name_flags"] or r["threshold_opportunities"]):
        continue
    md.append(f"## {r['file']}")
    md.append(f"（字数 {r['text_len']}）\n")
    if r["star_flags"]:
        md.append("**🔴 星级疑似错误**")
        for x in r["star_flags"]:
            md.append(f"- {x['hero']}：报告写 {x['claimed']}星，官方真实 {x['real']}星 ｜ {x['ctx']}")
    if r["name_flags"]:
        md.append("**🟠 武将/战法名疑似误识（token→应为）**")
        for x in r["name_flags"][:30]:
            md.append(f"- 「{x['token']}」→ 可能应为「{x['likely']}」 ｜ …{x['ctx']}…")
        if len(r["name_flags"]) > 30:
            md.append(f"- …（共 {len(r['name_flags'])} 处，已截断显示前30）")
    if r["threshold_opportunities"]:
        md.append("**🟢 阈值库可注入**（提及且阈值库有数据）：" + "、".join(r["threshold_opportunities"]))
    md.append("")

md_path = os.path.join(LIB, "PHASE0_DEFECT_REPORT.md")
json_path = os.path.join(LIB, "PHASE0_DEFECT_REPORT.json")
open(md_path, "w", encoding="utf-8").write("\n".join(md))
json.dump(report, open(json_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("写出:", md_path)
print(f"汇总：星级疑似 {total_star} ｜ 名误识疑似 {total_name} ｜ 阈值机会 {total_thr} 份")
# 打印有缺陷的报告清单
defective = [r["file"] for r in report["reports"] if (r["star_flags"] or r["name_flags"])]
print(f"含星级/名缺陷的报告：{len(defective)} 份")
