# 交接提示词（复制给接手 AI）

你是**率土之滨抖音视频深度学习项目**的 AI——本项目最初由你创建，现在请继续接手（交接时间 2026-08-22 14:30，项目负责人已确认）。

项目根目录：`D:\Desktop\shandou\`

## 【必读，按顺序】
1. `D:\Desktop\shandou\HANDOFF_20260822.md` —— 结构化交接（接手时间/工作日志/工作结果/当下任务/停留节点）
2. `D:\Desktop\shandou\HANDOFF_DIALOG_20260822.md` —— 对话脉络（08-20~08-22 决策链、规则由来、用户协作方式）
3. `D:\Desktop\shandou\.workbuddy\memory\RULES\`（01卡面识别/02实体核验/03表述规范/04数据源/05流程）—— **权威规则库，规则只认这里**
4. `D:\Desktop\shandou\.workbuddy\memory\2026-08-22.md` —— 今日日志
5. `D:\Desktop\shandou\USAGE_GUIDE.md` —— 环境与运行范式

## 【当前状态】
- 报告库 163 docx（旧56项目 100 / 海之呼唤 38 / 赛季 8 / 开荒 2 / 阵容新批 14 / 阈值报告 1）
- **阵容新批 23 视频，已完 14**（JSON+精编各 14 份，`资料库/zhenrong_frame_json/` + `报告库/阵容新批/精编/`）
- **甘宁碰瓷队 = 模板金标准**（两遍最严核验：本地库+视觉+官网/网易大神交叉）
- 其余 13 份已全局复核，`crosscheck.py` A-E 全空；宁元刀已定案
- **第十三期测试报告已交用户，等验收**

## 【当下任务】
继续阵容新批**剩余 9 视频**流水线：子智能体逐帧判读（作业书 `资料库/FRAME_AGENT_BRIEF_ZHENRONG.md` + schema `frame_report_schema.md`）→ JSON → 核验 → 精编报告。未产清单见 HANDOFF §4。

## 【铁律速记】（细节以 RULES/ 为准）
- **涉图必调视觉模型** `资料库/vision_glm.py`（Read 看图不可靠、有幻觉）
- 星级/兵种以「画面 + 自带战法→method_map」唯一锚定；固化表仅回退；「极」=红度满星非第6星；陈寿·敏学=4星卡升5星战法不变
- **官方库一律不补录**，须用户真人核验同意；多版本武将（朱儁/大乔/孙权等）按帧判断
- **版本唯一锁定原则**：字段看不清时，其余确定字段在库中唯一锁定版本 → 直接用官方值
- **AI 阅读为唯一标准，冗余即删，无散文摘要**
- 粉丝阵容=点评对象非攻略参考；宝物缺失写空缺不猜测；宝物三层结构 gear/traits/unit_traits
- 环境坑：managed python（`C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe`）+ `PYTHONPATH=D:\WorkBuddyData\python-env\shandou\Lib\site-packages` + **脚本文件模式**（venv heredoc 会崩 WinError 123）

## 【第一个动作】
1. 跑 `D:/WorkBuddyData/zh_verify/crosscheck.py` 确认 13 份全绿
2. 读 RULES/ 五文件
3. 向用户确认：①第十三期测试报告是否达标 ②剩余 9 份推进节奏 ③阵容新批是否要做逐帧1秒版
