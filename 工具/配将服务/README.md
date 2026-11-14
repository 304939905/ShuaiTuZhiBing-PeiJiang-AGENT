# 配将服务：账号 → 方案 → 验收 → 战报反馈

这套工具负责防止资源和硬规则出错，不代替配将师判断强度。所有判断优先使用本次账号、当前客户端战法文本和战报；精编报告只作低权重案例。

## 固定流程

1. 读本次账号、确认赛季、版本、觉醒和战法当前可用数量。新账号不能沿用旧账号结论。
2. 先列候选队伍，不在此阶段承诺战法占用；按赛季门禁排除当前无法新获取的提升项。
3. 按 `priority_rank=1,2,3` 给主力分配武将和核心战法，核对觉醒名额与战法份数。
4. 用剩余资源安排第4队以后；不为凑10队而牺牲前三队。
5. 检查所有权、三阵位、COST、兵种、攻击/战法距离、速度、效果冲突、拆解与回收成本；逐条处理警告。
6. 完整账号咨询在阵容定稿后才给施政两案：`金币获取`和`自由建议`。
7. 按《战报阅读与配将反馈规则》记录准备回合、行动链和第一个异常事件；确定性硬错误可在完整证据下立即纠正，随机性和强度问题收集5–10份代表战报后再调整，不按单场胜负改队。

## 账号解析

百家社原始导出含敏感信息，不放进资料库。先只读检查：

```powershell
$py = 'C:\Users\30493\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONIOENCODING = 'utf-8'
& $py .\工具\配将服务\parse_account.py 'D:\Desktop\账号数据.json'
```

解释器路径已于2026-10-04在本机验证；账号路径为示例，须替换为本次实际文件。当前接手入口见项目根目录 `README.md` 和 `HANDOFF_20261004.md`。

只有用户明确要求建立账号档案，才指定第二个参数写出脱敏 JSON。也可在最终验收时直接用 `--raw-account` 在内存解析，避免留下档案：

```powershell
& $py .\工具\配将服务\audit_consultation.py 'D:\Desktop\账号数据.json' '.\临时\lineup-plan.json' --raw-account
```

武将星级优先用 `hero_extra.id → hero.json.hero_id` 且自带战法 ID 一致的记录锁定。`hero_extra.quality` 的 `4-SR` 不是4星；本地393条同ID对账显示它对应 `hero.json.quality=5`。无法精确匹配的武将会列为未解决项，不能直接编入正式方案。

解析结果会注明原始文件修改时间。宝物只记录本次导出给出的条目：`gear_data_status=not_exposed` 表示导出未展示，`empty_export` 仅表示记录为空，均不能单凭导出证明账号没有宝物。当前两字段战法记录没有单列研究进度，解析器不猜测研究状态；如需拆解/研究建议，应补充当前客户端证据。

战法显示的 `左/右` = **当前空闲份数 / 账号可分配总份数**；已分配 = 右 − 左。`0/1` 表示1份已用、空闲0份，不是未拥有；`1/2` 表示空闲1份、已有1份分配出去；`0/3` 表示3份都已分配。百家社原始导出当前只含左值，解析为 `available_copies`；右值 `total_copies` 暂按战法ID从本地 `skill_extra.skillCount` 补出，并标注 `total_copies_source`，**不是导出直接给出的账号字段**。没有页面对账前，不把这个补出的右值写成已实测账号事实。

解析器还会核对资料库 `notice` 中“可配置几个武将”的文字：与 `skillCount` 一致则标记 `db_notice_agree`；没有这句说明则标记 `db_field_only`；两者冲突时停止推定总份数，使用该战法的方案不能通过正式交付验收。同一战法 ID 的完全相同记录会折叠，内容不同则直接报错，不静默取最后一条。

