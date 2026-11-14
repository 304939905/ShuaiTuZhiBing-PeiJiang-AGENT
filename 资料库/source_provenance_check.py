#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查旧批视频母本及报告的来源可追溯性。

覆盖范围：旧56、开荒、海之呼唤、赛季的逐帧 JSON 与对应精编/精修 DOCX。
不能从当前快照推断历史上是否删过某条来源；以后若删除来源，母本必须写
``source_deletions``，每项至少包含 ``source`` 与 ``reason``，供本检查器验证。
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from docx import Document
from gen_refined_report import _source_items, _source_urls


ROOT = Path(r"D:/Desktop/shandou")
SOURCE_DIRS = (
    ROOT / "资料库" / "frame_json",
    ROOT / "资料库" / "frame_json_kaihuang",
    ROOT / "资料库" / "hzh_frame_json",
    ROOT / "资料库" / "saiji_frame_json",
)
REPORT_DIRS = (
    ROOT / "报告库" / "旧56项目" / "精编",
    ROOT / "报告库" / "开荒" / "精编",
    ROOT / "报告库" / "海之呼唤" / "精编",
    ROOT / "报告库" / "赛季" / "精编",
)

FORBIDDEN_CLAIMS = (
    "网易大神 ds.163.com 核验后的主动推断",
    "已由网易大神核验",
)
EXTERNAL_NAME_RE = re.compile(r"网易大神|ds\.163\.com", re.I)


def issue(level: str, code: str, path: Path, detail: str) -> dict:
    return {"level": level, "code": code, "path": str(path), "detail": detail}


def validate_source_deletions(value, path: Path) -> list[dict]:
    if value is None:
        return []
    if not isinstance(value, list):
        return [issue("ERROR", "SOURCE_DELETIONS_TYPE", path, "source_deletions 必须是列表")]
    findings = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            findings.append(issue("ERROR", "SOURCE_DELETION_FORMAT", path, f"第 {index + 1} 项必须是对象"))
            continue
        if not str(item.get("source") or "").strip():
            findings.append(issue("ERROR", "SOURCE_DELETION_SOURCE", path, f"第 {index + 1} 项缺少 source"))
        if not str(item.get("reason") or "").strip():
            findings.append(issue("ERROR", "SOURCE_DELETION_REASON", path, f"第 {index + 1} 项缺少 reason"))
    return findings


def check_json(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [issue("ERROR", "JSON_READ", path, f"无法读取：{exc}")]

    findings = []
    raw_sources = data.get("sources")
    items = _source_items(raw_sources)
    if not items:
        findings.append(issue("ERROR", "SOURCE_EMPTY", path, "sources 为空或清洗后为空"))
    else:
        joined = "\n".join(items)
        if EXTERNAL_NAME_RE.search(joined) and not _source_urls(items):
            findings.append(issue("WARN", "EXTERNAL_NAME_NO_URL", path, "提到外部站点但未给可复现 HTTP(S) 直链"))
    findings.extend(validate_source_deletions(data.get("source_deletions"), path))

    raw = json.dumps(data, ensure_ascii=False)
    for claim in FORBIDDEN_CLAIMS:
        if claim in raw:
            findings.append(issue("ERROR", "FORBIDDEN_EXTERNAL_CLAIM", path, claim))
    return findings


def check_docx(path: Path) -> list[dict]:
    try:
        paragraphs = [p.text.strip() for p in Document(path).paragraphs]
    except Exception as exc:
        return [issue("ERROR", "DOCX_READ", path, f"无法读取：{exc}")]

    findings = []
    source_lines = [p for p in paragraphs if p.startswith("来源：") or p.startswith("证据来源：")]
    # 旧“精修”报告把原始静帧范围列在“溯源索引”章节，虽非字面“来源：”
    # 行，仍是可打开的本地画面证据；不能误报为来源缺失。
    has_trace_index = any("溯源索引" in p or "时间锚" in p and "静帧" in p for p in paragraphs)
    if not source_lines and not has_trace_index:
        findings.append(issue("WARN", "REPORT_SOURCE_MISSING", path, "未找到来源行或溯源索引"))
    else:
        for line in source_lines:
            value = line.removeprefix("来源：").strip()
            if not value:
                findings.append(issue("ERROR", "REPORT_SOURCE_EMPTY", path, "“来源：”行为空"))
            if any(claim in line for claim in FORBIDDEN_CLAIMS):
                findings.append(issue("ERROR", "FORBIDDEN_EXTERNAL_CLAIM", path, line))
            if EXTERNAL_NAME_RE.search(line) and not re.search(r"https?://", line, re.I):
                findings.append(issue("WARN", "REPORT_EXTERNAL_NAME_NO_URL", path, "报告来源提到外部站点但无直链"))
    return findings


def run(root: Path = ROOT) -> tuple[list[dict], dict]:
    json_paths = [p for directory in SOURCE_DIRS for p in sorted(directory.glob("*.json")) if p.exists()]
    report_paths = [p for directory in REPORT_DIRS for p in sorted(directory.glob("*.docx")) if p.exists()]
    findings = [f for path in json_paths for f in check_json(path)]
    findings.extend(f for path in report_paths for f in check_docx(path))
    stats = {
        "json_files": len(json_paths),
        "docx_files": len(report_paths),
        "errors": sum(f["level"] == "ERROR" for f in findings),
        "warnings": sum(f["level"] == "WARN" for f in findings),
        "by_code": dict(sorted(Counter(f["code"] for f in findings).items())),
    }
    return findings, stats


def write_report(path: Path, findings: list[dict], stats: dict) -> None:
    lines = [
        "# 来源可追溯性自动检查",
        "",
        f"- JSON 母本：{stats['json_files']}",
        f"- DOCX 报告：{stats['docx_files']}",
        f"- ERROR：{stats['errors']}",
        f"- WARN：{stats['warnings']}",
        "",
        "说明：检查器不能从当前文件快照推断历史上是否删除过来源；未来删除必须写 `source_deletions`，并包含 `source` 和 `reason`。",
        "",
        "## 发现",
        "",
    ]
    if not findings:
        lines.append("无。")
    else:
        for f in findings:
            lines.append(f"- [{f['level']}] `{f['code']}`：`{f['path']}` — {f['detail']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, help="可选：写入 Markdown 报告")
    args = parser.parse_args()
    findings, stats = run()
    print(json.dumps({"stats": stats, "findings": findings}, ensure_ascii=False, indent=2))
    if args.report:
        write_report(args.report, findings, stats)
        print(f"REPORT={args.report}")
    raise SystemExit(1 if stats["errors"] else 0)
