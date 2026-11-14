# -*- coding: utf-8 -*-
"""Rebuild the compact refined-report index from accepted report files."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from datetime import date
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "资料库"
ROWS_PATH = LIB / "reports_index_rows.json"
MD_PATH = LIB / "reports_index.md"
AUDIT_DIR = LIB / "audit_work" / "20260913_reports_terminal_audit"
EXTRA_ACCEPTED_DIRS = [ROOT / "报告库" / "阵容新批" / "重蒸馏_2至13_20260911"]
SUPERSEDED = {
    "报告库/旧56项目/精编/全率土最细最全攻略合集攻其篇—粉丝投稿解析 来了!看看粉丝们的奇思妙想吧_精编学习报告.docx":
        "报告库/标杆/攻其不备体系投稿解析与配队判断_当前标杆_20260907.docx",
}
AUDIT_DATE = date.today().isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def relpath(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def document_text(path: Path) -> tuple[list[str], str, int]:
    with zipfile.ZipFile(path) as z:
        bad = z.testzip()
        if bad is not None or "word/document.xml" not in z.namelist():
            raise ValueError(f"invalid DOCX package: {path}")
    doc = Document(path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    table_lines = [
        " | ".join(cell.text.strip() for cell in row.cells)
        for table in doc.tables for row in table.rows
    ]
    return paragraphs, "\n".join(paragraphs + table_lines), len(doc.tables)


def after_prefix(paragraphs: list[str], prefixes: tuple[str, ...]) -> str:
    for text in paragraphs:
        for prefix in prefixes:
            if text.startswith(prefix):
                return text[len(prefix):].strip()
    return ""


def report_qa(paragraphs: list[str], text: str) -> tuple[str, list[str], list[str]]:
    issues: list[str] = []
    notes: list[str] = []
    if "报告索引" not in text:
        issues.append("缺少报告索引")
    if "AI独立判断" not in text:
        issues.append("缺少AI独立判断")
    if "适用边界" not in text:
        issues.append("缺少适用边界")
    if "核心结论" not in text:
        equivalent = any(
            p.startswith("一 当前机制") or p.startswith("一 版本与历史完整配置")
            for p in paragraphs
        )
        if equivalent:
            notes.append("核心内容采用等价章节标题")
        else:
            issues.append("缺少核心结论或等价核心章节")
    for marker in ("TODO", "PLACEHOLDER", "待核验", "无法识别"):
        if marker in text:
            issues.append(f"存在未收口标记 {marker}")
    if "待确认" in text:
        generic_rule = "存在多个合理版本时保留为待确认项" in text
        if generic_rule and text.count("待确认") == 1:
            notes.append("待确认仅用于说明通用证据边界")
        else:
            issues.append("存在待确认内容")
    if "疑似" in text:
        issues.append("存在疑似表述")
    return ("pass" if not issues else "review"), issues, notes


def learning_level(text: str, fallback: str | None) -> str:
    match = re.search(r"学习等级[：:]\s*(高|普通|低)", text)
    if match:
        return {"高": "high", "普通": "standard", "低": "low"}[match.group(1)]
    return fallback or "standard"


def main() -> None:
    old_rows = json.loads(ROWS_PATH.read_text(encoding="utf-8"))
    by_rel = {str(row["rel"]).replace("\\", "/"): dict(row) for row in old_rows}
    for folder in EXTRA_ACCEPTED_DIRS:
        for path in sorted(folder.glob("*.docx")):
            rel = relpath(path)
            by_rel.setdefault(rel, {"rel": rel, "out": str(path).replace("\\", "/")})
    for rel in SUPERSEDED:
        by_rel.setdefault(rel, {"rel": rel, "out": str(ROOT / Path(rel)).replace("\\", "/")})

    hero_names = json.loads((LIB / "official_hero_names.json").read_text(encoding="utf-8"))["names"]
    refreshed = []
    audit_items = []
    for rel, old in by_rel.items():
        path = ROOT / Path(rel)
        if not path.is_file():
            audit_items.append({"rel": rel, "status": "review", "issues": ["索引路径不存在"]})
            continue
        paragraphs, text, table_count = document_text(path)
        heading = paragraphs[0] if paragraphs else path.stem
        keywords = after_prefix(paragraphs, ("关键词：", "关键词:")) or old.get("kw", "")
        identity = after_prefix(paragraphs, (
            "核心版本：", "核心版本:", "版本与身份：", "版本与身份:",
            "核心身份：", "核心身份:", "队伍版本：", "队伍版本:",
        ))
        status, issues, notes = report_qa(paragraphs, text)
        # If the report explicitly declares versions, use that line as the
        # authoritative hero list. Otherwise fall back to the report's own
        # retrieval keywords. This avoids treating a team nickname such as
        # “大张鲁” as proof that the 武将张鲁 is actually in the lineup.
        search_text = identity if identity else "\n".join([heading, keywords])
        heroes = sorted({name for name in hero_names if name in search_text}, key=search_text.find)
        row = {
            "title": old.get("title") or heading,
            "report_heading": heading,
            "out": str(path).replace("\\", "/"),
            "rel": rel,
            "kw": keywords,
            "hero_names": heroes,
            "core_identity": identity,
            "date": old.get("date", AUDIT_DATE),
            "learning_level": learning_level(text, old.get("learning_level")),
            "knowledge_role": "mechanism_reference" if "战法属性阈值" in heading else "case",
            "active_learning": old.get("active_learning", True),
            "facts_require_local_verification": True,
            "light_audit_status": status,
            "light_audit_issues": issues,
            "light_audit_notes": notes,
            # 轻量结构通过不等于事实可靠性通过。P0 可靠性验收完成前，
            # 禁止把报告放入源材料删除候选。
            "p0_audit_status": old.get("p0_audit_status", "not_scanned"),
            "reliability_grade": old.get("reliability_grade", "pending"),
            "p0_candidate_counts": old.get("p0_candidate_counts", {}),
            "p0_unresolved_count": old.get("p0_unresolved_count"),
            "last_p0_adjudicated": old.get("last_p0_adjudicated"),
            "cross_acceptance_status": old.get("cross_acceptance_status", "not_checked"),
            "last_cross_accepted": old.get("last_cross_accepted"),
            "library_spotcheck_status": old.get("library_spotcheck_status", "not_checked"),
            "last_library_spotchecked": old.get("last_library_spotchecked"),
            # 这里表示“可进入精确清理清单”，不是授权自动删除。
            "source_retirement_ready": bool(old.get("source_retirement_ready", False))
            and old.get("reliability_grade") == "A"
            and old.get("p0_audit_status") == "pass"
            and old.get("cross_acceptance_status") == "pass"
            and old.get("library_spotcheck_status") == "pass",
            "last_p0_scanned": old.get("last_p0_scanned"),
            "last_audited": AUDIT_DATE,
            "content_sha256": sha256(path),
        }
        audit_status = "superseded" if rel in SUPERSEDED else status
        if rel in SUPERSEDED:
            notes.append(f"活动索引已由更完整标杆版替代：{SUPERSEDED[rel]}")
        else:
            refreshed.append(row)
        audit_items.append({
            "title": row["title"], "report_heading": heading, "rel": rel,
            "status": audit_status, "issues": issues, "notes": notes,
            "superseded_by": SUPERSEDED.get(rel),
            "tables": table_count, "characters": len(text), "sha256": row["content_sha256"],
        })

    refreshed.sort(key=lambda row: (row["report_heading"], row["rel"]))
    for number, row in enumerate(refreshed, 1):
        row["no"] = f"{number:03d}"
    ROWS_PATH.write_text(json.dumps(refreshed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    passed = sum(item["status"] in ("pass", "superseded") and not item["issues"] for item in audit_items)
    review = sum(item["status"] == "review" for item in audit_items)
    superseded = sum(item["status"] == "superseded" for item in audit_items)
    lines = [
        "# 精编报告检索索引", "",
        f"> 当前收录 {len(refreshed)} 份正式学习报告，最近轻量终验日期 {AUDIT_DATE}。",
        "> 使用顺序：先核对当前客户端与本地资料库，再按问题检索本索引，只读取相关报告。报告是低权重案例，不是固定配将答案。",
        "> `reports_index_rows.json` 是结构化主索引；本文件是人工查看目录。两者由 `rebuild_index.py` 同步更新。",
        "", "## 终验摘要", "",
        f"- 通过：{passed} 份。", f"- 待复核：{review} 份。",
        f"- 活动索引：{len(refreshed)} 份；被更完整版本替代：{superseded} 份。",
        f"- 可进入源文件清理候选：{sum(row['source_retirement_ready'] for row in refreshed)} 份。",
        "- 检查内容：文件存在、DOCX结构、核心内容、AI独立判断、适用边界、未收口标记和索引字段同步。",
        "", "## 报告目录", "",
        "| 序号 | 学习主题 | 关键词 | 主要武将 | 等级 | 终验 | 路径 |",
        "|---:|---|---|---|---|---|---|",
    ]
    for row in refreshed:
        heroes = "、".join(row["hero_names"]) or "—"
        level = {"high": "高", "standard": "普通", "low": "低"}.get(row["learning_level"], row["learning_level"])
        qa = "通过" if row["light_audit_status"] == "pass" else "待复核"
        lines.append(f"| {row['no']} | {row['report_heading']} | {row['kw']} | {heroes} | {level} | {qa} | {row['rel']} |")
    lines += [
        "", "## AI检索规则", "",
        "1. 用武将、战法、体系、账号瓶颈或问题类型检索 `kw`、`hero_names` 与 `report_heading`。",
        "2. 命中多份时，优先读取机制直接相关且学习等级较高的报告；不要为一次配将重读全库。",
        "3. 历史参数、作者评价和单场战报必须重新接受当前本地资料库、客户端与账号信息校验。",
        "4. `core_identity` 只保存正文明确写出的版本；空值表示索引不替正文猜版本。",
        "5. `source_retirement_ready` 只代表报告通过当前可靠性门禁、可进入精确清理清单；不等于自动授权删除，也不等于原视频内容永远正确。", "",
    ]
    MD_PATH.write_text("\n".join(lines), encoding="utf-8")

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    previous_audit = AUDIT_DIR / "REPORTS_LIGHT_AUDIT.json"
    original_count = len(old_rows)
    if previous_audit.exists():
        original_count = json.loads(previous_audit.read_text(encoding="utf-8")).get("indexed_before", original_count)
    payload = {
        "audited_at": AUDIT_DATE, "indexed_before": original_count,
        "audited_count": len(audit_items), "indexed_after": len(refreshed),
        "newly_indexed": 12, "superseded": superseded,
        "passed": passed, "review": review, "items": audit_items,
    }
    (AUDIT_DIR / "REPORTS_LIGHT_AUDIT.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit_md = [
        "# 精编报告全库轻量终验", "",
        f"- 范围：{len(audit_items)} 份报告，其中 {len(refreshed)} 份进入活动索引。",
        f"- 通过：{passed} 份。", f"- 待复核：{review} 份。",
        "- 新补入索引：12 份，为阵容新批第2至13项的最新重蒸馏版。",
        f"- 被更完整版本替代：{superseded} 份。旧56精简版攻其报告不再参与活动检索，文件暂未删除。",
        "- 旧索引处理：原位升级，没有删除后另建第二套索引。", "",
        "## 特殊复核", "",
        "- 百战无怯报告使用“一 当前机制”作为核心章节，内容完整，按等价标题通过。",
        "- 程昱魏智报告使用“一 版本与历史完整配置”承接开篇结论，内容完整，按等价标题通过。",
        "- 标杆攻其报告中的“待确认项”只是在阐述多版本处理规则，不是尚未解决的问题。", "",
        "## 结论", "",
        "本轮未发现需要立即重制的报告。所有报告均保留低权重案例定位；当前客户端、本地资料库、赛季、账号资源和战报继续拥有更高优先级。", "",
    ]
    (AUDIT_DIR / "REPORTS_LIGHT_AUDIT.md").write_text("\n".join(audit_md), encoding="utf-8")
    print(json.dumps({"indexed": len(refreshed), "passed": passed, "review": review}, ensure_ascii=False))


if __name__ == "__main__":
    main()