**默认配将口径（用户确定）：以可分配总份数核算整套新阵容，不以当前空闲份数作为上限。**默认可以拆掉现有队伍并收回其战法；只有用户明确要求保留的旧队，才把其占用与新队一同计入总份数。空闲数只用于说明实际换装时需要先收回几份。若总份数无法可靠确定，不擅自按空闲数或资料库上限冒充账号事实，须标记待核验。

## 方案数据与检查

最小结构见 [配将方案示例.json](配将方案示例.json)。正式方案应补齐：

- 顶层：`season`、`cost_limit`、`team_limit`、`requested_main_teams`、`awakening_resources.five_star_slots`、`teams`、`planned_dismantles`、`planned_acquisitions`、`counter_tactics`、`unused_five_star_reasons`；完整账号咨询加 `consultation_type: "full_account"` 和 `governance_plans` 两案。
- 每队：`name`、`priority`（前三主力填“主力”）、`priority_rank`、`members`、`speed_order`、`core_logic`、`speed_requirements`、`strengths`、`major_counters`、`alternatives`、`awakening_cost`、`dismantling_cost`、`resource_conflicts`。
- 每名武将：`position`、`hero_id`、两个学习战法 ID；未觉醒而计划用第三格时填 `will_awaken: true`。替代战法对象须写 `replacement_cost`。
- 旧队资源：默认按本次全部重组处理；只有**确定要保留**的旧队武将和战法才填 `existing_occupancy.heroes/skills`。校验“保留旧队 + 新队”是否超过总份数，并记录新方案需从旧队收回几份；不再逐份填写 `reallocated_skill_copies`。执行时仍须先从实际旧队拆下再重新配置。
- 拟拆解武将填 `planned_dismantles`，唯一卡、副卡数量不明、五星彩耗都会提示。

仅查硬规则：

```powershell
& $py .\工具\配将服务\validate_lineup.py '.\临时\account-profile.json' '.\临时\lineup-plan.json'
```

完整交付验收：

```powershell
& $py .\工具\配将服务\audit_consultation.py '.\临时\account-profile.json' '.\临时\lineup-plan.json'
```

通过验收后可加 `--render-md '.\临时\配将咨询报告.md'` 生成统一格式的报告；未通过时不会生成正式报告。只有用户明确要求长期保存账号档案时才保留对应 profile，报告本身也应按用户的保存意愿处理。

验收结果分为 `lineup_ready`（阵容与报告字段已合格，可以继续做施政）和 `delivery_ready`（两套施政也齐全，可以正式交付）。每套施政除 `direction` 外，必须在 `plan` 或 `details` 填写非空正文；结构化方案至少含一处非空文本值，纯数字和字典键不算正文。完整账号咨询必须明确 `requested_main_teams`、`cost_limit`、`team_limit` 和 `awakening_resources.five_star_slots`，不能靠检查器默认猜账号约束。

`errors` 必须清零；`warnings` 要逐条判断，已处理项写入 `reviewed_warnings`，每条包含原警告的 `code`、`team`、`message` 以及你的 `decision`、`reason`，不能按一个代码批量忽略。总份数未知、空闲数未知、副卡数量未知等资源警告不可豁免，须补证据或改方案。`notes` 会提示实际换装需收回的份数。最终输出应把“已核实 / 结构判断 / 待复核”分开，不把检查器通过解释成队伍强度保证。

## 赛季门禁

`season_gate.py` 可独立检查战法“当前能否新获取”。已有战法可以继续使用，但“已有一份”不代表当前赛季能再新获取一份。`XP` 只是标签；本地 `provisional_default` 按征服赛季保守过滤，只有会改变正式结论时才列人工核验。克制分析不把我方拥有当成对手拥有证据，只有当季实战观察到的战法可明确例外。

## 战报反馈

先按 [战报阅读与配将反馈规则](../../资料库/官方机制库/战报阅读与配将反馈规则_20260921.md) 阅读截图或文本，再结构化为 JSON；不可读处留空，不猜。

