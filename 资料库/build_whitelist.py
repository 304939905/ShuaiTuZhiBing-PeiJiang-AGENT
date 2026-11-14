# -*- coding: utf-8 -*-
"""合并战法白名单：扩展战法(650) ∪ 内政政策(307) ∪ 确认真实战法(典藏/缺失)。
产出 official_jineng_names_full.json，供 qc_gate.py / scan_assert.py 加载。
确认来源：
  内政政策 policyName —— 从 hero_extra.json 提取（official_policy_names.json, 307 条）
  单骑救主 —— 赵云兑换典藏战法，网易大神多源确认
  知己知彼 —— A 级指挥战法，stzb.163.com/jinenglist/200249 官方页确认
  正始之变 —— S 级典藏战法，网易大神确认
  七擒七纵 —— 南中之战赛季机制/典故，非战法，故意不入白名单
用法: python build_whitelist.py
"""
import json, os

BASE = "D:/Desktop/shandou/资料库"
ext = set(json.load(open(BASE + "/official_jineng_names_ext.json", encoding="utf-8"))["names"])
pol = set(json.load(open(BASE + "/official_policy_names.json", encoding="utf-8"))["names"])

# 经核验确为真实战法、但扩展白名单(650)缺失者
CONFIRMED = ["单骑救主", "知己知彼", "正始之变"]

missing_from_ext = [c for c in CONFIRMED if c not in ext]
print("并入确认真实战法(原不在650):", missing_from_ext)

full = ext | pol | set(CONFIRMED)
data = {
    "count": len(full),
    "note": "= official_jineng_names_ext(650) ∪ 内政政策policyName(307) ∪ 确认真实战法[单骑救主,知己知彼,正始之变]",
    "names": sorted(full),
}
out = BASE + "/official_jineng_names_full.json"
json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("写出", out, "总条数", len(full), "(ext %d + policy %d + confirmed %d)" % (len(ext), len(pol), len(CONFIRMED)))
# 自检：确认几个关键名都在
for k in ["河内世泽", "磐阵善守", "将出关西", "久战熟谋", "以诱待来", "胜兵求战", "单骑救主", "知己知彼", "正始之变", "审时度势", "文德皇后", "太平要术"]:
    print(("  OK " if k in full else "  !!MISS"), k)
