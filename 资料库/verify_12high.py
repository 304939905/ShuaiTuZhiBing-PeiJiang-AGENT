# -*- coding: utf-8 -*-
import json, os

BASE = "D:/Desktop/shandou/资料库"
hero = json.load(open(os.path.join(BASE, "hero.json"), encoding="utf-8"))
jext = json.load(open(os.path.join(BASE, "official_jineng_names_ext.json"), encoding="utf-8"))

hero_names = set(h.get("name", "") for h in hero if h.get("name"))
jineng_names = set(jext.get("common", [])) | set(jext.get("innate_from_hero", []))

# (report, src, tgt, kind)  kind: hero / jineng
items = [
    ("开荒专题", "血溅黄沙", "血溅黄砂", "jineng"),
    ("开荒专题", "鬼旅",     "鬼谋",     "jineng"),
    ("开荒专题", "王越",     "王异",     "hero"),
    ("焚决篇",   "制策",     "孙策",     "hero"),
    ("焚决篇",   "至策",     "孙策",     "hero"),
    ("张机篇",   "司马沿",   "司马懿",   "hero"),
    ("徐庶篇",   "急战",     "急救",     "jineng"),
    ("垒实篇",   "回水",     "回马",     "jineng"),
    ("距离思路", "法谋",     "法正",     "hero"),
    ("这战法概率","司马盐",  "司马懿",   "hero"),
    ("这战法概率","折击",     "追击",     "jineng"),
    ("太后篇",   "血溅黄沙", "血溅黄砂", "jineng"),
]

def in_db(tok, kind):
    if kind == "hero":
        return tok in hero_names
    return tok in jineng_names

print(f"{'report':10} | {'src':8} | src_in_db | {'tgt':8} | tgt_in_db | verdict")
print("-"*70)
for rep, src, tgt, kind in items:
    src_in = in_db(src, kind)
    tgt_in = in_db(tgt, kind)
    if (not src_in) and tgt_in:
        verdict = "CONFIRMED 源token非官方实体，目标token官方存在 → 确为误识"
    elif src_in and tgt_in:
        verdict = "BOTH-IN-DB 两者均为官方实体 → 需逐帧核实究竟哪个是视频原字"
    elif (not src_in) and (not tgt_in):
        verdict = "NEITHER 两者都不在白名单 → 白名单缺口或均错，需查网易大神"
    else:
        verdict = "SRC-IN-ONLY 源token在白名单而目标不在 → 疑似误判（目标可能不存在）"
    print(f"{rep:10} | {src:8} | {str(src_in):8} | {tgt:8} | {str(tgt_in):8} | {verdict}")