`reports[]` 每条至少有 `id`、`team`、`opponent_archetype`、`result`、`rounds`、`action_order`、`main_damage_source`、`diagnosis_tags`；建议另填：

- `expected_action_order`、`first_control`、`first_buff`、`headshot_round`、`representative`；
- `evidence_status`：`complete / partial / summary_only`；不填按 `summary_only` 处理；
- `first_abnormal_event`：首次偏离配将预期的事件，不写最终结果；
- `mechanism_observations[]`：每项含 `category`、`evidence`、`confidence`，可加 `round`、`current_text_checked`、`controlled_reproduction`。

标准 `category`：行动顺序、触发前提、目标或距离、战法冲突、控制链、增减伤通道、输出结构、生存保护、恢复链、兵种相克、兵力衰减、随机波动、其他。`confidence` 使用 `confirmed / probable / unknown`。

示例观察：

```json
{
  "evidence_status": "complete",
  "first_abnormal_event": "准备回合后释放的同类效果失效",
  "mechanism_observations": [
    {
      "category": "战法冲突",
      "round": 0,
      "evidence": "准备回合日志明确显示后释放效果未生效",
      "confidence": "confirmed",
      "current_text_checked": true,
      "controlled_reproduction": false
    }
  ]
}
```

同一战报 ID 不能重复凑样本；回合数、行动顺序、问题标签和爆头回合格式错误会被拦截。程序只分析已正确结构化的战报，不会自动从截图猜这些字段。

```powershell
& $py .\工具\配将服务\analyze_battle_reports.py '.\临时\battle-reports.json'
```

`summary_only` 只能统计结果，不计入机制诊断样本，其问题标签、行动顺序、爆头回合和机制观察也不参与调整建议。`sample_count` 包含全部有效代表战报，`diagnostic_sample_count` 只含 `complete/partial` 事件证据样本。完整事件链且已核对当前文本时，目标/距离、触发前提、战法冲突或行动顺序等确定性硬错误可立即纠正，但不据一场战报重做整队；发动率、选目标、普通物理波动及一般强度问题，仍要求每队至少5份 `complete/partial` 代表样本，建议5–10份并覆盖常见对手。`partial` 只说明有部分事件证据，不等于具体机制已确认。
复盘时也可给 `audit_consultation.py` 加 `--battle-reports '.\临时\battle-reports.json'`，把实战反馈并入本次咨询验收与报告；调整阵容后重新跑全局验收，形成“战报 → 重复问题 → 修改方案 → 再验收”的闭环。

## 边界与测试

脚本无法自动证明战法数值、目标、具体效果冲突、宝物适配、加点和强度；`effect` 标签只筛出冲突风险，必须回到当前战法文本逐效果判断。百家社导出不提供旧队每份战法的具体去向，也不直接提供比例右值；如果要保留某支旧队，须另列其占用。拆解价值和施政收益同样需当前账号与客户端证据。

```powershell
& $py -m unittest discover -s '.\工具\配将服务' -p 'test_*.py' -v
```

## 五项优化的当前边界

1. 账号导入：已支持只读解析、精确ID锁版本、战法数量和来源状态；导出未提供的研究进度、宝物细节和副卡数不补猜，也不自动建立长期账号档案。
2. 资源检查：已检查武将/战法全局占用、觉醒、赛季、站位、COST、兵种、距离、速度要求和可筛出的效果冲突。队伍强度、具体战法数值与“是否最优”仍由当前文本和战报人工判断。
3. 交付流程：先候选、主力优先、全局验收，再做施政；`lineup_ready` 与 `delivery_ready` 分开。
4. 战报反馈：结构化且每队至少5份有效代表样本才提出重复问题调整；截图识别和实战解释仍需当前证据。
5. 赛季门禁：区分已拥有可用与当前可新获取；暂定XP保守过滤，只在影响正式方案时核验；缺“已确认”状态不说成已确认。
