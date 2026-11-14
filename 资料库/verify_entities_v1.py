# -*- coding: utf-8 -*-
"""第1视频实体白名单核验: 五队并三队"""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

LIB = r"D:/Desktop/shandou/资料库"
wl = json.load(open(LIB + "/official_merged_whitelist.json", encoding="utf-8"))
hero_extra = json.load(open(LIB + "/hero_extra.json", encoding="utf-8"))
gears_db = json.load(open(LIB + "/gear_id.json", encoding="utf-8"))

def in_wl(name):
    return (name in wl.get("heroes", []) or name in wl.get("skills", [])
            or name in wl.get("gears", []) or name in wl.get("heros", []))

heroes = ["甘宁","司马炎","孙权","王异","卫瓘","张辽","荀彧","贾诩","郭嘉",
          "李儒","木鹿大王","姜维","何太后","陆抗","司马懿","黄盖","王璨"]
skills = ["侵掠如火","及锋而试","汜水关","谋议宏图","三军之众","计险远近","九锡黄龙","始计",
          "浑水摸鱼","世仇","众谋不懈","并进","持节镇西","神兵天降","大赏三军","其疾如风",
          "反计之策","悬权而动","驱虎吞狼","焰焚箕轸","深谋远虑","谋谟帷幄","磐阵善守",
          "河内世泽","奇佐鬼谋","久战熟谋","战必断金","文伐","一夫当关","计谲废立",
          "篝火延焚","夔吼象踏","知己知彼","妖术","列营守险","形兵之极","反击","空城",
          "兵无常势","避其锋谋","避其锋芒","筹算","平蛮","威敌","利刃","列阵","地利",
          "齐射","疾行","出奇","守备","勇毅","迂回","破敌","散射"]
gear_names = ["大柯斧","连弩","元戎","大都督","大柯茶"]

print("== 白名单键:", list(wl.keys()))
print("\n== 武将 ==")
for h in heroes:
    print(f"  {h}: 白名单={in_wl(h)}")
print("\n== 战法 ==")
for s in skills:
    print(f"  {s}: 白名单={in_wl(s)}")
print("\n== 宝物 ==")
for g in gear_names:
    print(f"  {g}: 白名单={in_wl(g)}")

print("\n== hero_extra methodName（自带战法）==")
# hero_extra 结构探测
if isinstance(hero_extra, list):
    items = hero_extra
else:
    items = hero_extra.get("list") or hero_extra.get("data") or list(hero_extra.values())
print("hero_extra 类型:", type(hero_extra).__name__, "条目数:", len(items) if hasattr(items,'__len__') else '?')
sample = items[0] if isinstance(items, list) else None
if sample: print("首条字段:", list(sample.keys())[:15] if isinstance(sample, dict) else sample)

def find_hero(name):
    out = []
    for it in (items if isinstance(items, list) else []):
        if isinstance(it, dict) and (it.get("name") == name or it.get("heroName") == name):
            out.append(it)
    return out

for h in ["木鹿大王","姜维","李儒","卫瓘","甘宁","司马炎","孙权","王异","张辽","荀彧","贾诩","郭嘉","何太后","陆抗"]:
    hits = find_hero(h)
    if hits:
        for it in hits:
            print(f"  {h}: methodName={it.get('methodName')} camp={it.get('camp') or it.get('country')} star={it.get('star') or it.get('quality')}")
    else:
        print(f"  {h}: [hero_extra 未命中]")

print("\n== gear_id 宝物模糊匹配 ==")
if isinstance(gears_db, list):
    gitems = gears_db
else:
    gitems = gears_db.get("list") or gears_db.get("data") or []
for g in gear_names:
    hits = [it for it in gitems if isinstance(it, dict) and g in str(it.get("name", ""))]
    print(f"  {g}: {len(hits)} 命中 -> {[it.get('name') for it in hits][:3]}")
