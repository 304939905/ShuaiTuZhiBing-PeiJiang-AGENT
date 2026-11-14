# 项目交接文件：率土之滨抖音视频深度学习

> **本次移交时间：2026-08-19 19:43**
> **本会话工作执行者**：WorkBuddy（GLM-5.2，用户称呼"小八"）
> 本文供接手此项目的同事 / 后续 AI 会话阅读，读完即可在不重新探索的前提下接着干。
> 配套：`USAGE_GUIDE.md`（环境/命令/避坑）、`资料库/REPORT_CONVENTIONS.md`（6大硬规则，单一事实来源）、`资料库/VERIFY_REORG.md`（2026-08-19 物理归置核验报告）。
> 最新一日工作流水见 `.workbuddy/memory/2026-08-19.md`；项目长期约定见 `.workbuddy/memory/MEMORY.md`。

---

## 0. 一分钟结论

- **目标**：把率土之滨抖音攻略视频转成结构化 Word 学习汇报；不断扩展新批次视频；端到端核验最低错误率。报告最终交给 AI 阅读使用，故只留干净知识，剔除一切元信息（旧版修正/转写失真/已核对声明等）。
- **当前阶段（2026-08-19 19:43）**：
  - 项目已**物理归置**完成——所有报告按子项目+版本归入 `报告库/`，非活跃 `_` 目录归入 `归档_备份_20260819/`，视频/静帧/转写保持原位。**证据链 `资料库/evidence_chain.{json,md}` 把每份报告↔静帧图包↔源视频↔转写一键串起**（79份/帧100%/视频100%/转写98%）。
  - **旧56项目** 50 精编 + 开荒 5 精编（独立成组）+ 海之呼唤 19 + 赛季 4 + 阵容新批 1 = 79 份精编，全部在 `报告库/<子>/精编/`；另有完整版 51、逐帧1秒版 74 在 `报告库/<子>/{完整版,逐帧1秒版}/`。
  - **阵容新批 22 视频**：抽帧+转写完成，**仅1份已渲染（配将第五期）**，**剩 21 份待做**——这是**当下的主任务**。
  - 攻其篇精编修正版已交付；009宝物焚决、013神赏篇已按干净母本重渲。
- **不要重做的**：旧102份完整版/1秒版已多轮核验，全量重刷/联网核对边际收益趋零；归置已完成且通过零丢失对账。

---

## 1. 项目背景与目标

- **来源视频**：`抖音/`（北冥合集50个 + 开荒6个 + 海之呼唤19 + 赛季4 + 阵容22 = 101个）；另 `哔哩哔哩视频/`（4个+3srt，未纳入学习）。
- **交付物**：每个视频1份Word深度学习汇报；开荒6个有5份独立精编+1份合并专题。
- **用户格式要求**：排版清晰简约；查不到写「查不到/不知道」；该插图处用抽帧；开荒视频合并深度分析。
- **术语约定**：遇黑话/战法/体系/玩家术语，优先 WebSearch/WebFetch 去 **网易大神 ds.163.com** 查，权威释义整理进 `资料库/名词概念.md`（685行/90+词条）。

---

## 2. 目录结构（2026-08-19 归置后真实状态）

| 目录 | 性质 | 处置 |
|---|---|---|
| `报告库/` | **★所有报告**：`<子项目>/{精编,完整版,逐帧1秒版}/` | 成果留，AI溯源主入口 |
| `资料库/` | 工具+官方库JSON+规则书+证据链+主索引+skill | 核心资产留 |
| `抖音/` `开荒/` | 源视频（输入） | 不可动 |
| `抖音_frames_dense_1s/` `海之呼唤_frames_dense_1s/` `赛季_frames_dense_1s/` | 1秒/帧静帧（输入） | 重资产，重跑需重抽 |
| `抖音_transcripts/` `海之呼唤_transcripts/` `赛季_transcripts/` | 音频转写JSON | 可软删，重跑需重转 |
| `归档_备份_20260819/` | 非活跃`_`目录+重复副本+测试残留 | 可后续确认删除；含55份重做前快照 |
| `.workbuddy/` | 项目记忆（日志+长期记忆+skill） | 留 |

> 操作前完整备份在项目外：`D:\WorkBuddyData\shandou_backup_20260819`（23GB/27662文件，可回滚）。

---

## 3. 交付物清单

