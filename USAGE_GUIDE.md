# 使用指南 / 操作手册：率土之滨抖音视频深度学习

> 配套 `HANDOFF.md`（项目总览 + 当前对话状态 + 接手指南）。
> 固定规则手册 `资料库/REPORT_CONVENTIONS.md`（**所有报告生成/复核的单一事实来源，必读**）。
> 本文给接手者提供**可直接照抄的命令**与**避坑清单**。所有命令在 Git Bash（Windows）下验证过。
> 最新一日工作流水见 `.workbuddy/memory/2026-08-19.md`。

---

## 0. 必读顺序

1. `HANDOFF.md` §0（一分钟结论）+ §6（当前对话状态与接手指南）
2. `资料库/REPORT_CONVENTIONS.md`（6 大硬规则，单一事实来源）
3. 本文档（命令与避坑）
4. `.workbuddy/memory/2026-08-19.md`（最新工作流水与教训）

---

## 1. 环境

| 项 | 值 |
|---|---|
| Python（managed，必须用这个） | `C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe` |
| 依赖 venv（opencv/python-docx/numpy/Pillow） | `D:\WorkBuddyData\python-env\shandou` |
| whisper 模型缓存（仅重转写用） | `D:/WorkBuddyData/whisper_models/base` |
| 工作目录 | `D:\Desktop\shandou\` 与 `D:\Desktop\shandou\资料库\` |

---

## 2. 通用运行范式（照抄，别改）

**正确模板**（脚本文件模式 + PYTHONPATH + UTF-8 输出）：
```bash
cd "D:/Desktop/shandou/资料库/" && \
PYTHONPATH=D:/WorkBuddyData/python-env/shandou/Lib/site-packages \
PYTHONIOENCODING=utf-8 \
"C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" script.py
```

**错误示范（会崩/静默失败，严禁）：**
- ❌ 用 venv 的 `python.exe` + heredoc（`<<EOF`）：pyrepl 崩溃 WinError 123。
- ❌ `python x.py | tail`：中文输出触发 exit 1 且无任何 stdout/stderr。
- ❌ Bash `rm` 删中文路径文件：`relative path rejected` 且**文件实际没删**。
- ❌ 直接 `python script.py`（不显式 PYTHONPATH）：缺 opencv/python-docx。

**正确取脚本输出**：重定向到 `.log` 再 Read，或 `PYTHONIOENCODING=utf-8` 后直接看 stdout。

---

## 3. 地雷清单（踩中即废）

1. **中文路径读帧**：opencv 直接读中文路径 mp4 会失败。抽帧脚本已用 `ctypes.GetShortPathNameW` 转 8.3 短路径规避；你写新抽帧脚本必须照做。
2. **核验画面一致性**：必须用「全分辨率 + 顺序解码」做基准。缩略图比对、随机 `CAP_PROP_POS_FRAMES` seek 会制造**假故障**（MAE 虚高 3~19，抽样假失败 7/10）。出异常先证伪方法本身。
3. **顺序解码 OOM**：1080p 90 秒全量缓存 ≈ 16GB；必须流式（只留 target±3 帧）。单次样本 ≤8 视频较稳。
4. **源视频特性**：含完全重复帧 + fps=29.993，时间戳偏移 ±1~2 帧属**匹配歧义，不是错误**。
5. **jineng_list.json 不完整**：只含通用/可学战法，**不含武将自带战法**（击势/及锋而试/避锐治气/合纵连横/百战无怯 等在 `hero_extra.json` 的 `methodName*`）。OCR 查战法名**必须用 `official_jineng_names_ext.json`（648 条）**。
6. **非官方标准名**：焚决、关妹、骁锐/筹算、神赏 —— 核查时标「待核实」，**勿当错名**。
7. **宝物词条**：英勇/筹算加发动率（非武/智）；骁锐加攻击%、天资加谋略%。别把「词条名」当「宝物名」。
8. **删除文件**：用 Python `shutil.move`/`os.remove`，不用 Bash `rm`（尤其中文路径）。

---

## 4. 常用任务食谱

### 4.1 跑门禁（确认成果齐全/无损坏/无已知回归）
```bash
cd "D:/Desktop/shandou/资料库/" && \
PYTHONPATH=D:/WorkBuddyData/python-env/shandou/Lib/site-packages PYTHONIOENCODING=utf-8 \
"C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" qc_gate.py
```
- 看输出 `gate_ok`：True 即通过（A 完整性 / B 已知修复回归）。C/D/E 是 INFO 级，不阻塞。

### 4.2 交付体检（章节/插图/字数）
```bash
PYTHONIOENCODING=utf-8 "...python..." final_check.py
```

### 4.3 重新抽帧（1秒/帧，全量）
```bash
PYTHONIOENCODING=utf-8 "...python..." extract_frames_1s.py
# 输出到 抖音_frames_dense_1s/<相对路径>/frame_%04d_MM-SS.jpg + _meta.txt
```
- 抽完用三层核验：`verify_frames_1s.py`（结构）→ `verify_frames_content.py`（内容）→ `verify_final.py`（精度）。

### 4.4 重新音频转写
```bash
PYTHONIOENCODING=utf-8 "...python..." transcribe.py
# 依赖 D:/WorkBuddyData/whisper_models/base（faster-whisper base，中文）
```

### 4.5 重新渲染某份报告 docx（按批次选渲染器）
- 旧 56 项目 / 海之呼唤 / 赛季（通用渲染器）：`gen_refined_report.py`
- **攻其篇精编**：`gen_gongqi_refined.py`（手工批准版，改它必须改母本不能只覆盖 docx）
- **阵容新批**：`gen_refined_report_zhenrong.py`（消费新 schema 的 frame_json，含 `ai_inference` 章节、`bracket_pos()` 位置规整）
- 合并专题（开荒）：`gen_kaihuang.py` + `kaihuang_meta.py`
- 单份 9 章结构旧版：`gen_report.py`
- 批量从逐帧 JSON：`gen_frame_report_batch.py`
- 导出 PDF/图片：`render_docx.py`（docx → LibreOffice headless → pymupdf PNG，**无水印**；勿用 aspose）

> **渲染必须注入 PYTHONPATH**：`PYTHONPATH=D:/WorkBuddyData/python-env/shandou/Lib/site-packages <managed-python> <script>.py`，否则 `No module named 'docx'`。
> **改报告改母本（.py / frame_json），不要只覆盖 docx**，否则重渲复发旧错。

### 4.6 离线数值/品质 parity 全扫（战法+宝物）
```bash
PYTHONIOENCODING=utf-8 "...python..." parity_all.py
# 用 official_skill_db.json / gear_id.json 比对报告断言，输出候选
```
- 逐条判读时排除：引用语境（CITE 正则）、加成后实测值（BUFF 正则）、品质词跨名错绑（用「最近战法名 + 中间不得夹其他名 + 窗口 22」绑定，见 `check_numeric.py` 的 `bind()`）。

### 4.7 抽取可核断言（对战/赛季/数值/宝物）
- `extract_all_claims.py`（全量四分类）
- `extract_reasoning.py`（算术推理）
- `extract_matchup.py`（对战/赛季，选样用）

### 4.8 加/改术语
- 直接编辑 `D:\Desktop\shandou\资料库\名词概念.md`，**附来源链接**（网易大神 / 官网图鉴 / newton）。
- 新发现战法/宝物，先去 `official_*` 白名单与 `official_skill_db.json` 确认官方名，勿凭音译造名。

### 4.9 定点修复 docx（备份先行！）
```bash
# 1) 备份
cd "D:/Desktop/shandou/学习汇报/" && mkdir -p _backup_xxx && cp "目标文件.docx" "_backup_xxx/"
# 2) 用 python-docx 改（参考 fix_deepmu.py / fix_step5.py / fix_numeric_errors.py 写法）
# 3) 验证旧串清零 + 新串就位
# 4) 重跑 qc_gate.py 确认不回归
```
- **永远先备份再改**，仿 `_backup_*` 目录模式。

---

## 5. 验证工作流（改完必须做）

1. 改 docx 后：用 python-docx 读全文，断言「旧串 not in 全文」「新串 in 全文」。
2. **自检必须覆盖表格单元格**：`document.paragraphs` **不含表格内容**，须遍历 `document.tables` 的所有 cell.paragraphs（"钜黍（吕布）"曾藏在投稿三表格 takeaway 单元格，段落自检误判为干净）。
3. 重跑 `qc_gate.py` → `gate_ok=True`。
4. 若动到术语库：确认 `名词概念.md` 与 docx 一致（二者曾发生漂移）。
5. 重大改动后在 `VERIFY_REPORT.md` 追加一节记录。
6. 规则变更（武将书写/位置/AI 推断/路径）必须同步更新 `资料库/REPORT_CONVENTIONS.md`，并校核 `FRAME_AGENT_BRIEF.md` 与 `frame_report_schema.md` 是否同步。

---

## 5.5 阵容新批流水线命令（接手者从这里启动）

### Step 1：查待做视频
```bash
ls "D:/Desktop/shandou/资料库/zhenrong_transcripts/" | grep -v ".wav" | sed 's/.json$//' | sort > /tmp/todo.txt
ls "D:/Desktop/shandou/资料库/zhenrong_frame_json/" | sed 's/.json$//' | sort > /tmp/done.txt
comm -23 /tmp/todo.txt /tmp/done.txt   # 输出待做清单
```

### Step 2：单发子智能体逐帧读图（不要并行！曾 4 并发全静默失败 0 落盘）
派 Agent 工具，作业书 `资料库/FRAME_AGENT_BRIEF.md`，给**精确绝对路径**（不靠 glob），让子智能体逐帧 Read 全部帧后写 `frame_json` 到 `资料库/zhenrong_frame_json/<视频名>.json`。

### Step 3：磁盘复核（必做，失败率约 10%）
```bash
ls -la "D:/Desktop/shandou/资料库/zhenrong_frame_json/<视频名>.json"
```
没落盘 → 重发子智能体。

### Step 4：渲染到阵容新批目录
```bash
cd "D:/Desktop/shandou/资料库/" && \
PYTHONPATH=D:/WorkBuddyData/python-env/shandou/Lib/site-packages PYTHONIOENCODING=utf-8 \
"C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" gen_refined_report_zhenrong.py
# 输出到 学习成果汇总/阵容新批/
```

### Step 5：表格级自检 + 汇报进度
按 §5 验证；每完成 1-3 份向用户汇报（不要后台批量派发，曾导致数小时无反馈被投诉）。

### Step 6：并入主索引
全部 21 份完成后，重建 `资料库/reports_index.md`（由渲染器产出 `reports_index_rows.json` 统一重建）。

---

## 6. 文件命名规范（子智能体/脚本产出必守）

- 报告 docx 文件名 = 源视频文件名 + 后缀（`_完整学习报告` / `_逐帧深度学习报告_1秒版`），**含空格标点逐字一致**。
- 帧文件：`frame_%04d_MM-SS.jpg`（序号 4 位 + MM-SS 时间戳）。
- JSON 报告：与 docx 同名（去后缀），放统一中间目录。
- 截图 id 文内统一 `图1`/`图2` 规范，避免风格不一。
- JSON 内中文引号用「」（全角），避免与 JSON 半角 `"` 定界符冲突。

