# -*- coding: utf-8 -*-
import sys, os, re, json, glob
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

ROOT = "D:/Desktop/shandou"
REP = os.path.join(ROOT, "学习汇报")
TERM = os.path.join(ROOT, "资料库", "名词概念.md")
FACTS = os.path.join(ROOT, "资料库", "facts_index.json")

# ---------- 载入 51 份 1秒版 ----------
def load_docs():
    out = []
    for f in sorted(glob.glob(os.path.join(REP, "*_逐帧深度学习报告_1秒版.docx"))):
        try:
            d = Document(f)
            paras = [p.text for p in d.paragraphs]
            out.append((os.path.basename(f), "\n".join(paras)))
        except Exception as e:
            out.append((os.path.basename(f), ""))
    return out

docs = load_docs()
print(f"[载入] 1秒版报告 {len(docs)} 份\n")

# ---------- 1. 残差 OCR / 繁体扫描 ----------
print("=" * 70)
print("一、残差 OCR / 繁体扫描（修复后重新检测）")
print("=" * 70)
# 已知 OCR 可疑 token（修复后应清零，除已标注存疑者）
suspect_tokens = ["勞駮", "游騎", "大桐琴", "機勢", "機热", "萬劍", "戰畢", "魂水", "釋起",
                  "張忌", "石技", "雷石", "合太后", "酒系荒龙", "四水关", "司马盐", "吉峰儿式"]
# 繁体常用字集合（率土报告应全简体）
fan = set("國隊戰萬關寶圖將軍級飛騎遊飄勞駮點體進擊擇張機勢驅駛與從來為這個當時"
          "後無學開隊長發覺見說話語該號變顯現會應會對話讀實實驗組經終處設許話視頻種動圖書頁這個過則總結繼續類際類別區劃協尋幫")
hit_report = {}
for name, txt in docs:
    hits = []
    for tok in suspect_tokens:
        c = txt.count(tok)
        if c:
            hits.append(f"{tok}×{c}")
    # 繁体字符计数
    fan_hits = {}
    for ch in set(txt):
        if ch in fan:
            fan_hits[ch] = txt.count(ch)
    if hits or fan_hits:
        hit_report[name] = (hits, fan_hits)
if not hit_report:
    print("  ✅ 全部 51 份：已知 OCR 可疑 token = 0，繁体字 = 0。")
else:
    for name, (h, fh) in hit_report.items():
        print(f"  ⚠ {name[:30]}")
        if h: print("     可疑token:", ", ".join(h))
        if fh: print("     繁体:", ", ".join(f"{k}×{v}" for k, v in fh.items()))

# ---------- 2. 跨报告一致性（关键实体数值） ----------
print("\n" + "=" * 70)
print("二、跨报告一致性检测（关键实体关联数值）")
print("=" * 70)
entities = ["金匮要略", "神赏", "神兵天降", "大赏三军", "击势", "侵掠如火",
            "汜水关", "乘胜追击", "星汉", "七擒七纵", "游飘", "元戎", "沧海",
            "磐阵善守", "垒实迎击", "神赏体系", "百战", "攻其不备", "反计之策"]
pct = re.compile(r"\d+(?:\.\d+)?\s*%")
for ent in entities:
    snippets = []
    reports_with = set()
    for name, txt in docs:
        for m in re.finditer(re.escape(ent), txt):
            s = max(0, m.start() - 30); e = min(len(txt), m.end() + 50)
            seg = txt[s:e].replace("\n", " ")
            pcs = pct.findall(seg)
            if pcs:
                snippets.append((name, seg.strip(), pcs))
                reports_with.add(name)
    if snippets:
        # 收集不同数值集合
        vals = set()
        for _, _, pcs in snippets:
            for p in pcs:
                vals.add(p)
        flag = " ⚠数值有分歧" if len(vals) > 1 else ""
        print(f"\n  ● {ent}  （出现于 {len(reports_with)} 份，关联数值 {sorted(vals)}{flag}）")
        # 仅在该实体数值有分歧时展开
        if len(vals) > 1:
            for name, seg, pcs in snippets[:8]:
                print(f"     [{name[:18]}] …{seg[:80]}…  ({', '.join(pcs)})")

# ---------- 3. 术语库覆盖缺口 ----------
print("\n" + "=" * 70)
print("三、术语库覆盖缺口（报告中出现但名词概念.md 未收录）")
print("=" * 70)
term_doc = open(TERM, encoding="utf-8").read()
fidx = json.load(open(FACTS, encoding="utf-8"))
by_term = fidx.get("by_term", {})
all_terms = list(by_term.keys())
covered = [t for t in all_terms if t in term_doc]
uncovered = [t for t in all_terms if t not in term_doc]
print(f"  facts_index 聚合术语 {len(all_terms)} 个；名词概念.md 已收录 {len(covered)}；未收录 {len(uncovered)}")
if uncovered:
    print("  未收录术语（来自报告事实句，可能需补条或属误听/变体）：")
    for t in uncovered:
        ex = by_term[t][0][:60] if by_term[t] else ""
        print(f"    - {t}  | 例: {ex}")

# 输出 JSON 供后续
res = {"docs": len(docs), "ocr_hits": {k: v for k, v in hit_report.items()},
       "uncovered_terms": uncovered}
json.dump(res, open(os.path.join(ROOT, "资料库", "deep_review_out.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\n[完成] 结果已写 资料库/deep_review_out.json")
