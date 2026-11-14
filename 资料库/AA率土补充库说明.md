# AA率土权威补充层

## 用途

`aa_rate_supplement.json` 由 `sync_aa_rate_supplement.py` 从
`AA率土/率土之滨数据库.xlsx` 生成。它用于补充现有武将、战法、战法效果和状态
资料，不替换原有 `hero.json`、`hero_extra.json`、`skill_extra.json`。

## 安全边界

- 武将：先排除 `book_type != 0` 的兵书/战法书配置，再仅收录能以 `heroid = hero_id` 精确关联到 `hero.json` 的 941 条记录。
- 战法：仅收录现有 `skill_extra.json`、武将自带战法和 `official_skill_db.json` 已引用且能以 ID/名称精确关联的记录。
- 原表其余条目保留在 Excel 原始源中；未完成“是否可携带/可拆解”的分类前，不能用于配将、拆解或白名单结论。
- `is_release` 不是“游戏内可用/可获取”的可靠字段；同步程序不会用它过滤武将，也不能据此给出资产结论。
- `quality` 的换算规则为 `AA quality + 1 = 项目星级`，质量代码 5 仍按项目规则显示为 5 星。
- 原表有 4 个主效果缺少效果明细：枭姬、诸葛锦囊、魏武之泽、全虎朱梦。其中前三项已被现有资料引用，因此会在补充层标记为缺证据；全虎朱梦未进入现有引用范围。不得从缺失明细自动推导其数值或冲突状态。
- 补充层已接入 `hero_version_resolver.py`。新源显示一批普通卡与 SP 卡共享同名、自带战法，少数还共享兵种和星级；这 151 组不再默认判为普通版。必须提供同帧的普通/SP/XP 标识；若同标识下仍有多个候选，再提供兵种。历史报告不自动重渲，避免在没有卡面证据时把旧结论批量改成“版本待核实”。

## 更新与核验

源文件更新后，用项目 Python 运行：

```powershell
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'D:\Desktop\shandou\资料库\sync_aa_rate_supplement.py'
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'D:\Desktop\shandou\资料库\test_aa_rate_supplement.py'
```

生成文件记录源 Excel 的 SHA-256，用于确认之后的查询对应同一份权威源。
