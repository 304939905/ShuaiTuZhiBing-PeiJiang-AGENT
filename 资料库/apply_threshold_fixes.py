"""Apply C2/C3/C4 cross-validation fixes to threshold_db.json (2026-08-20).
- C2 徽言龙凤 增伤增长率 待数据 → 无数据
- C3 奉令护蜀 减伤 main_attr 攻击 → 防御（官方权威）
- C4 遗志 标记 data_status=invalid_placeholder + 官方机制描述
"""
import json
from pathlib import Path
DB = Path("D:/Desktop/shandou/资料库")
tdb = json.load(open(DB/"threshold_db.json", encoding="utf-8"))

changes = []
# C2: 徽言龙凤 增伤 → 增长率 改"无数据"
for c in tdb["categories"]:
    if c["name"] != "增伤类战法": continue
    for e in c["entries"]:
        if e.get("skill") == "徽言龙凤" and e.get("effect") == "我方增伤":
            if e.get("growth") == "待数据":
                e["growth"] = "无数据"
                e["growth_note"] = "官方描述仅说「受谋略属性影响」未给具体数值；2026-08-20 用户授权，按指示标'无数据'"
                changes.append(f"C2 徽言龙凤/增伤: growth 待数据 → 无数据")

# C3: 奉令护蜀 减伤 → main_attr 攻击 → 防御
for c in tdb["categories"]:
    if c["name"] != "减伤类战法": continue
    for e in c["entries"]:
        if e.get("skill") == "奉令护蜀" and e.get("effect") == "我方减伤":
            if e.get("main_attr") == "攻击":
                old = e["main_attr"]
                e["main_attr"] = "防御"
                e["main_attr_note"] = "官方描述为'受到的所有伤害降低20.0%（受防御属性影响）'，2026-08-20 与 hero_extra 200865 交叉验证修正。原'攻击'为阈值表录入错误"
                changes.append(f"C3 奉令护蜀/减伤: main_attr {old} → 防御")

# C4: 遗志 → 标注 data_status + 官方机制
for c in tdb["categories"]:
    if c["name"] != "恢复类战法": continue
    for e in c["entries"]:
        if e.get("skill") == "遗志":
            e["data_status"] = "invalid_placeholder"
            e["data_status_note"] = "image_2 原始 9999%/null/null 为占位符，2026-08-20 用户确认数据源错误，按指示不录入"
            e["official_mechanism"] = {
                "trigger": "战斗开始后第 3 回合（固定回合触发）",
                "effect_A": "使我军前锋（步兵或弓兵）恢复极大量兵力",
                "effect_B": "此后受到普通攻击可反击（伤害率 85%）",
                "limit": "同时无法恢复兵力，持续直到战斗结束",
                "source": "hero_extra.json 孙坚 id=100033 methodId=200033 + jineng_list.json 200033"
            }
            e["formula_excluded"] = True
            changes.append("C4 遗志: 标 invalid_placeholder + 录入官方回合触发机制")

# 更新 cross_source_conflicts 状态
for x in tdb["cross_source_conflicts"]:
    if x.get("id") == "C2":
        x["status"] = "resolved"
        x["resolution"] = "2026-08-20 用户授权 + 本地官方战法库(hero_extra 司马徽 200294)交叉验证：多效战法确认(士气+增伤+概率攻击三效并存)；增伤增长率改为'无数据'(官方无具体数值)。"
    elif x.get("id") == "C3":
        x["status"] = "resolved"
        x["resolution"] = "2026-08-20 用户授权 + 本地官方战法库(hero_extra 马岱 200865)交叉验证：多效战法确认(普攻增伤+减伤同时生效可叠加5次)；阈值表 image_1 减伤属性'攻击'为录入错误，修正为'防御'(按官方'受防御属性影响')。增长率保留表格图参考值。"
    elif x.get("id") == "C4":
        x["status"] = "resolved"
        x["resolution"] = "2026-08-20 用户确认数据源错误(9999%为占位符)，按指示不录入；官方机制(hero_extra 200033)确认遗志为第3回合触发的固定效果(恢复极大量兵力+反击85%+无法恢复)，不适用线性公式。"

# 更新 uncertainties
new_unc = []
for u in tdb["uncertainties"]:
    if "徽言龙凤" in u and "增长率" in u:
        new_unc.append("徽言龙凤 image_0 增伤增长率 → 已标'无数据'（官方仅'受谋略属性影响'无具体数值）")
    elif "遗志" in u and "回血机制" in u:
        new_unc.append("遗志 → 已标 invalid_placeholder 并录入官方回合触发机制，不纳入线性公式（2026-08-20）")
    else:
        new_unc.append(u)
tdb["uncertainties"] = new_unc

# 备份
import shutil
shutil.copy(DB/"threshold_db.json", DB/"threshold_db.json.bak_2026-08-20")
# 写回
json.dump(tdb, open(DB/"threshold_db.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)

print("应用变更:")
for c in changes: print("  -", c)
print(f"\n备份: threshold_db.json.bak_2026-08-20")
print(f"已写回 threshold_db.json")