### 3.1 报告库（79份精编 + 51完整版 + 74逐帧1秒版 = 204份docx）
- **精编**（`报告库/<子>/精编/`）：旧56 50 + 开荒 5 + 海之呼唤 19 + 赛季 4 + 阵容新批 1 = 79。
- **完整版/逐帧1秒版**（`报告库/<子>/{完整版,逐帧1秒版}/`）：旧56各50 + 开荒各1 + 海之呼唤1秒版19 + 赛季1秒版4。
- 每份精编含：报告索引块（关键词+武将版本标签+生成日期+路径）、武将版本对照表、AI主动推断独立章节。

### 3.2 索引与证据链（均在 `资料库/`）
- `evidence_chain.json` / `.md`：**报告↔静帧图包↔源视频↔转写**一键溯源（79条，缺口标null）。
- `reports_index.md` / `reports_index_rows.json`：主索引（78条，已指向报告库新路径）。
- `VERIFY_REORG.md`：归置核验报告（零丢失对账）。

### 3.3 官方数据资产（本地化金标准，离线核数值的唯一权威源）

| 文件 | 内容 | 关键说明 |
|---|---|---|
| `hero_extra.json` | 武将+自带战法`methodName`+distance/type/quality | quality为稀有度编码**非星级** |
| `hero.json` | 全量英雄定义 | **星级以此 quality 为准**（≥5即5星，核心编码6归5星） |
| `jineng_list.json` | 通用/可学战法 | ⚠️不含武将自带战法 |
| `gear_id.json` | 宝物114件 | 宝物数值金标准 |
| `official_jineng_names_ext.json` | 扩展战法白名单(通用∪自带) | ⚠️OCR查战法名**必须用此表** |
| `official_jineng_supplement.json` | 典藏战法补白名单 | 消误报 单骑救主/正始之变 |
| `official_all_names.json` | 分类映射总表 | |

> **铁律**：战法名OCR核查用 `official_jineng_names_ext.json`，不要用 `jineng_list.json`（缺自带战法，会误杀击势/及锋而试/避锐治气/合纵连横/百战无怯等）。
> **星级铁律**：武将星级查 `hero.json` 的 `quality`；**不要用 `hero_extra.json` 的 quality**（那是'4-SR'稀有度，周瑜/吕蒙等5星武将也显示4-SR，曾导致系统性星级偏低错误）。
> **非官方标准名**（核查时标「待核实」勿当错名）：焚决、关妹、骁锐/筹算、神赏。

---

## 4. 本会话工作日志（2026-08-19，移交者执行）

| 时段 | 工作 |
|---|---|
| 13:22前 | 攻其篇精编去冗余（删修正章节/转写元描述）；009/013按干净母本重渲；星级Bug根因定位（渲染器误用hero_extra的quality，改查hero.json）；本地库污染证伪（8文件体检+官网15武将抽样对账全过） |
| 17:23 | **证据链目录建成**：`evidence_chain.json/.md` + `build_evidence_chain.py`，79份/帧100%/视频100%/转写98% |
| 19:16-19:43 | **物理归置**：盘点(`inventory.py`)→用户拍板归档+报告归置方案→完整备份到D盘隔离区(robocopy/COPY:DAT，27662文件1:1对账PASS)→`organize.py`执行归档+报告库收编→修复2个路由问题(海之呼唤3份开荒误路由/4份dup重复副本)→证据链重跑刷新→主索引78条+md78处路径更新→活跃渲染器2个路径更新→核验报告`VERIFY_REORG.md` |

**工作结果**：项目物理结构从"学习汇报平铺106份+10备份目录混杂"归置为"`报告库/`按子项目+版本清晰分层 + `归档_备份_20260819/`统一收容非活跃资产"；证据链+主索引+渲染器路径全部适配新结构；零文件丢失（扩展名逐类对账PASS）。

---

## 5. 已修复错误（勿重复修）

### 5.1 旧版累计6处（详见 `资料库/VERIFY_REPORT.md`）
程昱魏智众谋不懈/河内世泽品级、高顺群骑奇正之势类型、宝物焚决大橹词条、程昱魏智元戎词条、战法篇深谋远虑类型。修复前快照在 `归档_备份_20260819/学习汇报/_backup_*/`。

### 5.2 攻其篇精编修正（2026-08-19，3处+母本11处）
根因：生成器母本`gen_gongqi_refined.py`硬编码错误+子智能体未做版本反查+自检漏扫表格。修复后通过表格级自检。详见 `VERIFY_REPORT.md` §5.2。最新版三处同步：桌面/报告库旧56精编/（现统一在`报告库/旧56项目/精编/`）。

