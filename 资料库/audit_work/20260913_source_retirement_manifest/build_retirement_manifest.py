# -*- coding: utf-8 -*-
"""Build a read-only, conservative source-retirement manifest. Deletes nothing."""

from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path


ROOT = Path(r"D:\Desktop\shandou")
LIB = ROOT / "资料库"
OUT_DIR = LIB / "audit_work" / "20260913_source_retirement_manifest"
INDEX = LIB / "reports_index_rows.json"
OUT_JSON = OUT_DIR / "SOURCE_RETIREMENT_MANIFEST.json"
OUT_MD = OUT_DIR / "SOURCE_RETIREMENT_MANIFEST.md"

# Exact directory roots. Every entry means the complete directory subtree.
LOW_RISK_ROOTS = [
    ROOT / "__pycache__",
    ROOT / ".codex_tmp",
    ROOT / "_qa_s1_report",
    ROOT / "_qa_s1_report_revised",
    ROOT / "_qa_s1_report_revised_v2",
    ROOT / "_qa_s1_report_revised_v3",
    ROOT / "_qa_s1_report_revised_v4",
    ROOT / "qa_s1_second_revision",
    ROOT / "qa_s1_second_revision_v2",
    ROOT / "qa_s1_second_revision_v3",
    ROOT / "qa_s1_second_revision_v4",
    LIB / "__pycache__",
    LIB / "_layout",
    LIB / "audit_render",
    LIB / "sample_frames",
]

SOURCE_ROOTS = [
    ROOT / "哔哩哔哩视频",
    ROOT / "抖音",
    ROOT / "抖音_frames_dense_1s",
    ROOT / "抖音_transcripts",
    ROOT / "开荒",
    ROOT / "赛季_frames_dense_1s",
    ROOT / "赛季_transcripts",
    LIB / "frame_json",
    LIB / "frame_json_kaihuang",
    LIB / "saiji_frame_json",
    LIB / "jizhi_transcripts",
    LIB / "transcripts",
    LIB / "zhenrong_frame_json",
    LIB / "zhenrong_transcripts",
]

ARCHIVE_ROOTS = [
    ROOT / "归档_备份_20260819",
    ROOT / "交付",
    LIB / "_backup_cleanup_20260820",
    LIB / "_backup_deepfix_20260820",
    LIB / "audit_backups",
    LIB / "reports",
    LIB / "reports_json",
]

# These contain useful final audit records mixed with disposable renders/scripts,
# or their role is not sufficiently clear. They must be split before deletion.
HOLD_ROOTS = [
    LIB / "audit_work",
    LIB / "分类",
    LIB / "zhenrong_recon",
]


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def tree_stats(path: Path) -> dict:
    count = 0
    size = 0
    extensions: Counter[str] = Counter()
    if not path.exists():
        return {"path": rel(path), "exists": False, "files": 0, "bytes": 0, "extensions": {}}
    files = [path] if path.is_file() else path.rglob("*")
    for item in files:
        if not item.is_file():
            continue
        try:
            stat = item.stat()
        except OSError:
            continue
        count += 1
        size += stat.st_size
        extensions[item.suffix.lower() or "<none>"] += 1
    return {
        "path": rel(path), "exists": True, "files": count, "bytes": size,
        "extensions": dict(extensions.most_common()),
    }


def sum_group(items: list[dict]) -> dict:
    return {"roots": len(items), "files": sum(x["files"] for x in items), "bytes": sum(x["bytes"] for x in items)}


def gib(size: int) -> str:
    return f"{size / 1024 ** 3:.3f} GiB"


