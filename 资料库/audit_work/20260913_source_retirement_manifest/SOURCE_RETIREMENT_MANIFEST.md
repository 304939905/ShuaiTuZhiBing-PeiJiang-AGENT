# 源材料退役候选清单（只读预演）

- 生成日期：2026-09-13。
- 本次未删除、移动或覆盖任何文件。
- 活动精编报告：66 份；可靠性门禁：全部通过。
- 活动报告与候选目录交叉：0 项。
- 清单采用目录整树路径；路径即准确作用范围，不使用模糊关键词删除。

## 分类结果

| 组别 | 内容 | 文件数 | 空间 | 当前处理建议 |
|---|---|---:|---:|---|
| A | 缓存、渲染和QA中间产物 | 292 | 0.070 GiB | 第一批清理候选 |
| B | 原视频、静帧、音频、转写和源JSON | 12075 | 8.108 GiB | 报告验收后清理候选 |
| C | 归档、备份、旧交付包 | 2362 | 0.794 GiB | 核对唯一文件后清理 |
| D | 报告库内未进入活动索引的DOCX | 82 | 0.579 GiB | 逐份做重复/替代校验 |
| E | 报告库内PDF等非活动产物 | 1 | 0.001 GiB | 确认不作交付后清理 |
| F | 审计工作区及用途不完全明确目录 | 1969 | 0.501 GiB | 暂缓，先拆分最终证据与中间产物 |

## 第一至第三批准确目录

### A 第一批低风险候选

| 路径（整目录） | 文件数 | 空间 |
|---|---:|---:|
| `__pycache__` | 2 | 0.000 GiB |
| `.codex_tmp` | 75 | 0.020 GiB |
| `_qa_s1_report` | 48 | 0.011 GiB |
| `_qa_s1_report_revised` | 14 | 0.004 GiB |
| `_qa_s1_report_revised_v2` | 15 | 0.004 GiB |
| `_qa_s1_report_revised_v3` | 15 | 0.004 GiB |
| `_qa_s1_report_revised_v4` | 15 | 0.004 GiB |
| `qa_s1_second_revision` | 16 | 0.004 GiB |
| `qa_s1_second_revision_v2` | 16 | 0.004 GiB |
| `qa_s1_second_revision_v3` | 15 | 0.004 GiB |
| `qa_s1_second_revision_v4` | 16 | 0.004 GiB |
| `资料库/__pycache__` | 29 | 0.000 GiB |
| `资料库/_layout` | 1 | 0.000 GiB |
| `资料库/audit_render` | 0 | 0.000 GiB |
| `资料库/sample_frames` | 15 | 0.003 GiB |

### B 第二批源材料候选

| 路径（整目录） | 文件数 | 空间 |
|---|---:|---:|
| `哔哩哔哩视频` | 7 | 0.246 GiB |
| `抖音` | 79 | 3.489 GiB |
| `抖音_frames_dense_1s` | 11343 | 3.562 GiB |
| `抖音_transcripts` | 92 | 0.266 GiB |
| `开荒` | 5 | 0.322 GiB |
| `赛季_frames_dense_1s` | 416 | 0.140 GiB |
| `赛季_transcripts` | 8 | 0.012 GiB |
| `资料库/frame_json` | 41 | 0.001 GiB |
| `资料库/frame_json_kaihuang` | 5 | 0.000 GiB |
| `资料库/saiji_frame_json` | 4 | 0.000 GiB |
| `资料库/jizhi_transcripts` | 6 | 0.008 GiB |
| `资料库/transcripts` | 2 | 0.006 GiB |
| `资料库/zhenrong_frame_json` | 25 | 0.001 GiB |
| `资料库/zhenrong_transcripts` | 42 | 0.056 GiB |

### C 第三批归档与旧交付候选

| 路径（整目录） | 文件数 | 空间 |
|---|---:|---:|
| `归档_备份_20260819` | 1053 | 0.659 GiB |
| `交付` | 1170 | 0.042 GiB |
| `资料库/_backup_cleanup_20260820` | 5 | 0.040 GiB |
| `资料库/_backup_deepfix_20260820` | 6 | 0.040 GiB |
| `资料库/audit_backups` | 80 | 0.011 GiB |
| `资料库/reports` | 0 | 0.000 GiB |
| `资料库/reports_json` | 48 | 0.001 GiB |

## 必须保留

- 活动索引中的66份A级精编报告。
- `资料库/官方机制库`、`资料库/策略知识库`、本地武将/战法数据库、名称映射、报告规则与索引。
- `配将历史`。
- F组在完成拆分前全部保留。

## 下一步门槛

1. 先审核D组未入索引DOCX，确认每份都有正式替代品或确实无学习价值。
2. 将F组中的最终验收报告、必要规则和索引生成器移入核心区，其余再转为候选。
3. 用户确认准确清理范围后才生成删除脚本；删除脚本按显式绝对路径工作，并先执行一次 dry-run。

JSON明细：`资料库/audit_work/20260913_source_retirement_manifest/SOURCE_RETIREMENT_MANIFEST.json`。
