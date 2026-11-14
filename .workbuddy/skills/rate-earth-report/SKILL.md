---
name: rate-earth-report
description: 率土之滨抖音攻略视频「1秒/帧逐帧深度学习」报告生成与复核工作流。当用户要生成/重渲染/审校/交叉核验率土之滨抖音攻略视频的学习报告（攻其篇/神赏篇/阵容点评/开荒等），或涉及武将版本标签、站位表述、AI推断章节、宝物距离核验时使用。固化了版本标签格式、位置按排序且非强制、AI推断独立成章、外推先查本地库+网易大神、桌面路径D:\Desktop、自检须覆盖表格、改母本不改只覆盖docx 等固定规则。
---

# 率土之滨深度学习报告工作流

项目根：`D:\Desktop\shandou`。视频已按 1秒/帧 全量抽帧于 `抖音_frames_dense_1s/`。
每个视频产出一份 Word 报告（索引块 + 武将版本标签 + 生成日期 + AI推断独立章）。

## 何时用本技能
- 生成/重渲染/审校率土抖音攻略视频学习报告。
- 涉及武将版本标签写法、站位（大营/中军/前锋）表述、宝物攻击距离核验、AI 主动推断章节。
- 继续未完成的批次（如阵容新批剩余视频）。

## 四大硬标准（每份报告必含）
1. 报告索引块（关键词+核心武将版本+生成日期+路径），并追加 `资料库/reports_index.md`。
2. 武将版本标签（格式+位置见下）。
3. 报告生成日期（中性，禁时效警告语）。
4. AI 主动推断独立成章，标注"非视频原话"。

## 武将版本标签（固定格式 + 固定位置）
- **格式**：`阵营-兵种-星级`，如 `群-骑-5星`、`群-步-5星`、`蜀-步-5星(SP)`。
  **名字绝不内嵌**（错误：`群-木鹿大王-骑-5星`、`群-兀突骨-步-5星`）。
- **判定主键=自带战法**：反查 `hero_extra.json` 的 `methodName` 定 阵营/兵种/星级/SP。
- **出现位置仅两处**：① 开头「核心武将（版本）」清单；② 阵容表格「武将」列。
  **正文 prose 只写武将名，不重复版本标签，除非重名**（如张飞(SP)）。

## 位置（站位）规则
- 位置由阵容「大营/中军/前锋」排序承载（第一行=大营、第二=中军、第三=前锋）。
- **位置词严禁并入武将名**（错误：`中军兀突骨`/`前排董卓`/`大营祝融`）。
- **武将资料推荐站位=系统建议，非强制**：某将可放任意位置
  （如"把大营位的祝融替换为兀突骨"=兀突骨接大营）。
- **替换固定写法**：`用 X 替换大营位置的 Y`（X 不带版本/位置；「大营位置的」只作目标槽位限定）。

## 宝物/距离核验
- `hero_extra.json` 的 `distance`：祝融=3 需钜黍+1 补足；吕布=4（长弓）不需钜黍。
- 推断"某将带某宝物"前必须查 `distance`+网易大神 ds.163.com，写入 evidence，禁止盲推。

## AI 主动推断（独立成章）
- JSON 顶层 `ai_inference` 字段，渲染为单独章节，标注非视频原话；与事实物理隔离。
- 每项 `{point, evidence, confidence}`，evidence 含本地库字段+网易大神链接+画面时间点。

## 工程化防复发（必读）
- **用户真实桌面=`D:\Desktop`**（项目根 `D:\Desktop\shandou`）。**不是** `C:\Users\Administrator\Desktop`。
- **改报告必须改生成器母本（`.py`/`frame_json`），不能只覆盖 docx**——否则重渲复发旧错。
- **渲染注入 PYTHONPATH**：`PYTHONPATH="D:/WorkBuddyData/python-env/shandou/Lib/site-packages" <managed-python> <script>.py`，否则 `No module named 'docx'`。
- **自检须覆盖表格单元格**：`document.paragraphs` 不含表格，须遍历 `document.tables` 单元格（"钜黍（吕布）"曾藏在表格 takeaway 单元格逃过段落自检）。
- 渲染产物同步 学习汇报/、学习成果汇总/<批次>/、D:\Desktop 三处。

## 关键文件
- 作业书：`资料库/FRAME_AGENT_BRIEF.md` ｜ Schema：`资料库/frame_report_schema.md`
- 固定规则手册：`资料库/REPORT_CONVENTIONS.md`（single source of truth）
- 渲染器：攻其篇 `gen_gongqi_refined.py`；阵容新批 `gen_refined_report_zhenrong.py`
- 主索引：`资料库/reports_index.md` ｜ 官方库：`hero_extra.json`/`jineng_list.json`/`gear_id.json`/`official_*_names.json`