def main() -> None:
    rows = json.loads(INDEX.read_text(encoding="utf-8"))
    active = {Path(row["out"]).resolve() for row in rows if row.get("active_learning", True)}
    ready = all(
        row.get("reliability_grade") == "A"
        and row.get("p0_audit_status") == "pass"
        and row.get("cross_acceptance_status") == "pass"
        and row.get("library_spotcheck_status") == "pass"
        and row.get("source_retirement_ready") is True
        for row in rows
    )

    low = [tree_stats(p) for p in LOW_RISK_ROOTS if p.exists()]
    source = [tree_stats(p) for p in SOURCE_ROOTS if p.exists()]
    archive = [tree_stats(p) for p in ARCHIVE_ROOTS if p.exists()]
    hold = [tree_stats(p) for p in HOLD_ROOTS if p.exists()]

    report_root = ROOT / "报告库"
    inactive_reports = []
    other_report_artifacts = []
    for item in report_root.rglob("*"):
        if not item.is_file() or item.resolve() in active:
            continue
        record = {"path": rel(item), "bytes": item.stat().st_size, "extension": item.suffix.lower()}
        if item.suffix.lower() == ".docx":
            inactive_reports.append(record)
        else:
            other_report_artifacts.append(record)

    overlap = []
    candidate_roots = [Path(ROOT / x["path"]).resolve() for x in low + source + archive]
    for report in active:
        for candidate in candidate_roots:
            if report == candidate or candidate in report.parents:
                overlap.append({"report": rel(report), "candidate_root": rel(candidate)})

    payload = {
        "generated_at": date.today().isoformat(),
        "mode": "dry_run_only",
        "deletion_performed": False,
        "active_reports": len(active),
        "all_active_reports_pass_reliability_gate": ready,
        "active_report_candidate_overlap": overlap,
        "groups": {
            "A_low_risk_generated_artifacts": {"summary": sum_group(low), "items": low},
            "B_source_video_frame_audio_transcript": {"summary": sum_group(source), "items": source},
            "C_archives_backups_old_delivery": {"summary": sum_group(archive), "items": archive},
            "D_inactive_report_docx_review_before_delete": {
                "summary": {"files": len(inactive_reports), "bytes": sum(x["bytes"] for x in inactive_reports)},
                "items": inactive_reports,
            },
            "E_other_report_artifacts": {
                "summary": {"files": len(other_report_artifacts), "bytes": sum(x["bytes"] for x in other_report_artifacts)},
                "items": other_report_artifacts,
            },
            "F_hold_split_required": {"summary": sum_group(hold), "items": hold},
        },
        "must_keep": {
            "active_report_paths": sorted(rel(p) for p in active),
            "core_roots": ["资料库/官方机制库", "资料库/策略知识库", "配将历史"],
            "core_files": [
                "资料库/reports_index_rows.json", "资料库/reports_index.md",
                "资料库/REPORT_CONVENTIONS.md", "资料库/当前精编报告标杆.md",
                "资料库/账号信息获取教程.md", "资料库/ocr_misread_map.json",
                "资料库/official_skill_db.json", "资料库/hero.json", "资料库/skill.json",
                "资料库/hero_extra.json", "资料库/aa_rate_supplement.json",
            ],
        },
        "safety": {
            "can_generate_delete_script_now": not overlap and ready,
            "actual_delete_requires_user_confirmation": True,
            "hold_group_must_be_split_first": True,
            "inactive_reports_require_duplicate_or_supersession_check": True,
        },
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    groups = payload["groups"]
    reclaim_a = groups["A_low_risk_generated_artifacts"]["summary"]["bytes"]
    reclaim_b = groups["B_source_video_frame_audio_transcript"]["summary"]["bytes"]
    reclaim_c = groups["C_archives_backups_old_delivery"]["summary"]["bytes"]
    reclaim_d = groups["D_inactive_report_docx_review_before_delete"]["summary"]["bytes"]
    reclaim_e = groups["E_other_report_artifacts"]["summary"]["bytes"]
    lines = [
        "# 源材料退役候选清单（只读预演）", "",
        f"- 生成日期：{payload['generated_at']}。",
        "- 本次未删除、移动或覆盖任何文件。",
        f"- 活动精编报告：{len(active)} 份；可靠性门禁：{'全部通过' if ready else '未全部通过'}。",
        f"- 活动报告与候选目录交叉：{len(overlap)} 项。",
        "- 清单采用目录整树路径；路径即准确作用范围，不使用模糊关键词删除。", "",
        "## 分类结果", "",
        "| 组别 | 内容 | 文件数 | 空间 | 当前处理建议 |",
        "|---|---|---:|---:|---|",
        f"| A | 缓存、渲染和QA中间产物 | {groups['A_low_risk_generated_artifacts']['summary']['files']} | {gib(reclaim_a)} | 第一批清理候选 |",
        f"| B | 原视频、静帧、音频、转写和源JSON | {groups['B_source_video_frame_audio_transcript']['summary']['files']} | {gib(reclaim_b)} | 报告验收后清理候选 |",
        f"| C | 归档、备份、旧交付包 | {groups['C_archives_backups_old_delivery']['summary']['files']} | {gib(reclaim_c)} | 核对唯一文件后清理 |",
        f"| D | 报告库内未进入活动索引的DOCX | {len(inactive_reports)} | {gib(reclaim_d)} | 逐份做重复/替代校验 |",
        f"| E | 报告库内PDF等非活动产物 | {len(other_report_artifacts)} | {gib(reclaim_e)} | 确认不作交付后清理 |",
        f"| F | 审计工作区及用途不完全明确目录 | {groups['F_hold_split_required']['summary']['files']} | {gib(groups['F_hold_split_required']['summary']['bytes'])} | 暂缓，先拆分最终证据与中间产物 |",
        "", "## 第一至第三批准确目录", "",
    ]
    labels = [
        ("A 第一批低风险候选", low),
        ("B 第二批源材料候选", source),
        ("C 第三批归档与旧交付候选", archive),
    ]
    for title, items in labels:
        lines += [f"### {title}", "", "| 路径（整目录） | 文件数 | 空间 |", "|---|---:|---:|"]
        for item in items:
            lines.append(f"| `{item['path']}` | {item['files']} | {gib(item['bytes'])} |")
        lines.append("")
    lines += [
        "## 必须保留", "",
        "- 活动索引中的66份A级精编报告。",
        "- `资料库/官方机制库`、`资料库/策略知识库`、本地武将/战法数据库、名称映射、报告规则与索引。",
        "- `配将历史`。",
        "- F组在完成拆分前全部保留。", "",
        "## 下一步门槛", "",
        "1. 先审核D组未入索引DOCX，确认每份都有正式替代品或确实无学习价值。",
        "2. 将F组中的最终验收报告、必要规则和索引生成器移入核心区，其余再转为候选。",
        "3. 用户确认准确清理范围后才生成删除脚本；删除脚本按显式绝对路径工作，并先执行一次 dry-run。", "",
        f"JSON明细：`{rel(OUT_JSON)}`。", "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "active": len(active), "ready": ready, "overlap": len(overlap),
        "low_risk": sum_group(low), "source": sum_group(source), "archive": sum_group(archive),
        "inactive_docx": len(inactive_reports), "other_report_artifacts": len(other_report_artifacts),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
