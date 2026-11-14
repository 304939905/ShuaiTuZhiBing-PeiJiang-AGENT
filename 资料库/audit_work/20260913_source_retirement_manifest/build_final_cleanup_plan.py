# -*- coding: utf-8 -*-
"""Consolidate the exact cleanup scope. This script never deletes files."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(r"D:\Desktop\shandou")
LIB = ROOT / "资料库"
WORK = LIB / "audit_work" / "20260913_source_retirement_manifest"
BASE = json.loads((WORK / "SOURCE_RETIREMENT_MANIFEST.json").read_text(encoding="utf-8"))
AUDIT = json.loads((WORK / "INACTIVE_REPORT_AND_HOLD_AUDIT.json").read_text(encoding="utf-8"))
ROWS = json.loads((LIB / "reports_index_rows.json").read_text(encoding="utf-8"))
OUT_JSON = WORK / "FINAL_CLEANUP_DRY_RUN.json"
OUT_MD = WORK / "FINAL_CLEANUP_DRY_RUN.md"


def abspath(relative: str) -> Path:
    return (ROOT / Path(relative)).resolve()


def gib(value: int) -> str:
    return f"{value / 1024 ** 3:.3f} GiB"


def main() -> None:
    groups = BASE["groups"]
    directory_roots = []
    for group_name in (
        "A_low_risk_generated_artifacts",
        "B_source_video_frame_audio_transcript",
        "C_archives_backups_old_delivery",
    ):
        for item in groups[group_name]["items"]:
            directory_roots.append({**item, "group": group_name})

    # Source reconstruction files and an empty classification directory were
    # held in the first pass; the second audit resolved their roles.
    recon = AUDIT["hold_split"]["zhenrong_recon_source_intermediates"]
    if recon:
        recon_root = LIB / "zhenrong_recon"
        directory_roots.append({
            "path": "资料库/zhenrong_recon", "exists": recon_root.exists(),
            "files": len(recon), "bytes": sum(x["bytes"] for x in recon),
            "extensions": {}, "group": "B_source_video_frame_audio_transcript",
        })
    if AUDIT["hold_split"]["classification_directory_empty"]:
        directory_roots.append({
            "path": "资料库/分类", "exists": (LIB / "分类").exists(),
            "files": 0, "bytes": 0, "extensions": {}, "group": "A_low_risk_generated_artifacts",
        })

    retire_reports = [
        {"path": item["path"], "bytes": item["bytes"], "status": item["status"],
         "replacement": item.get("replacement"), "evidence": item["evidence"]}
        for item in AUDIT["inactive_report_decisions"] if item["status"].startswith("retire")
    ]
    keep_reports = [
        item for item in AUDIT["inactive_report_decisions"] if item["status"].startswith("keep")
    ]
    explicit_files = []
    explicit_files.extend({**item, "group": "D_retired_report"} for item in retire_reports)
    explicit_files.extend(
        {**item, "group": "E_other_report_artifact"}
        for item in groups["E_other_report_artifacts"]["items"]
    )
    explicit_files.extend(
        {**item, "group": "F_audit_intermediate"}
        for item in AUDIT["hold_split"]["audit_candidate_after_user_confirmation"]
    )

    protected_files = {Path(row["out"]).resolve() for row in ROWS}
    protected_files.update(abspath(path) for path in BASE["must_keep"]["core_files"])
    protected_roots = [abspath(path) for path in BASE["must_keep"]["core_roots"]]
    protected_files.update(abspath(item["path"]) for item in keep_reports)
    protected_files.update(abspath(item["path"]) for item in AUDIT["hold_split"]["audit_keep"])

    problems = []
    candidate_roots = [abspath(item["path"]) for item in directory_roots]
    candidate_files = [abspath(item["path"]) for item in explicit_files]
    for protected in protected_files:
        for root in candidate_roots:
            if protected == root or root in protected.parents:
                problems.append({"type": "protected_inside_candidate_root", "protected": str(protected), "root": str(root)})
        if protected in candidate_files:
            problems.append({"type": "protected_explicit_file", "protected": str(protected)})
    for root in protected_roots:
        for candidate in candidate_roots:
            if root == candidate or candidate in root.parents or root in candidate.parents:
                problems.append({"type": "protected_root_overlap", "protected": str(root), "candidate": str(candidate)})

    missing = []
    for item in directory_roots + explicit_files:
        if not abspath(item["path"]).exists():
            missing.append(item["path"])

    root_bytes = sum(item["bytes"] for item in directory_roots)
    file_bytes = sum(item["bytes"] for item in explicit_files)
    payload = {
        "mode": "dry_run_only",
        "deletion_performed": False,
        "directory_roots": directory_roots,
        "explicit_files": explicit_files,
        "protected": {
            "active_reports": len(ROWS),
            "keep_inactive_reports": keep_reports,
            "audit_final_files": AUDIT["hold_split"]["audit_keep"],
            "core_roots": BASE["must_keep"]["core_roots"],
            "core_files": BASE["must_keep"]["core_files"],
        },
        "validation": {
            "unresolved_inactive_reports": AUDIT["unresolved_count"],
            "protected_overlap": problems,
            "missing_candidates": missing,
            "ready_for_user_scope_confirmation": not problems and not missing and AUDIT["unresolved_count"] == 0,
        },
        "totals": {
            "directory_roots": len(directory_roots),
            "explicit_files": len(explicit_files),
            "bytes": root_bytes + file_bytes,
        },
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    by_group = {}
    for item in directory_roots + explicit_files:
        g = item["group"]
        by_group.setdefault(g, {"targets": 0, "bytes": 0})
        by_group[g]["targets"] += 1
        by_group[g]["bytes"] += item["bytes"]

    lines = [
        "# 最终清理范围预演", "",
        "- 本文件只是清理计划，没有删除、移动或覆盖任何文件。",
        f"- 候选目录整树：{len(directory_roots)} 个；候选单文件：{len(explicit_files)} 个。",
        f"- 预计释放：{gib(root_bytes + file_bytes)}。",
        f"- 未解决旧报告：{AUDIT['unresolved_count']}。",
        f"- 正式报告/核心资料误包含：{len(problems)}。",
        f"- 候选路径不存在：{len(missing)}。",
        f"- 当前状态：{'可以提交用户确认清理范围' if payload['validation']['ready_for_user_scope_confirmation'] else '尚不能生成删除脚本'}。", "",
        "## 候选汇总", "",
        "| 组别 | 目标数 | 空间 |",
        "|---|---:|---:|",
    ]
    labels = {
        "A_low_risk_generated_artifacts": "缓存、渲染与空目录",
        "B_source_video_frame_audio_transcript": "原视频、静帧、音频、转写及蒸馏中间材料",
        "C_archives_backups_old_delivery": "归档、备份与旧交付包",
        "D_retired_report": "已锁定替代关系或已放弃的旧DOCX",
        "E_other_report_artifact": "报告库非活动PDF等产物",
        "F_audit_intermediate": "历史审计中间文件",
    }
    for group, stat in by_group.items():
        lines.append(f"| {labels.get(group, group)} | {stat['targets']} | {gib(stat['bytes'])} |")
    lines += [
        "", "## 明确保留", "",
        "- 活动索引中的66份A级精编报告。",
        "- 1份独立账号诊断报告，后续转入配将历史。",
        "- 当前机制库、策略知识库、本地武将/战法数据库、名称映射、报告规则与索引。",
        f"- 最终质量门禁与清理清单：{len(AUDIT['hold_split']['audit_keep'])} 个文件。",
        "- 整个配将历史目录。", "",
        "## 安全边界", "",
        "只有用户确认这份范围后，才生成按显式绝对路径执行的PowerShell脚本。脚本仍需先运行 dry-run；正式删除不得使用关键词搜索、通配符或工作区根目录作为目标。", "",
        "逐目录、逐文件明细见 `FINAL_CLEANUP_DRY_RUN.json`。", "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "roots": len(directory_roots), "files": len(explicit_files),
        "bytes": root_bytes + file_bytes, "gib": gib(root_bytes + file_bytes),
        "problems": len(problems), "missing": len(missing),
        "ready": payload["validation"]["ready_for_user_scope_confirmation"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
