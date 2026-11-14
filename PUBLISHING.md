# GitHub 发布与附件安排

本仓库优先保证首次克隆速度。主分支保存 Agent 源码、规则、结构化资料、索引和最终 DOCX
报告；大体积来源媒体单独可选，不阻塞普通使用。

## 主仓库内容

- Python 工具及其测试；
- Markdown 规则、交接、索引、审计和学习笔记；
- 结构化 JSON 资料库及证据记录；
- 最终案例报告，以及作为检索知识库的 DOCX；
- `README.md`、`AGENTS.md`、`蒸馏视频表.md` 等仓库级说明。

## 不进入主仓库的内容

- `.tools/`：便携 LibreOffice，约 1.10 GB；用户按需自行安装 Office 或 LibreOffice。
- `待蒸馏/`：原始视频、网页快照、抽帧和压缩包；普通使用不需要。
- `临时/`：配将讨论稿、逐页渲染和中间验收文件。
- `.codex_tmp/`：本地模型输出、音频临时文件和中间脚本。
- `_tmp_madai_review_*/`：临时复核输出。
- 百家社原始账号导出、Token、Cookie、API Key、私密凭据和其他本地秘密。
- 图片、PDF、视频、压缩包和多数二进制媒体。

## 可选附件

### 最新配将成果

2026-10-14 的《S3 打架重配方案 v2（30级）Word 报告》单独发布在：

- [下载 Word 报告](https://github.com/304939905/ShuaiTuZhiBing-PeiJiang-AGENT/releases/download/latest-report-v2-20261014/S3_PeiJiang_Report_v2_Level30_20261014.docx)
- [查看成果发布页](https://github.com/304939905/ShuaiTuZhiBing-PeiJiang-AGENT/releases/tag/latest-report-v2-20261014)

该报告是讨论稿，实际觉醒预算不足，`lineup_ready` 和 `delivery_ready` 均为 `false`。

### 原始来源附件

原始来源附件单独发布在：

[`source-attachments-v1`](https://github.com/304939905/ShuaiTuZhiBing-PeiJiang-AGENT/releases/tag/source-attachments-v1)

附件包包含部分长期网页、原始马岱视频、抽帧和压缩包，不是全部 105 个来源视频。
只需要代码、规则、结构化资料和最终报告的用户可以完全跳过附件。

## 为什么不用 Git LFS

当前主仓库约 18 MB，直接普通 Git 克隆即可。若把媒体加入 Git LFS：

- 每次相关克隆仍会请求大对象；
- 会消耗账户的 Git LFS 存储和下载带宽配额；
- 对只需要文本和源码的用户没有收益。

因此采用“主仓库轻量、附件按需下载”的结构。

GitHub 当前规则：

- 普通仓库单文件超过 100 MiB 会被阻止；
- 官方建议仓库尽量小于 1 GiB；
- 单个 Release 最多 1000 个资产；
- 单个 Release 文件必须小于 2 GiB。

官方说明：

- [GitHub 上的大文件](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
- [Git LFS 计费](https://docs.github.com/en/billing/concepts/product-billing/git-lfs)

## 可见性与授权

仓库当前公开。内部包含开发日志、第三方攻略资料、图片和历史摘录，尚未完成公开再分发授权。

改为公开前至少检查：

- 第三方网页、视频、截图和报告摘录的授权与署名；
- 内部路径、账号线索和开发日志是否需要脱敏；
- 原创代码采用的许可证；
- 是否存在账号衍生资料需要继续保密。

仓库中存在文件不等于授予开源许可证。

## 发布前检查

每次推送或创建 Release 前：

1. 运行 `README.md` 和 `AGENTS.md` 中的验证命令。
2. 确认 Git 索引中没有超过 GitHub 限制的文件。
3. 确认未暂存原始账号导出、Token、Cookie 或秘密。
4. 确认主仓库只包含预期文件。
5. 大附件提供 SHA-256 校验值。

## 当前发布状态

- 主仓库：约 18 MB；
- 默认分支：`main`；
- 可见性：公开；
- 可选来源附件：约 91.04 MiB；
- 附件 SHA-256：`BDF71798ECBA21CFBF023BC27ED22673075425F3946E1AD5A5176D8907822B10`。
