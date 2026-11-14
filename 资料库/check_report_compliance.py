# -*- coding: utf-8 -*-
"""通用报告合规自检：覆盖 REPORT_CONVENTIONS.md 6 大硬规则 + 位置词(官方武将名单精确匹配)。
用法：python check_report_compliance.py <报告docx路径> [已知错误词表json(可选)]
返回 0=通过，非0=发现问题数。可复用于旧56重做后逐份自检。"""
import sys, os, re, json
from docx import Document

DEF_HERO = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'official_hero_names.json')

def main():
    if len(sys.argv) < 2:
        print("用法: python check_report_compliance.py <报告.docx> [错误词表json]")
        return 2
    P = sys.argv[1]
    if not os.path.exists(P):
        print("文件不存在:", P); return 2
    known = {}
    if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
        known = json.load(open(sys.argv[2], encoding='utf-8'))

    d = Document(P)
    para = [p.text for p in d.paragraphs]
    table_texts = []
    for ti, tb in enumerate(d.tables):
        for ri, row in enumerate(tb.rows):
            for ci, c in enumerate(row.cells):
                table_texts.append((ti, ri, ci, c.text))
    full = "\n".join(para) + "\n" + "\n".join(t[3] for t in table_texts)
    issues = []

    # 规0 四大硬标准
    has_kw = "关键词" in full
    has_hero = "核心武将" in full
    has_date = bool(re.search(r"报告生成日期[：:]\s*\d{4}-\d{2}-\d{2}", full))
    has_path = "报告路径" in full
    if not (has_kw and has_hero and has_date and has_path):
        issues.append("索引块四要素缺失")
    ver_re = re.compile(r"(吴|蜀|群|魏|汉|晋)-(步|弓|骑)-[1-5]星(?:\((?:SP|XP)\))?")
    bad_ver = re.compile(r"(吴|蜀|群|魏|汉)-(.{1,6})-(步|弓|骑)-[1-5]星")
    if bad_ver.findall(full):
        issues.append("版本标签名字内嵌")
    warn = re.compile(r"(可能已过时|以官方更新为准|请结合时间戳|是否过期)")
    if warn.search(full):
        issues.append("含时效性警告语")
    ai_ch = ("AI 智能体主动推断" in full) or ("AI主动推断" in full) or ("AI 推断" in full)
    if not ai_ch:
        issues.append("缺AI推断独立章节")

    # 规2 位置词+武将名（官方名单精确匹配）
    hero_names = sorted(json.load(open(DEF_HERO, encoding='utf-8'))['names'], key=len, reverse=True)
    pos_pat = re.compile(r"(中军|大营|前排|前锋)")
    real_bad = []
    for m in pos_pat.finditer(full):
        after = full[m.end():m.end()+5]
        before = full[max(0, m.start()-4):m.start()]
        if "位置的" in before or "位置" in before[-3:] or after.startswith("的位置") or after.startswith("的"):
            continue
        matched = next((hn for hn in hero_names if after.startswith(hn)), None)
        if matched:
            real_bad.append(m.group(1)+matched)
    if real_bad:
        issues.append(f"位置词并入武将名:{real_bad[:5]}")

    # 已知错误词表残留（可选）
    if known:
        resid = []
        for k, desc in known.items():
            if re.search(k, full):
                resid.append(k)
        if resid:
            issues.append(f"已知错误残留:{resid}")

    # 表格单元格扫描（通用：查已知错误词）
    if known:
        tbad = []
        for (ti, ri, ci, txt) in table_texts:
            for k in known:
                if re.search(k, txt):
                    tbad.append(k)
        if tbad:
            issues.append(f"表格单元格残留:{tbad}")

    print(f"报告: {os.path.basename(P)}")
    print(f"  段落={len(para)} 表格={len(d.tables)} 单元格={len(table_texts)}")
    print(f"  版本标签(正确格式)命中:{len(ver_re.findall(full))} 名字内嵌:{len(bad_ver.findall(full))}")
    print(f"  索引块(kw/hero/date/path):{has_kw}/{has_hero}/{has_date}/{has_path} AI推断章:{ai_ch}")
    print(f"  位置词真实违规:{real_bad}")
    if not issues:
        print("✅ 合规通过")
        return 0
    else:
        print(f"❌ 发现问题({len(issues)}):")
        for i in issues:
            print("  -", i)
        return len(issues)

if __name__ == "__main__":
    sys.exit(main())
