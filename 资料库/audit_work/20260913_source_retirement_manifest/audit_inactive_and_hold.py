# -*- coding: utf-8 -*-
"""Audit inactive DOCX replacements and split the hold group without deleting files."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from docx import Document


ROOT = Path(r"D:\Desktop\shandou")
LIB = ROOT / "资料库"
WORK = LIB / "audit_work" / "20260913_source_retirement_manifest"
INDEX = LIB / "reports_index_rows.json"
MANIFEST = WORK / "SOURCE_RETIREMENT_MANIFEST.json"
OUT_JSON = WORK / "INACTIVE_REPORT_AND_HOLD_AUDIT.json"
OUT_MD = WORK / "INACTIVE_REPORT_AND_HOLD_AUDIT.md"

KNOWN_REPLACEMENTS = {
    "报告库/旧56项目/精编/全率土最细最全攻略合集攻其篇—粉丝投稿解析 来了!看看粉丝们的奇思妙想吧_精编学习报告.docx":
        "报告库/标杆/攻其不备体系投稿解析与配队判断_当前标杆_20260907.docx",
}

SOURCE_BATCH_REPLACEMENTS = {
    "全率土最细最全攻略合集攻其篇粉丝投稿解析": "报告库/标杆/攻其不备体系投稿解析与配队判断_当前标杆_20260907.docx",
    "对自己队伍不确定": "报告库/阵容新批/重蒸馏_2至13_20260911/02_同阵容不同账号为何会变质_重蒸馏学习报告.docx",
    "来来来上人配将": "报告库/阵容新批/重蒸馏_2至13_20260911/03_缺将缺法账号的四队顺序分配_重蒸馏学习报告.docx",
    "来人配将免费粉丝配将第十三期": "报告库/阵容新批/重蒸馏_2至13_20260911/04_资源受限账号的三队分配方法_重蒸馏学习报告.docx",
    "来人配将先到先得": "报告库/阵容新批/重蒸馏_2至13_20260911/05_主力集中与工具队分层_重蒸馏学习报告.docx",
    "免费粉丝配将第九期": "报告库/阵容新批/重蒸馏_2至13_20260911/06_有战法但缺核心武将时如何止损_重蒸馏学习报告.docx",
    "免费粉丝配将第六期": "报告库/阵容新批/重蒸馏_2至13_20260911/07_无孙权账号的替代开荒与四队分配_重蒸馏学习报告.docx",
    "免费粉丝配将第五期": "报告库/阵容新批/重蒸馏_2至13_20260911/08_缺核心后的功能位替代_重蒸馏学习报告.docx",
    "免费配将第八期": "报告库/阵容新批/重蒸馏_2至13_20260911/09_平民账号只配三队的决策_重蒸馏学习报告.docx",
    "配将配将免费配将": "报告库/阵容新批/重蒸馏_2至13_20260911/10_S赛季资源受限的四队分配_重蒸馏学习报告.docx",
    "配将配将专心为粉丝配将": "报告库/阵容新批/重蒸馏_2至13_20260911/11_先识别队伍核心再纠错_重蒸馏学习报告.docx",
    "月卡配将不一定配": "报告库/阵容新批/重蒸馏_2至13_20260911/12_从付费方案反推全局资源错误_重蒸馏学习报告.docx",
    "在给大量粉丝配将以后": "报告库/阵容新批/重蒸馏_2至13_20260911/13_低投入账号如何评价三皇价值_重蒸馏学习报告.docx",
    "开荒专题6视频合并": "报告库/开荒/精编/开荒专题（5视频合并）_精修学习报告.docx",
}

USER_REJECTED_SOURCE_KEYS = {
    "一分钟了解率土之滨玩家要经历的赛季和试师赛季征服赛季推荐百业争鸣和北伐兴汉作为新手初入试师副本",
}

ESSENTIAL_AUDIT_FILES = {
    "资料库/audit_work/20260913_p0_reliability_scan/P0_ADJUDICATION.json",
    "资料库/audit_work/20260913_p0_reliability_scan/P0_ADJUDICATION.md",
    "资料库/audit_work/20260913_p0_reliability_scan/CROSS_REPORT_ACCEPTANCE.json",
    "资料库/audit_work/20260913_p0_reliability_scan/CROSS_REPORT_ACCEPTANCE.md",
    "资料库/audit_work/20260913_p0_reliability_scan/FINAL_SPOTCHECK_RESULT.json",
    "资料库/audit_work/20260913_p0_reliability_scan/FINAL_SPOTCHECK_RESULT.md",
    "资料库/audit_work/20260913_source_retirement_manifest/SOURCE_RETIREMENT_MANIFEST.json",
    "资料库/audit_work/20260913_source_retirement_manifest/SOURCE_RETIREMENT_MANIFEST.md",
    "资料库/audit_work/20260913_source_retirement_manifest/INACTIVE_REPORT_AND_HOLD_AUDIT.json",
    "资料库/audit_work/20260913_source_retirement_manifest/INACTIVE_REPORT_AND_HOLD_AUDIT.md",
}


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def doc_text(path: Path) -> str:
    doc = Document(path)
    parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    parts += [cell.text.strip() for table in doc.tables for row in table.rows for cell in row.cells if cell.text.strip()]
    return "\n".join(parts)


def compact(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", text).lower()


def source_key(path: Path) -> str:
    stem = path.stem
    stem = re.sub(r"^(?:video_)?", "", stem)
    stem = re.sub(r"_top_\d+_\d+", "", stem)
    for suffix in (
        "_逐帧深度学习报告_1秒版", "_精编学习报告", "_精修学习报告",
        "_重蒸馏学习报告", "_正式库旧版", "_原视频静帧重蒸馏试验_20260911",
    ):
        stem = stem.replace(suffix, "")
    return compact(stem)


def size_sum(items: list[dict]) -> int:
    return sum(item.get("bytes", 0) for item in items)


def gib(value: int) -> str:
    return f"{value / 1024 ** 3:.3f} GiB"


def main() -> None:
    rows = json.loads(INDEX.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    inactive = manifest["groups"]["D_inactive_report_docx_review_before_delete"]["items"]

    active_docs = []
    for row in rows:
        path = Path(row["out"])
        text = doc_text(path)
        active_docs.append({
            "rel": row["rel"], "path": path, "title": row["report_heading"],
            "sha": row["content_sha256"], "text_compact": compact(text),
            "name_compact": compact(path.stem + row["report_heading"]),
        })

    decisions = []
    for record in inactive:
        path = ROOT / Path(record["path"])
        rp = record["path"]
        key = source_key(path)
        file_sha = sha(path)
        decision = {
            "path": rp, "bytes": record["bytes"], "source_key": key,
            "status": "hold", "replacement": None, "evidence": [],
        }

        if rp.startswith("报告库/账号诊断/"):
            decision["status"] = "keep_move_to_history"
            decision["evidence"].append("账号诊断不属于视频学习报告，不能随源材料删除")
            decisions.append(decision)
            continue

        if rp in KNOWN_REPLACEMENTS:
            decision["status"] = "retire_replaced"
            decision["replacement"] = KNOWN_REPLACEMENTS[rp]
            decision["evidence"].append("正式索引生成器记录了明确 superseded_by 关系")
            decisions.append(decision)
            continue

        if key in USER_REJECTED_SOURCE_KEYS:
            decision["status"] = "retire_user_rejected"
            decision["evidence"].append("此前已明确决定删除该无保留价值报告及相关内容")
            decisions.append(decision)
            continue

        mapped = [
            (marker, replacement)
            for marker, replacement in SOURCE_BATCH_REPLACEMENTS.items()
            if compact(marker) in key
        ]
        if len(mapped) == 1 and any(a["rel"] == mapped[0][1] for a in active_docs):
            decision["status"] = "retire_replaced"
            decision["replacement"] = mapped[0][1]
            decision["evidence"].append("已完成重蒸馏批次或开荒重制脚本记录了原视频标题与正式报告的唯一映射")
            decisions.append(decision)
            continue

        exact_sha = [a for a in active_docs if a["sha"] == file_sha]
        if len(exact_sha) == 1:
            decision["status"] = "retire_exact_duplicate"
            decision["replacement"] = exact_sha[0]["rel"]
            decision["evidence"].append("DOCX SHA-256 完全相同")
            decisions.append(decision)
            continue

        direct = [a for a in active_docs if len(key) >= 8 and key in a["text_compact"]]
        if len(direct) == 1:
            decision["status"] = "retire_replaced"
            decision["replacement"] = direct[0]["rel"]
            decision["evidence"].append("旧报告原始标题在一份活动报告正文材料范围中完整出现")
            decisions.append(decision)
            continue

        name_direct = [a for a in active_docs if len(key) >= 4 and key in a["name_compact"]]
        if len(name_direct) == 1:
            decision["status"] = "retire_replaced"
            decision["replacement"] = name_direct[0]["rel"]
            decision["evidence"].append("旧报告原始标题与一份活动报告文件名/标题直接对应")
            decisions.append(decision)
            continue

        # Directory role is strong enough to identify a source-layer report,
        # but not enough to invent its replacement. Keep it if unique mapping failed.
        if "逐帧1秒版" in path.parts:
            decision["status"] = "hold_unmapped_source_report"
            decision["evidence"].append("可确认是逐帧源报告，但未唯一锁定对应活动报告")
        else:
            ranked = sorted(
                ((SequenceMatcher(None, key, a["name_compact"]).ratio(), a) for a in active_docs),
                key=lambda x: x[0], reverse=True,
            )
            decision["evidence"].append("没有唯一直接证据；相似度仅作线索，不作为删除依据")
            decision["possible_match"] = ranked[0][1]["rel"] if ranked else None
            decision["possible_match_score"] = round(ranked[0][0], 4) if ranked else None
        decisions.append(decision)

    audit_root = LIB / "audit_work"
    audit_keep = []
    audit_candidate = []
    for path in audit_root.rglob("*"):
        if not path.is_file():
            continue
        item = {"path": rel(path), "bytes": path.stat().st_size}
        if item["path"] in ESSENTIAL_AUDIT_FILES:
            audit_keep.append(item)
        elif "20260913_source_retirement_manifest" in item["path"] and path.name in {
            "build_retirement_manifest.py", "audit_inactive_and_hold.py"
        }:
            audit_keep.append(item)
        else:
            audit_candidate.append(item)

    zhenrong_recon = [
        {"path": rel(p), "bytes": p.stat().st_size}
        for p in (LIB / "zhenrong_recon").rglob("*") if p.is_file()
    ]
    classification_empty = not any(p.is_file() for p in (LIB / "分类").rglob("*"))

    counts = Counter(item["status"] for item in decisions)
    unresolved = [item for item in decisions if item["status"].startswith("hold")]
    payload = {
        "mode": "read_only_audit",
        "deletion_performed": False,
        "inactive_report_decisions": decisions,
        "inactive_report_summary": dict(counts),
        "unresolved_count": len(unresolved),
        "hold_split": {
            "audit_keep": audit_keep,
            "audit_candidate_after_user_confirmation": audit_candidate,
            "zhenrong_recon_source_intermediates": zhenrong_recon,
            "classification_directory_empty": classification_empty,
        },
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    retired = [item for item in decisions if item["status"].startswith("retire")]
    keep = [item for item in decisions if item["status"].startswith("keep")]
    lines = [
        "# 未入索引报告与暂缓目录核验", "",
        "- 本轮只读核验，没有删除或移动文件。",
        f"- 未入索引DOCX：{len(decisions)} 份。",
        f"- 已用直接证据锁定替代/重复关系：{len(retired)} 份，{gib(size_sum(retired))}。",
        f"- 应保留并转入配将历史：{len(keep)} 份。",
        f"- 尚未唯一锁定：{len(unresolved)} 份。", "",
        "## 结论分组", "",
        "| 状态 | 数量 | 含义 |",
        "|---|---:|---|",
    ]
    explanations = {
        "retire_exact_duplicate": "与活动报告文件完全相同，可退役旧位置副本",
        "retire_replaced": "存在唯一活动替代报告，可进入清理候选",
        "retire_user_rejected": "用户已明确放弃，原报告和相关源材料可退役",
        "keep_move_to_history": "账号诊断资料，应保留并归入配将历史",
        "hold_unmapped_source_report": "虽是逐帧源报告，但尚未唯一映射",
        "hold": "没有足够直接证据",
    }
    for status, count in sorted(counts.items()):
        lines.append(f"| `{status}` | {count} | {explanations.get(status, '')} |")
    if unresolved:
        lines += ["", "## 尚未唯一锁定", ""]
        for item in unresolved:
            lines.append(f"- `{item['path']}`")
    lines += [
        "", "## F组拆分", "",
        f"- 审计工作区建议保留：{len(audit_keep)} 个最终结果或生成脚本，{gib(size_sum(audit_keep))}。",
        f"- 审计工作区中间产物候选：{len(audit_candidate)} 个文件，{gib(size_sum(audit_candidate))}。",
        f"- `资料库/zhenrong_recon`：{len(zhenrong_recon)} 个源蒸馏中间文件，{gib(size_sum(zhenrong_recon))}，可并入源材料候选。",
        f"- `资料库/分类`：{'空目录，可清理' if classification_empty else '非空，继续保留'}。", "",
        "完整的逐文件证据、替代路径和F组拆分明细见同目录JSON。", "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "inactive": len(decisions), "status": dict(counts), "unresolved": len(unresolved),
        "audit_keep": len(audit_keep), "audit_candidate": len(audit_candidate),
        "zhenrong_recon": len(zhenrong_recon), "classification_empty": classification_empty,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
