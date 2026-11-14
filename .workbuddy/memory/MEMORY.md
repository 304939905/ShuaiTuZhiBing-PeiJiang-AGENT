# 项目长期记忆：率土之滨抖音视频深度学习

## 目标与状态
- 目标：对 `D:\Desktop\shandou\抖音\` 下 56 个率土攻略视频深度学习，每视频 1 份 Word；开荒 6 个合并专题 → 51 份 docx。
- ✅ **旧批次已交付**（2026-08-09）：两套报告（完整版+逐帧1秒版 51 份，1571 插图/25.9万字）；事后勘误 10 处已修复，术语库 `资料库/名词概念.md` 685 行。
- **当前批次（阵容新批，2026-08-20/21 进行中）**：`抖音_frames_dense_1s/阵容/` 23 个视频 → `资料库/zhenrong_frame_json/<视频名>.json`（17 顶层键）。已完 12/23（截至 08-21 14:30）。

## 报告最终结构（2026-08-20 整合）
每视频 = 1 精修(`精编/`) + 1 逐帧1秒版(`逐帧1秒版/`)。报告库共 150 docx：旧56项目(100) / 开荒(2) / 海之呼唤(38) / 赛季(8) / 阵容新批(1) + 阈值报告。3 份标杆精修（攻其篇/神赏篇/009焚决）跳过批量重渲。
- 精修生成器 `资料库/gen_refined.py`：帧名连字符、多帧根路由 FRAME_ROOT_MAP、双时间戳、文末溯源索引。重渲 `资料库/regen_refined.py`（assert gen==71）。
- 旧归档：`归档_备份_20260819/`；报告备份 `D:\WorkBuddyData/shandou_report_backup_20260820`。

## 关键技术
- Python：managed 3.13.12；venv `D:\WorkBuddyData\python-env\shandou`（opencv/python-docx/numpy/Pillow）。
- ⚠️ **运行方式坑**：venv python.exe + heredoc 触发 pyrepl 崩溃(WinError 123)。必须 managed python + `PYTHONPATH=D:\WorkBuddyData\python-env\shandou\Lib\site-packages` + 脚本文件模式。
- **静帧命名（2026-08-20 全库统一）**：`frame_000001_00h00m00s000ms.jpg`（序号=秒+1 补6位）。**frame_000050 时间戳=00h00m49s**（序号-1 秒）——写 file 前先 ls 目录核对，杜绝序号-时间戳错配。
- 抽帧：`资料库/extract_frames.py`（中文路径用 ctypes 短路径）。转写：`资料库/transcribe.py`（faster-whisper base，缓存 D:/WorkBuddyData/whisper_models/base）。
- 文档渲染：`资料库/render_docx.py`（LibreOffice headless → pymupdf PNG）。

## 视觉模型规则（2026-08-21 用户指令，重要）
- **视觉模型不可用 → 立即暂停工作向用户汇报**（不得默默换模型/继续）。
- **默认直接用兜底模型**：`资料库/vision_glm.py` provider 顺序已改为 **① Superoute → ② 阿里云百炼 → ③ 商汤日日新**。Key：环境变量/注册表/secrets 文件三路读取（SUPEROUTE_API_KEY / ALIYUN_API_KEY / SENSENOVA_API_KEY），不回显。
- 用法：`python vision_glm.py <图片路径> [问题]`。
- 实测：gpt-5.5 对率土阵容弹窗识别准（宝物名/兵种词条），智谱限流频繁且质量差。图像 `Read` 工具**不可靠**（有缓存/幻觉），唯用户肉眼核验最可信。

## 宝物栏三层结构（2026-08-21 用户铁律）
1. **宝物名**（图标旁大字）→ `gear`（无宝物=null，禁止编造）
2. **宝物词条**（宝物名**正上方紧邻**小字，如 骁锐/选锋/坚忍/机敏/天资）→ `traits`
3. **兵种词条**（宝物下方小字，如 地利/齐射/疾行/出奇/守备/勇毅/列阵/利刃）→ `unit_traits`
- 常见错误（已修正）：把兵种词条当宝物名（如"疾行"）、把 OCR 误读当宝物（亢戎=元戎）、宝=别鸣误写尉繚、地刹=地利误读。

## 官方三资料库（本地化）
- 武将 `hero_extra.json`(393) ｜ 战法 `jineng_list.json`(516) ｜ 宝物 `gear_id.json`(114) ｜ 全量 `hero.json`(946)。
- 白名单：`official_hero_names.json`(武将298) / `official_jineng_names_ext.json`(扩展战法648) / `official_gear_names.json`(宝物114)。
- **坑**：jineng_list 不含武将自带战法（藏在 hero_extra 的 methodName 字段）；hero_extra 的 quality 是稀有度非星级（星级查 hero.json）。
- **官方库一律不补录**（2026-08-21 用户规则）：不确定项保留画面字面 + limitations 标注，须用户真人核验同意后才可补录。
- 来源优先级：官方接口 JSON ＞ 网易大神 ds.163.com ＞ 官网图鉴。

## 项目约定
- 黑话/术语：优先 WebSearch 网易大神查询，权威释义沉淀 `资料库/名词概念.md`（90+ 词条）。
- **粉丝阵容定位**：粉丝投稿阵容只是点评对象非攻略参考，学习重点是作者点评；宝物/词条缺失写空缺，不猜测补全。
- 易错：宝物词条「英勇/筹算」加战法发动率；「骁锐」加攻击%、「天资」加谋略%。

## 逐帧判读批量流水线（阵容新批）
标准循环（前台串行派发，**不要后台批量**）：
1. 派发子智能体（作业书 `资料库/FRAME_AGENT_BRIEF_ZHENRONG.md`，schema `frame_report_schema.md`，样板看已完成 JSON）
2. **磁盘复核**（子智能体静默失败率 ~10%，光看回复会漏）
3. JSON 语法检查（⚠️ 字符串内禁 ASCII 双引号——第八期 22 处裸引号致解析爆，用状态机转中文弯引号修复）
4. 帧落地核验（ls 目录核对实际文件名）→ 5. 实体核验（武将/战法/宝物/词条 vs 白名单）→ 6. 抽帧核验（Read 或 vision_glm）→ 7. 汇报
- 实体核验要点：词条集需全字段构建（出奇/地利/勇毅/守备/疾行/难测 等是真词条）；画面字面与官方 methodName 字形近标 OCR 存疑；证据链确定真名（队伍名+自带战法匹配）直接写真名。

## 子智能体常见缺陷
| 缺陷 | 修复 |
|---|---|
| JSON 压行截断 | brief 强制多行 + 写后 Read 自检 |
| 裸 ASCII 引号破坏 JSON | 状态机转中文弯引号 |
| 帧引用序号-时间戳错配 | ls 核对后修 file |
| 把词条/宝物混淆、OCR 误读实体名 | 三层结构铁律 + 白名单交叉核验 |
| desc 与画面不符（如 frame_000032 写第2队实为第1队） | 抽帧人工/模型核验后重写 |

## 用户偏好（跨项目）
- 保护 C 盘：venv 在 D 盘；大文件/缓存写 D 盘。
- 桌面文件是临时副本，交付原件落项目文件夹。
- 汇报格式：排版清晰、用词准确简约；查不到如实写；该插图就插图。

## 记忆体系分层（2026-08-22 用户确认）
- **规则库** `.workbuddy/memory/RULES/`（01卡面识别/02实体核验/03表述规范/04数据源/05流程）= 权威源，规则更新只写这里。
- **开发日志** `.workbuddy/memory/YYYY-MM-DD.md`：只记事件/决策/坑，不重复规则全文。
- **交接快照** `.workbuddy/memory/HANDOFF.md`：需要交接时才生成（含规则清单摘要），用完归档。
- 作业书 FRAME_AGENT_BRIEF*.md = 子智能体操作手册，内嵌关键规则 + 指向 RULES/；资料库不加规则副本（避免漂移）。