### 5.3 渲染器星级Bug（2026-08-19）
旧56渲染器`gen_refined_report.py`原用`hero_extra.json`的quality首字符当星级，导致周瑜/吕蒙/太史慈等5星武将系统性标4星。已改查`hero.json`的quality（≥5即5星）。重渲009/013验证达标。

---

## 6. 当下任务与停留节点（接手者从这开始）

### 6.1 当下主任务
**继续做完阵容新批剩余 21 份视频的逐帧精编报告**。当前已完成1份（`video_免费粉丝配将第五期…_top_0_2`）。

### 6.2 流程（单发，勿并行派发——曾4并发全静默失败）
1. 从 `资料库/zhenrong_transcripts/` 选一个未做的视频。
2. 派**单发**子智能体，作业书 `资料库/FRAME_AGENT_BRIEF.md`，schema `frame_report_schema.md`；给精确绝对路径（不靠glob），让子智能体逐帧Read全部帧后写 frame_json 到 `资料库/zhenrong_frame_json/`。
3. **磁盘复核**：比对预期文件名确认真落盘（失败率约10%，光看回复会漏）。
4. `gen_refined_report_zhenrong.py` 渲染 → `报告库/阵容新批/精编/`（路径已更新）。
5. 把新条目追加到 `reports_index_rows.json` + `reports_index.md`（或全部完成后一次性重建主索引并重跑`build_evidence_chain.py`刷新证据链）。
6. 每完成1-3份向用户汇报进度。

### 6.3 停留节点
- 物理归置 ✅ 完成（本会话）
- 证据链+主索引+渲染器路径 ✅ 全部适配新结构
- 【阵容新批第2个视频】：**未启动**——从这里接手
- 阵容新批22视频的转写在 `资料库/zhenrong_transcripts/`（22 json），帧在 `抖音_frames_dense_1s/`（带 `video_` 前缀 + `_top_0_N` 截断标记）。

### 6.4 接手者首条命令（照抄启动）
```bash
# 查还剩哪些阵容视频没做（注意：转写已批量挪到 资料库/zhenrong_transcripts/，证据链里阵容新批缺转写是因主转写目录抖音_transcripts无对应项，zhenrong_transcripts是真实来源）
ls "D:/Desktop/shandou/资料库/zhenrong_transcripts/" | grep -v ".wav" | sort > /tmp/todo.txt
ls "D:/Desktop/shandou/资料库/zhenrong_frame_json/" | sort > /tmp/done.txt
comm -23 <(sed 's/.json$//' /tmp/todo.txt) <(sed 's/.json$//' /tmp/done.txt)
```
输出即待做清单。挑第一个，按 6.2 第2步派单发子智能体。

### 6.5 接手后溯源任何报告
```bash
# 拿到报告标题，一键查其静帧包/源视频/转写
C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe -c "
import json
d=json.load(open('D:/Desktop/shandou/资料库/evidence_chain.json',encoding='utf-8'))
t=input('报告标题关键词: ')
for r in d['records']:
    if t in r['title']:
        print(r['subproject'],'|',r['title'])
        print('  报告:',r['report'])
        print('  静帧:',r['frames_dir'],'(',r['frame_count'],'帧)')
        print('  视频:',r['video'])
        print('  转写:',r['transcript'])
"
```

---

## 7. 用户工作风格与铁律（必须遵守）

### 7.1 五个铁律
1. **不确定直说不编造**：减少AI幻觉，查不到写「查不到/不知道」。
2. **数字/日期/价格标权威源**或标「需核实」，禁止猜测。
3. **通俗直白**，摒弃空洞晦涩词汇。
4. **先结论后理由**，不做冗长铺垫。
5. **需求模糊主动提问**，不揣测作答。

### 7.2 工作模式
- **省钱模式（caveman）为全局默认文风**：短句砍废话保留技术准确性；遇安全/不可逆操作自动切详尽。
- **先问后做**：遇待拍板必须先问用户。
- **后台作业**：无轮询；但⚠️**PowerShell run_in_background 的 task_id 可能下轮丢失**（本会话实测），长任务建议「后台启动+同轮TaskOutput block盯守」。
- **保C盘**：venv在`D:\WorkBuddyData\python-env`，缓存指D盘。
- **robocopy备份**：用`/COPY:DAT`，**不要用`/COPYALL`**（无管理员审核权限会EXIT=16）。

