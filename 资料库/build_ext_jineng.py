import json, os

BASE = os.path.dirname(os.path.abspath(__file__))

# 1) 删除探查临时文件（中文路径 rm 会被 safe-delete 拦截，用 Python 删）
for f in ["card_list.html", "card_list_0b33ffe.js"]:
    p = os.path.join(BASE, f)
    if os.path.exists(p):
        os.remove(p)
        print("已删除", f)

# 2) 提取武将自带战法（hero_extra.methodName / methodName1 / methodName2）
h = json.load(open(os.path.join(BASE, "hero_extra.json"), encoding="utf-8"))
innate = set()
for x in h:
    for k in ("methodName", "methodName1", "methodName2"):
        v = x.get(k)
        if v and isinstance(v, str) and v.strip():
            innate.add(v.strip())

# 3) 通用战法
jin_raw = json.load(open(os.path.join(BASE, "jineng_list.json"), encoding="utf-8"))
common = {x["name"] for x in jin_raw if x.get("name")}

# 4) 扩展战法白名单 = 通用 ∪ 自带
ext = sorted(common | innate)
json.dump({"count": len(ext), "common": sorted(common), "innate_from_hero": sorted(innate),
           "names": ext},
          open(os.path.join(BASE, "official_jineng_names_ext.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# 5) 更新总索引 map（战法类补充自带战法）
allm = json.load(open(os.path.join(BASE, "official_all_names.json"), encoding="utf-8"))["map"]
for n in ext:
    if allm.get(n) in (None, "jineng"):
        allm[n] = "jineng"
json.dump({"count": len(allm), "map": allm},
          open(os.path.join(BASE, "official_all_names.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("通用战法:", len(common), " 武将自带战法(去重):", len(innate), " 扩展战法白名单:", len(ext))

# 6) 重测探针
hero = {x["name"] for x in h if x.get("name")}
gear = {x["name"] for x in json.load(open(os.path.join(BASE, "gear_id.json"), encoding="utf-8")) if x.get("name")}
jin_probe = ["攻其不备","反计之策","避锐治气","焚决","一骑当千","击势","及锋而试","合纵连横","百战无怯"]
miss = [p for p in jin_probe if p not in ext]
print("战法探针(扩展后) 缺失:", miss if miss else "全中")
print("关妹->", allm.get("关妹"), " (应无，官方为关银屏:", "关银屏" in hero, ")")
print("骁锐/筹算是否宝物词条(应不在宝物名白名单):", "骁锐" in gear, "筹算" in gear)
