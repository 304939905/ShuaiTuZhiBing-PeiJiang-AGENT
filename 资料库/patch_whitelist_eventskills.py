# -*- coding: utf-8 -*-
"""补录事件/赛季战法到扩展白名单（官方接口未覆盖）。
   扫描脚本 scan_herojineng.py 读取的是 names 键（= common ∪ innate_from_hero 的并集），
   因此必须把新名同时写进 common 并重新并集生成 names，否则扫描不会生效。"""
import sys, json
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")

P = "D:/Desktop/shandou/资料库/official_jineng_names_ext.json"
add = ["当阳桥", "乌云山兵"]  # 事件/赛季战法，官方 jineng_list / hero_extra 均未覆盖
d = json.load(open(P, encoding="utf-8"))

common = d.get("common", [])
innate = d.get("innate_from_hero", [])
added = [n for n in add if n not in common and n not in innate]
for n in add:
    if n not in common:
        common.append(n)

names = sorted(set(common) | set(innate))
d["common"] = sorted(common)
d["innate_from_hero"] = sorted(innate)
d["names"] = names
d["count"] = len(names)
json.dump(d, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("新增到 common/innate:", added)
print("common:", len(d["common"]), "| innate_from_hero:", len(d["innate_from_hero"]),
      "| names(并集):", len(d["names"]), "| count:", d["count"])
print("names 含当阳桥:", "当阳桥" in d["names"], "| 乌云山兵:", "乌云山兵" in d["names"])
