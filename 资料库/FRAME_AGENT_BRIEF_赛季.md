# 逐帧判读作业书（赛季 · 1 秒/帧深度学习）

## 背景

《率土之滨》（网易 SLG 手游）抖音攻略视频**全新深度学习**项目（第二批）。素材取自
`D:\Desktop\shandou\抖音\赛季\` 下的 **4 个视频**，内容以**新手科普、赛季机制讲解、四星武将/队伍盘点**为主
（与第一批「海之呼唤」的战场实况不同，这批偏入门与机制科普）。

每个视频已按 **1 秒/帧** 全量抽帧，你的任务是**逐帧判读画面**，产出结构化 JSON，
主控用它渲染成 Word 报告。

这些视频信息**大量存在于画面**：武将卡、战法图标、赛季机制截图、UI 数值、硬字幕大字。
音频转写（whisper）经常把武将名/战法名转错。**逐帧判读的价值就在于补齐和校正这些画面信息。**

> 这是**全新素材**，没有既有报告可比，直接产出自包含深度学习报告。用 `comparison` 字段记录
> **「音频转写说错 / 画面核实为」** 的差异，用 `summary.corrections` 记录画面修正了音频的关键事实。

## 你要读的素材（全部用 Read 工具）

1. **contact sheets**（先看这个建立全局印象）
   `D:\Desktop\shandou\赛季_frames_dense_1s\<frames_dir>\contact_sheets\sheet_01.jpg` …
   每张 40 帧，5 列 × 8 行，从左到右、从上到下按时间顺序排列。
   每格上方标注 `序号 @MM:SS`，序号即 `frame_XXXX` 的编号。

2. **单帧原图**（关键：看不清就必须回看原图）
   `D:\Desktop\shandou\赛季_frames_dense_1s\<frames_dir>\frame_XXXX_MM-SS.jpg`
   contact sheet 是缩略图，武将名、战法名、数值基本看不清。
   **凡是要写进报告的具体名称/数值，都必须回看单帧原图确认**，至少回看 10–20 张。

3. **音频转写**
   `D:\Desktop\shandou\赛季_transcripts\<视频名>.json`

4. **术语库**
   `D:\Desktop\shandou\资料库\名词概念.md`
   遇到不认识的黑话先查这里；这里没有就用 WebSearch（`topic` 必须填 `"general"`）查
   网易大神 ds.163.com / 17173 / B站 / 知乎。
   **查不到就在 limitations 里如实写「查不到」，绝对不要编造。**

## 输出

用 Write 工具写 JSON 到：
`D:\Desktop\shandou\资料库\saiji_frame_json\<视频名>.json`

`video_title` / `frames_dir` 必须与源 mp4 文件名（去掉 .mp4）**逐字一致**，含空格和标点。
`frames_dir` 即 `赛季_frames_dense_1s/` 下与该视频同名的子目录名。

格式严格遵守 `D:\Desktop\shandou\资料库\frame_report_schema.md`（先读它）。
`comparison` 与 `summary.corrections` 用来写 **「音频转写 vs 画面核实」的差异**（没有就留空数组）。

## 质量红线

1. **不编造**。看不清就写看不清，查不到就写查不到，放进 `limitations`。
2. **具体优先**。不要写"作者介绍了赛季"，要写"01:41 介绍征服赛季包含 S1/S2/S3 及兵合车错等，
   推荐新手先打百业争鸣、北伐兴汉"。写不出具体的说明你没回看原图。
3. **文件名必须真实存在**。写 `file` 字段前先 `ls` 或按 `frame_%04d_MM-SS.jpg` 规则算准，
   序号从 0 开始（第 0 秒 = frame_0000_00-00.jpg，第 65 秒 = frame_0065_01-05.jpg）。
   写错会在报告里渲染成红色「图缺失」。
4. **timeline 插图总数控制在 20–40 张**，挑有信息增量的帧，不要连续放几乎相同的画面。
5. 中文引号统一用「」，不要用英文双引号或中文弯引号，避免 JSON 转义出错。
   注意：`「」` 只能出现在**字符串值内部**，JSON 本身的键名/值的定界符必须是半角 `"`。
6. `video_title` 必须与源 mp4 文件名（去掉 .mp4）**逐字一致**，含空格和标点。
7. **JSON 必须写成多行缩进格式（2 空格缩进），严禁把整个 JSON 压成一行。**
   单行超长内容会在写入时被截断，导致文件残缺、结构丢失。
8. **写完必须自检**：用 Read 重新读取自己写的文件，确认
   ① 文件结尾是完整的 `}`；
   ② 顶层字段齐全，必须同时存在 `video_title / video_id / frames_dir / duration_s /
     frame_count / sheet_count / resolution / report_date / summary / timeline /
     comparison / frame_only_value / limitations / glossary / sources` 共 15 个键；
   ③ `timeline` 是数组且非空。
   若发现残缺，重新写一遍（可拆成两次 Write：先写前半再用 Edit 追加），直到自检通过。
9. **写完后必须做磁盘验证**：用 Bash 执行
   `ls -la "D:/Desktop/shandou/资料库/saiji_frame_json/<视频名>.json"`，
   确认文件存在且大于 1KB。若文件不存在或过小，重新 Write 直到磁盘上确实存在有效 JSON。

## 工作步骤建议

1. 读 schema → 读音频转写（建立预期，注意转写常见的武将/战法名音近错误）
2. 顺序读全部 contact sheet，记录画面明显变化的时间点（标题卡、界面切换、盘点列表）
3. 挑 15–25 个关键时间点回看单帧原图，确认具体名称与数值
4. 遇到不懂的术语查术语库 / WebSearch
5. 整理「画面独有」「音频转写被画面修正」两类结论
6. 写 JSON

完成后回复一句话：写入成功 + timeline 帧数 + 发现的画面修正音频条数。150 字以内。
