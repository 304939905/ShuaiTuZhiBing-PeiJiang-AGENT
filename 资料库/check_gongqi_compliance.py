# -*- coding: utf-8 -*-
"""攻其篇精编报告 合规自检 v3：覆盖 REPORT_CONVENTIONS.md 6 大硬规则 + 已知3处错误残留。
位置词检测用官方武将名单精确匹配"位置+武将名"（排除合规固定写法/机制讲解）。"""
import os, re, json
from docx import Document

P = 'D:/Desktop/攻其篇精编报告_最终修正v2_2026-08-19.docx'
d = Document(P)
para_texts = [p.text for p in d.paragraphs]
table_texts = []
for ti, tb in enumerate(d.tables):
    for ri, row in enumerate(tb.rows):
        for ci, c in enumerate(row.cells):
            table_texts.append((ti, ri, ci, c.text))
full_para = "\n".join(para_texts)
full_table = "\n".join(t[3] for t in table_texts)
full_all = full_para + "\n" + full_table

print("="*60); print("攻其篇报告合规自检 v3"); print("="*60)
issues = []

# 规0 四大硬标准
print("\n[规0] 四大硬标准")
has_index_kw = "关键词" in full_all
has_index_hero = "核心武将" in full_all
has_date = bool(re.search(r"报告生成日期[：:]\s*\d{4}-\d{2}-\d{2}", full_all))
has_path = "报告路径" in full_all
print(f"  索引块 关键词:{has_index_kw} 核心武将:{has_index_hero} 生成日期:{has_date} 报告路径:{has_path}")
if not (has_index_kw and has_index_hero and has_date and has_path):
    issues.append("索引块四大要素缺失")
ver_re = re.compile(r"(吴|蜀|群|魏|汉|晋)-(步|弓|骑)-[1-5]星(?:\((?:SP|XP)\))?")
bad_ver_re = re.compile(r"(吴|蜀|群|魏|汉)-(.{1,6})-(步|弓|骑)-[1-5]星")
print(f"  版本标签(正确格式)命中:{len(ver_re.findall(full_all))}  名字内嵌:{len(bad_ver_re.findall(full_all))}")
if bad_ver_re.findall(full_all):
    issues.append("版本标签名字内嵌")
warn_re = re.compile(r"(可能已过时|以官方更新为准|请结合时间戳|是否过期)")
print(f"  时效警告语:{bool(warn_re.search(full_all))}")
if warn_re.search(full_all):
    issues.append("含时效性警告语")
ai_ch = ("AI 智能体主动推断" in full_all) or ("AI主动推断" in full_all) or ("AI 推断" in full_all)
print(f"  AI推断独立章节:{ai_ch}")
if not ai_ch:
    issues.append("缺AI推断独立章节")

# 规2 位置词+官方武将名（精确匹配）
print("\n[规2] 位置词并入武将名检测")
hero_names = sorted(json.load(open('official_hero_names.json',encoding='utf-8'))['names'], key=len, reverse=True)
pos_pat = re.compile(r"(中军|大营|前排|前锋)")
slot_tag = re.findall(r"【(大营|中军|前锋|前排)】", full_all)
print(f"  槽位标签【】旧写法命中:{slot_tag}")
real_bad = []
for m in pos_pat.finditer(full_all):
    after = full_all[m.end():m.end()+5]
    before = full_all[max(0,m.start()-4):m.start()]
    if "位置的" in before or "位置" in before[-3:] or after.startswith("的位置") or after.startswith("的"):
        continue
    matched = next((hn for hn in hero_names if after.startswith(hn)), None)
    if matched:
        real_bad.append(m.group(1)+matched)
print(f"  位置词+武将名 真实违规:{real_bad}")
if real_bad:
    issues.append(f"位置词并入武将名:{real_bad[:5]}")

# 已知3处错误残留（排除旧误推示例引用语境）
print("\n[已知错误] 3处修复残留扫描")
known = {
    "钜黍（吕布）": "吕布distance=4不需钜黍",
    "中军位的兀突骨": "兀突骨位置非强制",
    "兀突骨为中线将": "兀突骨位置非强制",
    "木鹿大王.*衡轭": "木鹿第三战法=夔吼象路非衡轭",
    "低COST": "误推残留",
    "低 COST": "误推残留",
}
residual = []
for k, desc in known.items():
    for m in re.finditer(k, full_all):
        ctx = full_all[max(0,m.start()-20):m.start()+20]
        if any(x in ctx for x in ["此前报告写成","双重错误","属盲推","已改为","已纠正","旧误推","示例"]):
            print(f"  (豁免引用) {k} -> ...{ctx}...")
            continue
        residual.append((k, desc, ctx))
ca = re.search(r"凑不齐曹操", full_all)
if ca:
    ctx = full_all[max(0,ca.start()-20):ca.start()+20]
    if "此前报告写成" in ctx or "双重错误" in ctx or "旧误推" in ctx:
        print(f"  (豁免引用) 凑不齐曹操 -> ...{ctx}...")
    else:
        residual.append(("凑不齐曹操","曹操未出场误推",ctx))
if residual:
    print("  ⚠ 发现残留:")
    for k, desc, ctx in residual:
        print(f"    - {k} ({desc}) ...{ctx}...")
    issues.append(f"已知错误残留:{[k for k,_,_ in residual]}")
else:
    print("  ✅ 无已知3处错误真实残留（旧误推示例引用已豁免）")

# 表格单元格专项
print("\n[表格] 单元格残留扫描")
table_issue = []
for (ti, ri, ci, txt) in table_texts:
    for k in known:
        if re.search(k, txt):
            table_issue.append((ti, ri, ci, k))
if table_issue:
    print("  ⚠ 表格单元格残留:", table_issue)
    issues.append(f"表格单元格残留:{[t[3] for t in table_issue]}")
else:
    print("  ✅ 表格单元格无已知错误残留")

print("\n"+"="*60)
if not issues:
    print("✅ 合规自检通过：6大硬规则 + 已知3处错误均无真实残留")
else:
    print(f"❌ 发现 {len(issues)} 类问题:")
    for i in issues:
        print(f"  - {i}")