### 7.3 推断规则
- 鼓励AI主动推断/总结，但**严禁盲推**：凡涉及"某将带某宝物/某将替代某将/站位"，必须先查本地库字段（`hero_extra.json`的distance/type + `hero.json`的quality星级）+网易大神核验，把证据写进`ai_inference[].evidence`。
- **事实与推断物理隔离**：推断单列章节「AI主动推断内容（非视频原话）」，不得混进视频事实部分。

---

## 8. 核心方法论与流水线

### 8.1 逐帧判读标准循环（每批6-7前台并行，**不要后台批量派发**）
派发子智能体→磁盘复核→`_jsoncheck.py`语法→`align_json_names.py --apply`→`fix_frame_refs.py --apply`→`normalize_frame_json.py`→渲染→汇报。

### 8.2 子智能体4类典型缺陷+修复
JSON压一行被截断(强制多行+Read自检)｜「」当定界符(仅值内可用)｜全/半角标点写错文件名(align_json_names)｜帧引用错误(fix_frame_refs)。

### 8.3 渲染器对应表（路径均已适配报告库新结构）
| 批次 | 渲染器 | 输出 |
|---|---|---|
| 旧56通用/海之呼唤/赛季 | `gen_refined_report.py` | `报告库/<子>/精编/` |
| 阵容新批 | `gen_refined_report_zhenrong.py` | `报告库/阵容新批/精编/` |
| 攻其篇(已完成) | `gen_gongqi_refined.py` | 历史，勿重跑 |

> 历史 audit/fix/scan 系列脚本仍指向旧路径`学习汇报/`，属一次性脚本，不更新；重跑前先改头部`REP`常量。

---

## 9. 关键环境（详见 USAGE_GUIDE）

- **Python**：managed `C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe`
- **依赖venv**：`D:\WorkBuddyData\python-env\shandou`（opencv-python-headless5.0/python-docx1.2/numpy/Pillow）
- **运行范式**：`PYTHONPATH=D:\WorkBuddyData\python-env\shandou\Lib\site-packages PYTHONIOENCODING=utf-8 <managed-python> script.py`
- **致命坑**：不用venv python+heredoc(pyrepl崩溃WinError123)；不用`python x.py|tail`(中文exit1无输出)；Bash`rm`中文路径静默失败(用Python删)；中文输出禁直接管道(重定向.log再cat)。
- **whisper模型**：`D:/WorkBuddyData/whisper_models/base`
- **LibreOffice**（docx→PDF/PNG无水印）：`D:\LibreOffice\program\soffice.exe`

---

## 10. 接手后常见诉求 → 去哪找

| 我想… | 看/做 |
|---|---|
| 看固定规则 | `资料库/REPORT_CONVENTIONS.md` |
| 溯源某报告的静帧/视频/转写 | `资料库/evidence_chain.json`（§6.5命令） |
| 看归置核验 | `资料库/VERIFY_REORG.md` |
| 接着做阵容新批 | 本文 §6.2 + §6.4 |
| 复核报告达标 | `资料库/qc_gate.py` + `final_check.py`（改REP指向报告库） |
| 重抽帧 | `资料库/extract_frames_1s.py`（中文路径用ctypes GetShortPathNameW转8.3） |
| 重转写 | `资料库/transcribe.py`（faster-whisper base中文） |
| 重新渲染某份 | 见§8.3渲染器表 |
| 改术语 | 编辑`资料库/名词概念.md`（附来源链接） |
| 看一日工作流水 | `.workbuddy/memory/2026-08-19.md` |
| 看项目长期约定 | `.workbuddy/memory/MEMORY.md` |

---

## 11. 一句话给接手 AI

项目已物理归置完成（`报告库/`+`归档_备份_20260819/`+证据链全适配），零丢失对账通过；**从§6.2起继续做阵容新批剩余21份**（单发逐帧读图→`gen_refined_report_zhenrong.py`渲染入`报告库/阵容新批/精编/`→并入主索引+重跑证据链）；动任何文件前先备份到D盘隔离区（robocopy/COPY:DAT）；所有事实断言以`资料库/`官方JSON库为唯一权威，星级查`hero.json`的quality、战法名OCR查`official_jineng_names_ext.json`；遇不确定先查库+网易大神，查不到直说「不知道」，禁止盲推。
