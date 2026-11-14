# -*- coding: utf-8 -*-
"""端到端复核 51 份 1秒版逐帧报告：结构 + 转录变体残留 + 事实错配。"""
import os, re, glob, json
from docx import Document

REPORT_DIR = r"D:/Desktop/shandou/学习汇报"
PATTERN = "*逐帧深度学习报告_1秒版.docx"

# 9 章 schema 关键词（用于在标题/正文中定位）
SECTION_KW = {
    "结论摘要": ["结论摘要", "结论与摘要", "结论"],
    "内容范围": ["视频内容范围", "内容范围", "视频范围"],
    "核心知识": ["核心知识详解", "核心知识", "核心机制"],
    "案例分析": ["视频案例分析", "案例分析", "案例"],
    "可执行方法": ["可执行方法", "执行方法", "实操方法"],
    "常见误区": ["常见误区", "误区"],
    "查不到": ["查不到", "无法确认", "待核实"],
    "来源索引": ["来源与证据索引", "来源与证据", "证据索引", "来源索引"],
    "截图": ["截图", "附图", "插图"],
}

# 转录变体残留（若出现说明报告内仍有 whisper 误听未清洗）
VARIANTS = [
    "衡热", "薄浪", "巨熟", "巨黍", "同素", "炉素", "极锋而适", "避其锐气",
    "远宫密策", "远攻密策", "战盘", "魂水", "当洋桥", "油飘", "重谋",
    "星汉继世", "三部上线",
]

def get_text(doc):
    parts = []
    for p in doc.paragraphs:
        if p.text.strip():
            parts.append(p.text)
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                if cell.text.strip():
                    parts.append(cell.text)
    return "\n".join(parts)

def get_headings(doc):
    hs = []
    for p in doc.paragraphs:
        sn = (p.style.name or "") if p.style else ""
        if ("Heading" in sn or "标题" in sn) and p.text.strip():
            hs.append(p.text.strip())
        elif p.runs and p.runs[0].bold and len(p.text.strip()) < 40 and p.text.strip():
            hs.append(p.text.strip())
    return hs

def check_sections(full_text, headings):
    blob = "\n".join(headings) + "\n" + full_text
    present = {}
    for sec, kws in SECTION_KW.items():
        present[sec] = any(kw in blob for kw in kws)
    return present

def scan_variants(text):
    found = {}
    for v in VARIANTS:
        c = text.count(v)
        if c:
            found[v] = c
    # 鼎足/折戟/全军 单独出现（非完整词条）也算可疑
    for short, full in [("鼎足", "鼎足江东"), ("折戟", "折戟强攻"), ("全军", "全军突击")]:
        for m in re.finditer(short, text):
            seg = text[m.start():m.start()+len(full)]
            if seg != full:
                found.setdefault(short+"*", 0)
                found[short+"*"] += 1
    return found

def scan_factual(text):
    flags = []
    # 英勇 应加发动率，不应加攻击属性/武力
    for m in re.finditer("英勇", text):
        s = max(0, m.start()-25); e = min(len(text), m.end()+25)
        ctx = text[s:e]
        if ("攻击属性" in ctx or "武力" in ctx or "攻击力" in ctx) and "发动率" not in ctx:
            flags.append(("英勇-攻击属性错配", ctx.replace("\n"," ")))
            break
    # 筹算 应加发动率(策略)，不应加谋略属性/智力
    for m in re.finditer("筹算", text):
        s = max(0, m.start()-25); e = min(len(text), m.end()+25)
        ctx = text[s:e]
        if ("谋略属性" in ctx or "智力" in ctx) and "发动率" not in ctx:
            flags.append(("筹算-谋略属性错配", ctx.replace("\n"," ")))
            break
    return flags

def main():
    files = sorted(glob.glob(os.path.join(REPORT_DIR, PATTERN)))
    print(f"报告总数: {len(files)}")
    results = []
    struct_problems = []
    variant_hits = {}
    factual_all = []
    total_headings = 0
    for f in files:
        name = os.path.basename(f)
        doc = Document(f)
        text = get_text(doc)
        heads = get_headings(doc)
        total_headings += len(heads)
        sec = check_sections(text, heads)
        missing = [k for k,v in sec.items() if not v]
        variants = scan_variants(text)
        factual = scan_factual(text)
        for k,c in variants.items():
            variant_hits.setdefault(k,0); variant_hits[k]+=c
        for fl in factual:
            factual_all.append((name, fl))
        if missing:
            struct_problems.append((name, missing))
        results.append({
            "name": name, "heading_cnt": len(heads),
            "missing_sections": missing, "variants": variants,
            "factual": [x[0] for x in factual],
        })
    print(f"标题段落总数: {total_headings}")
    print(f"\n=== 结构问题（缺章报告数）: {len(struct_problems)} ===")
    for n, m in struct_problems:
        print(f"  {n}: 缺 {m}")
    print(f"\n=== 转录变体残留（按词汇总，出现文件数/总次数）===")
    # 统计每个变体出现在多少文件
    per_file_variant = {}
    for r in results:
        for k in r["variants"]:
            per_file_variant.setdefault(k, set()); per_file_variant[k].add(r["name"])
    if not variant_hits:
        print("  （无残留变体，全部干净）")
    else:
        for k in sorted(variant_hits, key=lambda x:-variant_hits[x]):
            print(f"  {k}: 总 {variant_hits[k]} 次，涉 {len(per_file_variant.get(k,[]))} 份")
    print(f"\n=== 事实错配标记: {len(factual_all)} 处 ===")
    for n, (kind, ctx) in factual_all:
        print(f"  [{n}] {kind}: …{ctx}…")
    # 输出 JSON 供后续
    out = {"total": len(files), "struct_problems": struct_problems,
           "variant_hits": variant_hits, "factual": factual_all,
           "per_file": results}
    with open(os.path.join(REPORT_DIR, "..", "资料库", "audit_reports_v2.json"), "w", encoding="utf-8") as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)
    print("\n已写出 资料库/audit_reports_v2.json")

if __name__ == "__main__":
    main()