---

## 7. 回收站（软删产物）

- 路径：`D:\Desktop\shandou\_recycle_20260810\`（2026-08-10 软删的零风险中间产物：旧抽帧 2 目录 + 资料库缓存日志）。
- **恢复**：直接 `shutil.move` 回原路径。
- **永久清理**：确认无需要后，用 Python 删除该目录释放 ~100MB（不要动 `dense_1s`/`transcripts`，重跑需重抽/重转）。

---

## 8. 千万别做的几件事

1. ❌ 重跑「全量重刷 51 视频」/「全量联网核对」——已做过，边际收益趋零且有自伤风险。
2. ❌ 删 `抖音/`、`开荒/`、`学习成果汇总/` 下任何源视频或成果 docx。
3. ❌ 把 `jineng_list.json` 当战法全集去判错名（缺自带战法，会误杀合法名）。
4. ❌ 遇到音译疑似错名就全局替换——多义音近项（如「机势」可能是击势也可能是金吾飞将）须逐篇回查源帧。
5. ❌ 用更快的随机 seek 比对做画面核验（假故障）。
6. ❌ **只手改 docx 不改母本（.py / frame_json）**——下次重渲复发旧错（攻其篇曾因此复发"钜黍（吕布）"）。
7. ❌ **自检只扫段落**——表格单元格里的错误会漏（`document.paragraphs` 不含表格内容）。
8. ❌ **并行派发子智能体**——曾 4 并发全静默失败 0 落盘；改单发 + 精确路径。
9. ❌ **后台批量派发大量任务**——曾导致数小时无反馈被用户投诉；改前台小批，每完成 1-3 份汇报。
10. ❌ **把交付文件放到 `C:\Users\Administrator\Desktop`**——那是另一账户目录，用户看不到；正确桌面 = `D:\Desktop`。
11. ❌ **把武将位置词并入武将名**（"中军兀突骨""大营祝融"）——位置由阵容排序承载，位置词严禁并入武将标识。
12. ❌ **凭通用原理盲推**（"吕布大营首选钜黍"等）——推断前必须查 `distance/type/quality` + 网易大神。

---

## 9. 用户工作风格速查（接手者必读）

- **省钱模式默认**：短句、砍废话、保留技术准确性；安全/不可逆操作自动切详尽。
- **五铁律**：①不确定直说不编造 ②数字标权威源或"需核实" ③通俗直白 ④先结论后理由 ⑤需求模糊主动提问。
- **先问后做**：遇「待你拍板」必须先问，不得自行处理（除非已获明确授权）。
- **后台作业**：无轮询，等完成通知再行动。
- **任务节奏**：用户用简短「继续」驱动；产出问题先根因诊断再批量；进入下一步前 AI 先自核验。
- **保 C 盘**：venv 与缓存都在 D 盘，不要装 C 盘。
- **推断规则**：鼓励 AI 主动推断/总结，但严禁盲推；推断必须单列章节「AI 主动推断内容（非视频原话）」，与视频事实物理隔离。

---

## 10. 项目级 Skill（自动加载）

`D:\Desktop\shandou\.workbuddy\skills\rate-earth-report\SKILL.md`：本项目专用 skill，封装固定规则、流水线、避坑清单。AI 会话开始时自动加载，无需手动调用。

---

## 11. 索引目录与工作日志

- **主索引**：`资料库/reports_index.md`（80 条，字段：序号/标题/关键词/核心武将版本/生成日期/路径）。新增报告后由渲染器更新 `reports_index_rows.json`，统一重建主索引。
- **工作日志**：`.workbuddy/memory/YYYY-MM-DD.md`（每日 append-only）。
- **项目长期记忆**：`.workbuddy/memory/MEMORY.md`。
- **核查总报告**：`资料库/VERIFY_REPORT.md`（§1–§11 历史核查全记录）。
