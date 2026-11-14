# 子智能体工作手册：率土之滨抖音视频学习汇报生成

## 目标
为指定的一批《率土之滨》抖音攻略视频，各生成一份 **9 章节、A/B/C/D 分类、带画面证据** 的 Word 学习汇报的 **JSON 源文件**。
你（子智能体）只负责「读转写 + 读抽帧清单 + 撰写 report JSON」这一智力工作。**不要运行 gen_report.py**，docx 由主控集中生成。

## 输入位置（绝对路径，均存在）
- 音频转写：`D:/Desktop/shandou/抖音_transcripts/<视频名>.json`
  - 结构：`{ "video":..., "model":"base","language":"zh","duration":<秒,float>,"segments":[{"start":<秒>,"end":<秒>,"text":"..."}] }`
  - `segments` 是按时间顺序的逐句旁白转写，是报告的**唯一事实来源**。
- 抽帧画面：`D:/Desktop/shandou/抖音_frames/<视频名>/frame_XX.jpg`（XX 从 00 起，最多 8 张）
  - 帧数 `n` = 该目录里 `.jpg` 的数量；抽帧时间戳公式：`t_i(秒) = duration × (i + 0.5) / n`
  - 例：duration=112.7，n=5 → frame_00≈11.3s，frame_01≈33.8s，frame_02≈56.4s，frame_03≈78.9s，frame_04≈101.4s
  - **注意**：本环境无法读取图片像素。截图说明文字只能依据「该时间戳附近的 transcript 旁白」来写，禁止编造画面细节。
- 格式规范：`D:/Desktop/shandou/资料库/report_schema.md`（必读）
- 范例报告（必读 1~2 个，学习文风与粒度）：
  - `D:/Desktop/shandou/资料库/reports_json/一篇看懂心愿武将所有细节 多少玉一张保底，积分能否保留？一篇全看懂.json`
  - `D:/Desktop/shandou/资料库/reports_json/七擒七纵就是高配磐阵 ，战磐体系迎来全面加强，七擒七纵强度不错。.json`

## 输出位置
- 每个视频一份 JSON：`D:/Desktop/shandou/资料库/reports_json/<视频名>.json`
  - `<视频名>` 必须与转写文件名（去掉 `.json`）**完全一致**（含空格与标点）。
  - 用 Write 工具直接写 UTF-8 JSON。

## JSON 字段规范（9 章节映射）
顶层键（严格按名）：
- `video_title`：视频文件名（含标点空格）
- `video_id`：主控分配的编号（如 V006），照抄
- `duration`：把 transcript 的 `duration`(秒) 格式化为 `MM:SS`（例：112.7 → "01:52"；超过 1 小时用 `HH:MM:SS`）
- `resolution`：**查不到就写 "查不到"**（抖音视频无此元数据）
- `has_subtitle_stream`：false（抖音多为硬字幕，无独立字幕轨）
- `audio_transcribed`：true
- `report_date`："2026-08-07"
- `scope`："完整视频（音频转写 faster-whisper + 逐 ~20s 抽帧画面佐证）"

章节内容：
1. `summary`：`what_it_teaches`(一句话结论) / `core_conclusions`(3~6 条) / `not_concluded`(不宜得出的结论)
2. `content_scope`：`formal`(正式讲解) / `mentioned`(简单提及) / `preview`(系列预告) / `not_covered`(未讲内容) —— 用列表
3. `knowledge`：核心知识详解，按逻辑主题分组 `[{ "topic":"主题","points":[{ "text","time":"MM:SS","evidence":"旁白/字幕/画面","confidence":"明确/推断/无法确认","shot":"图N"(可选) }] }]`
   - `text` 先结论后理由；`time` 取自对应 segment 的 start 格式化；`evidence` 写"旁白"即可（除非能确认画面）
   - 配将/战法类必须分别核对：武将位置(大营/中军/前锋)、普攻距离≠战法距离、战法目标/发动条件/增伤增距取舍
4. `cases`：`[{ "title","time","proves":"证明什么","not_prove":"不能证明什么" }]`
5. `actionable`：`[{ "step","detail" }]` 可执行步骤/检查清单
6. `pitfalls`：常见误区列表
7. `unknown`：查不到/无法确认的内容列表（诚实写"查不到/不知道"）
8. `evidence_index`：`[{ "conclusion","time":"MM:SS","screenshot":"图N","confidence":"明确/推断" }]` 表格行
9. `screenshots`：截图汇总 `[{ "id":"图1","time":"MM:SS","path":"绝对路径.jpg","caption":"说明" }]`
   - `path` = `D:/Desktop/shandou/抖音_frames/<视频名>/frame_XX.jpg`
   - `time` 用上面的帧时间戳公式算，格式化 MM:SS
   - `caption`：依据该时间戳附近 transcript 旁白写一句，如"约 00:00:33：讲解两小一大保底规律（旁白：每天免费半架一共有4次）"
   - 每个视频选 **3~5 张**帧，尽量均匀覆盖（如 frame_00、frame_02、frame_04，确认文件存在）；`knowledge.points` 里用 `shot:"图N"` 把相关截图插到对应知识点旁

## A/B/C/D 信息分类（写入正文时遵守）
- A 视频明确说明（旁白/字幕/画面）→ 直接写，`confidence:"明确"`
- B 根据画面/上下文推断 → 必须标注"推断"，`confidence:"推断"`
- C 外部补充 → 放 `unknown` 并注明"外部未核实"，不要当成视频内容
- D 查不到/无法确认 → 写"查不到/不知道"，**禁止猜测**

## 质量红线（用户硬性要求）
- 内容必须**基于 transcript 旁白**，不得无中生有；率土游戏常识若补充须标"推断"。
- 查不到就写查不到，绝不编造数值/概率/武将属性。
- 排版清晰简约、用词准确；中文内部引号用「」避免 JSON 转义错误。
- JSON 必须合法（无未转义控制字符）。写完后可自行用 python 快速校验 json.load。

## 你不做的事
- 不运行 gen_report.py / 不生成 docx（主控集中处理）。
- 不修改 抖音_transcripts / 抖音_frames 原始数据。
