import json, os, datetime

BASE = os.path.dirname(os.path.abspath(__file__))

h = json.load(open(os.path.join(BASE, "hero_extra.json"), encoding="utf-8"))
j = json.load(open(os.path.join(BASE, "jineng_list.json"), encoding="utf-8"))
g = json.load(open(os.path.join(BASE, "gear_id.json"), encoding="utf-8"))
hj = json.load(open(os.path.join(BASE, "hero.json"), encoding="utf-8"))

hero_names = sorted({x["name"] for x in h if x.get("name")})
jineng_names = sorted({x["name"] for x in j if x.get("name")})
gear_names = sorted({x["name"] for x in g if x.get("name")})

json.dump({"count": len(hero_names), "names": hero_names},
          open(os.path.join(BASE, "official_hero_names.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
json.dump({"count": len(jineng_names), "names": jineng_names},
          open(os.path.join(BASE, "official_jineng_names.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
json.dump({"count": len(gear_names), "names": gear_names},
          open(os.path.join(BASE, "official_gear_names.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

allmap = {}
for n in hero_names:
    allmap[n] = "hero"
for n in jineng_names:
    allmap.setdefault(n, "jineng")
for n in gear_names:
    allmap.setdefault(n, "gear")
json.dump({"count": len(allmap), "map": allmap},
          open(os.path.join(BASE, "official_all_names.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# 同名跨类检测
cross = [k for k in allmap if sum(1 for src in (hero_names, jineng_names, gear_names) if k in src) > 1]

print("武将白名单:", len(hero_names))
print("战法白名单:", len(jineng_names))
print("宝物白名单:", len(gear_names))
print("总索引(去重):", len(allmap))
print("同名跨类:", cross[:20])

today = datetime.date.today().isoformat()
md = f"""# 率土之滨官方资料库（本地化）· 索引

> 拉取日期：{today} ｜ 来源：网易《率土之滨》官网资料站（stzb.163.com）+ CDN 配置接口
> 用途：作为本项目的**权威白名单**，核对视频学习报告中武将/战法/宝物名的 OCR/音译误识。

## 一、三个核心资料库（对应官网 3 个导航页）

| # | 类别 | 官网页面 | 本地文件 | 记录数 | 数据接口（已验证可用） |
|---|------|----------|----------|--------|------------------------|
| 1 | 武将 | card_list.html | `hero_extra.json` | {len(hero_names)} | `https://g0.gph.netease.com/ngsocial/community/stzb/cfg/hero_extra.json?gameid=g10` |
| 2 | 战法 | jineng_list.html | `jineng_list.json` | {len(jineng_names)} | `https://stzb.163.com/json/jineng_list.json` |
| 3 | 宝物 | baowu_list.html | `gear_id.json` | {len(gear_names)} | `https://g0.gph.netease.com/ngsocial/community/stzb/cfg/gear_id.json?gameid=g10` |

### 字段说明
- **武将 `hero_extra.json`**（list，每条=1 武将，共 42 字段）：`id, name, country(阵营), quality(品质如 3-R), cost, type(兵种), distance(攻击距离), attack/def/ruse/speed/siege(基础属性), *Grow(成长), group/groupName(阵营/部队), policyName/policyDesc(内政/兵种特性), methodName/methodDesc/methodId(自带战法), desc(史实简介)` 等。
- **战法 `jineng_list.json`**（list，每条=1 战法）：`id, name, type(主动/指挥/被动/追击/增益), soldierType(兵种), targetType, targetShow(目标)`。原始带 HTML 实体编码，已解码；原始版存 `jineng_list_raw.json`。
- **宝物 `gear_id.json`**（list，每条=1 宝物）：`id, name, type(武器大类), quality, skillName, skillDesc(词条), obtain(获取), desc`。

## 二、补充资料库
- `hero.json`：{len(hj)} 条「全量英雄定义表」（含赛季卡/SP 卡/界限），字段更偏底层（`hero_id, base_hero_id, is_sp_card, is_season_card, skill_init, season...`）。官网 card_list 实际渲染用的是 `hero_extra.json`，此文件作扩展参考保留。
  - 接口：`https://g0.gph.netease.com/ngsocial/community/stzb/cfg/hero.json?gameid=g10`
- `official_live_supplement.json`：收录官方图片已经明确发布、但当前结构化接口尚未能可靠关联 ID 的新武将/战法。该文件只补缺；ID 未确认前不得覆盖三大官方主库。

## 三、白名单 / 反查索引（核查用）
- `official_hero_names.json`：武将名白名单（{len(hero_names)}）
- `official_jineng_names.json`：战法名白名单（{len(jineng_names)}）
- `official_gear_names.json`：宝物名白名单（{len(gear_names)}，旧 `official_baowu_names.json` 同义保留）
- `official_all_names.json`：全名→类别映射（去重 {len(allmap)}，支持报告内反查某词是武将/战法/宝物）

## 四、来源优先级（沿用上一轮结论并扩展）
1. **官方数据接口 JSON**（本目录三库）＞ 2. 网易大神 ds.163.com ＞ 3. 官网图鉴页文案
- 注意：官网 SPA 页面本身为空壳，真实数据走 CDN（`g0.gph.netease.com/ngsocial/community/stzb/cfg/` 或 `stzb.163.com/json/`），直连 stzb.163.com 域名下 json 多数 404。
"""
open(os.path.join(BASE, "official_db_index.md"), "w", encoding="utf-8").write(md)
print("已生成 official_db_index.md")
