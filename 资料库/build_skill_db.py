# -*- coding: utf-8 -*-
"""把官方 skill_extra.json(642 战法含数值) + hero_extra(自带战法/政策) + gear_id(宝物)
   归一为一个数值核对金标准库 official_skill_db.json"""
import json, re, html, os

BASE = os.path.dirname(os.path.abspath(__file__))


def L(p):
    return json.load(open(os.path.join(BASE, p), encoding="utf-8"))


def clean(s):
    if s is None:
        return ""
    s = html.unescape(str(s))
    return re.sub(r"<[^>]+>", "", s).strip()


se = L("skill_extra.json")
sk = L("skill.json")
he = L("hero_extra.json")
ge = L("gear_id.json")

# AA 补充库保留战法的原始赛季编码。快速战法库只按规范战法 ID
# 精确关联赛季门禁字段，不复制完整效果明细和获取链。
aa_path = os.path.join(BASE, "aa_rate_supplement.json")
aa_skills = {}
if os.path.exists(aa_path):
    aa_skills = L("aa_rate_supplement.json").get("skills", {})

SEASON_TAGS = {
    0: "BASE",
    2: "S2",
    3: "S3",
    4: "XP",
    40003: "XP",
}

# XP 是战法标签，不是开放赛季。这里只固化已有本地文字或用户确认的
# 赛季结论；其余 XP 战法保留空值，后续按获取方式逐类核定。
ACQUISITION_STAGE_OVERRIDES = {
    "形兵之极": ("S3", "名词概念.md：S3赛季典藏战法"),
    "磐阵善守": ("S3", "用户确认：S3可以兑换（2026-09-14）"),
    "衡轭": ("征服赛季", "用户提供官方卡包截图：辛宪英、吾粲、于禁均来自征服赛季卡包（2026-09-14）"),
}

db = {}
for e in se:
    n = clean(e.get("name"))
    if not n:
        continue
    db[n] = {
        "id": e.get("id"),
        "probability": clean(e.get("probability")),
        "quality": clean(e.get("zfQuality")),
        "type": clean(e.get("type")),
        "soldier": clean(e.get("soldierType")),
        "target": clean(e.get("targetType")),
        "distance": e.get("distance"),
        "effect": clean(e.get("effect")),
        "desc": clean(e.get("desc")),
        "desc1": clean(e.get("desc(level1)")),
        "src": "skill_extra",
    }

# skill.json 补品质（含未在 skill_extra 的）
qmap = {}
for e in sk:
    n = clean(e.get("name"))
    if n:
        qmap[n] = clean(e.get("skill_quality_level"))
        if n not in db:
            db[n] = {"id": e.get("skill_id"), "probability": "", "quality": clean(e.get("skill_quality_level")),
                     "type": "", "soldier": "", "target": "", "distance": None, "effect": "",
                     "desc": "", "desc1": "", "src": "skill"}

# hero_extra 自带战法描述（补 skill_extra 未覆盖的）
hero_innate = {}
for e in he:
    hn = clean(e.get("name"))
    for nf, df in (("methodName", "methodDesc"), ("methodName1", "methodDesc1"), ("methodName2", "methodDesc2")):
        n, d = clean(e.get(nf)), clean(e.get(df))
        if not n:
            continue
        hero_innate.setdefault(n, {"heroes": [], "desc": d})
        hero_innate[n]["heroes"].append(hn)
        if d and not hero_innate[n]["desc"]:
            hero_innate[n]["desc"] = d
        if n not in db:
            db[n] = {"id": None, "probability": "", "quality": "", "type": "", "soldier": "",
                     "target": "", "distance": None, "effect": "", "desc": d, "desc1": "",
                     "src": "hero_innate"}
        elif not db[n]["desc"]:
            db[n]["desc"] = d

