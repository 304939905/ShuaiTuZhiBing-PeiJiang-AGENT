# 率土之滨官方资料库（本地化）· 索引

> 拉取日期：2026-08-09 ｜ 来源：网易《率土之滨》官网资料站（stzb.163.com）+ CDN 配置接口
> 用途：作为本项目的**权威白名单**，核对视频学习报告中武将/战法/宝物名的 OCR/音译误识。

## 一、三个核心资料库（对应官网 3 个导航页）

| # | 类别 | 官网页面 | 本地文件 | 记录数 | 数据接口（已验证可用） |
|---|------|----------|----------|--------|------------------------|
| 1 | 武将 | card_list.html | `hero_extra.json` | 298 | `https://g0.gph.netease.com/ngsocial/community/stzb/cfg/hero_extra.json?gameid=g10` |
| 2 | 战法 | jineng_list.html | `jineng_list.json` | 515 | `https://stzb.163.com/json/jineng_list.json` |
| 3 | 宝物 | baowu_list.html | `gear_id.json` | 114 | `https://g0.gph.netease.com/ngsocial/community/stzb/cfg/gear_id.json?gameid=g10` |

### 字段说明
- **武将 `hero_extra.json`**（list，每条=1 武将，共 42 字段）：`id, name, country(阵营), quality(品质如 3-R), cost, type(兵种), distance(攻击距离), attack/def/ruse/speed/siege(基础属性), *Grow(成长), group/groupName(阵营/部队), policyName/policyDesc(内政/兵种特性), methodName/methodDesc/methodId(自带战法), desc(史实简介)` 等。
- **战法 `jineng_list.json`**（list，每条=1 战法）：`id, name, type(主动/指挥/被动/追击/增益), soldierType(兵种), targetType, targetShow(目标)`。原始带 HTML 实体编码，已解码；原始版存 `jineng_list_raw.json`。
- **宝物 `gear_id.json`**（list，每条=1 宝物）：`id, name, type(武器大类), quality, skillName, skillDesc(词条), obtain(获取), desc`。

## 二、补充资料库
- `hero.json`：946 条「全量英雄定义表」（含赛季卡/SP 卡/界限），字段更偏底层（`hero_id, base_hero_id, is_sp_card, is_season_card, skill_init, season...`）。官网 card_list 实际渲染用的是 `hero_extra.json`，此文件作扩展参考保留。
  - 接口：`https://g0.gph.netease.com/ngsocial/community/stzb/cfg/hero.json?gameid=g10`
- `official_live_supplement.json`：收录官方图片已经明确发布、但当前结构化接口尚未能可靠关联 ID 的新武将/战法。该文件只补缺；ID 未确认前不得覆盖三大官方主库。

## 三、白名单 / 反查索引（核查用）
- `official_hero_names.json`：武将名白名单（298，取自 hero_extra）
- `official_jineng_names.json`：通用战法白名单（515，取自 jineng_list）
- `official_jineng_names_ext.json`：★扩展战法白名单（648 = 通用 515 ∪ 武将自带战法 514）。**重要**：`jineng_list.json` 仅是官网「战法」页的通用/可学战法，**不含武将自带战法**（如 击势/及锋而试/避锐治气/合纵连横/百战无怯 等），自带战法藏在 `hero_extra.json` 的 `methodName/methodName1/methodName2` 字段。做报告 OCR 核查时**必须用扩展版**，否则会把合法自带战法误判成错名。
- `official_gear_names.json`：宝物名白名单（114，旧 `official_baowu_names.json` 同义保留）
- `official_all_names.json`：全名→类别映射（去重，已并入扩展战法；支持报告内反查某词是武将/战法/宝物）

## 四、来源优先级（沿用上一轮结论并扩展）
1. **官方数据接口 JSON**（本目录三库）＞ 2. 网易大神 ds.163.com ＞ 3. 官网图鉴页文案
- 注意：官网 SPA 页面本身为空壳，真实数据走 CDN（`g0.gph.netease.com/ngsocial/community/stzb/cfg/` 或 `stzb.163.com/json/`），直连 stzb.163.com 域名下 json 多数 404。

## 五、使用须知 / 已知坑
- **战法「焚决」**：既不在通用战法也不在武将自带战法白名单 → 大概率不是官方标准战法名，可能是玩家/社区术语或某套搭配俗称（如视频标题「配将焚决」「玉符分配焚决」）。报告核查时若遇「焚决」**不要直接当错名**，标「待核实：非官方标准战法名」。
- **「关妹」**：不在武将白名单，官方标准名为「关银屏」（关羽之女）。属玩家昵称，报告中出现应记为昵称而非误识。
- **「骁锐 / 筹算」**：是宝物「词条」（gear_id.json 的 skillName 字段），**不是宝物名**，故正确不在宝物名白名单；核查宝物词条时另查 gear_id.json 的 skillDesc/skillName。
- **「神赏」**：是体系名（神兵天降+赏罚分明 组合），非单个战法名，正确不在战法白名单。