# 战法标签与已确认获取阶段。禁止只按名称合并：原始库中的同名多 ID
# 记录可能带不同内部 season 值，规范 ID 才是稳定关联键。
study_by_id = {
    str(item.get("id")): clean(item.get("studyDesc"))
    for item in se
    if item.get("id") is not None
}
for name, entry in db.items():
    skill_id = entry.get("id")
    aa_entry = aa_skills.get(str(skill_id)) if skill_id is not None else None
    season_code = aa_entry.get("season") if aa_entry else None
    entry["season_code"] = season_code
    entry["season_tag"] = SEASON_TAGS.get(season_code, "UNKNOWN")

    study_desc = study_by_id.get(str(skill_id), "")
    obtain_method = ""
    if "市井" in study_desc:
        obtain_method = "市井购买"
    elif "拆解武将" in study_desc:
        obtain_method = "拆解指定武将"
    elif "兑换获得" in study_desc:
        obtain_method = "兑换"
    if obtain_method:
        entry["obtain_method"] = obtain_method

    acquisition_stage = ""
    acquisition_source = ""
    acquisition_status = ""
    if season_code == 2:
        acquisition_stage = "S2"
        acquisition_source = "aa_rate_supplement.json：S2标签"
        acquisition_status = "confirmed"
    elif season_code == 3:
        acquisition_stage = "S3"
        acquisition_source = "aa_rate_supplement.json：S3标签"
        acquisition_status = "confirmed"
    elif "征服赛季" in study_desc:
        acquisition_stage = "征服赛季"
        acquisition_source = "skill_extra.json：获取说明"
        acquisition_status = "confirmed"
    elif name in ACQUISITION_STAGE_OVERRIDES:
        acquisition_stage, acquisition_source = ACQUISITION_STAGE_OVERRIDES[name]
        acquisition_status = "confirmed"
    elif entry["season_tag"] == "XP" and obtain_method == "拆解指定武将":
        acquisition_stage = "征服赛季"
        acquisition_source = "用户暂定规则：未核实的XP战法拆解武将默认按征服赛季卡处理（2026-09-14）"
        acquisition_status = "provisional_default"
    elif entry["season_tag"] == "XP" and obtain_method == "兑换":
        acquisition_stage = "征服赛季"
        acquisition_source = "用户暂定规则：开放赛季未核实的XP兑换战法默认按征服赛季处理（2026-09-14）"
        acquisition_status = "provisional_default"
    if acquisition_stage:
        entry["acquisition_stage"] = acquisition_stage
        entry["acquisition_stage_source"] = acquisition_source
        entry["acquisition_stage_status"] = acquisition_status

# 政策
policy = {}
for e in he:
    n, d = clean(e.get("policyName")), clean(e.get("policyDesc"))
    if n:
        policy[n] = d

# 宝物
gear = {}
for e in ge:
    n = clean(e.get("name"))
    if n:
        gear[n] = {
            "quality": clean(e.get("quality")),
            "type": clean(e.get("type")),
            "skillName": clean(e.get("skillName")),
            "skillDesc": clean(e.get("skillDesc")),
            "policyName": clean(e.get("policyName")),
            "policyDesc": clean(e.get("policyDesc")),
        }

out = {"skills": db, "policy": policy, "gear": gear,
       "counts": {"skills": len(db), "policy": len(policy), "gear": len(gear),
                  "with_prob": sum(1 for v in db.values() if v["probability"] not in ("", "--")),
                  "with_desc": sum(1 for v in db.values() if v["desc"])}}
json.dump(out, open(os.path.join(BASE, "official_skill_db.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("official_skill_db.json ->", out["counts"])

# 白名单增量
full = set(L("official_jineng_names_full.json")["names"])
new = sorted(set(db) - full)
print("\n新增战法名 %d 个（不在 960 白名单）:" % len(new))
print("  " + " ".join(new[:60]))
merged = sorted(full | set(db))
json.dump({"count": len(merged), "names": merged},
          open(os.path.join(BASE, "official_jineng_names_full.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n白名单 %d -> %d" % (len(full), len(merged)))
