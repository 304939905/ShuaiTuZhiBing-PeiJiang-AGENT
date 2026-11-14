# -*- coding: utf-8 -*-
"""为 2026-08-25 的5×5随机抽检生成只读证据包。

不修改任何成果；仅解析 DOCX、定位上游母本/转录/帧目录，
并统计报告内容与本地官方白名单的命中情况。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from docx import Document

ROOT = Path(r"D:\Desktop\shandou")
MANIFEST = ROOT / "资料库" / "5X5_RANDOM_AUDIT_MANIFEST_20260825.md"
OUT = ROOT / "资料库" / "5X5_RANDOM_AUDIT_LOCAL_EVIDENCE_20260825.json"
WHITELIST = ROOT / "资料库" / "official_merged_whitelist.json"


def read_docx(path: Path) -> tuple[list[dict], list[list[list[str]]]]:
    doc = Document(path)
    paragraphs = [
        {"style": p.style.name if p.style else "", "text": p.text.strip()}
        for p in doc.paragraphs
        if p.text.strip()
    ]
    tables = [
        [[cell.text.strip() for cell in row.cells] for row in table.rows]
        for table in doc.tables
    ]
    return paragraphs, tables


def normalize_stem(name: str) -> str:
    suffixes = [
        "_精编学习报告",
        "_精修学习报告",
        "_逐帧深度学习报告_1秒版",
        "_完整学习报告",
    ]
    for suffix in suffixes:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def find_candidates(stem: str, roots: list[Path], suffix: str) -> list[str]:
    exact = []
    fuzzy = []
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob(f"*{suffix}"):
            if p.stem == stem:
                exact.append(str(p))
            elif stem in p.stem or p.stem in stem:
                fuzzy.append(str(p))
    return sorted(set(exact or fuzzy))


def extract_paths(text: str) -> list[str]:
    pat = re.compile(r"[A-Za-z]:[/\\][^\r\n\u3002；;]+")
    return [m.group(0).strip().rstrip(".,。；;") for m in pat.finditer(text)]


def main() -> None:
    manifest_text = MANIFEST.read_text(encoding="utf-8")
    report_paths = [Path(x) for x in re.findall(r"`([A-Za-z]:\\[^`]+\.docx)`", manifest_text)]
    if len(report_paths) != 25:
        raise RuntimeError(f"样本数异常: {len(report_paths)}")

    wl = json.loads(WHITELIST.read_text(encoding="utf-8"))
    vocab = {
        key: sorted(wl[key], key=lambda x: (-len(x), x))
        for key in ["skills", "heroes", "gears", "forge_traits", "unit_traits"]
    }

    json_roots = [
        ROOT / "资料库" / "zhenrong_frame_json",
        ROOT / "资料库" / "frame_json",
    ]
    transcript_roots = [
        ROOT / "资料库" / "zhenrong_transcripts",
        ROOT / "抖音_transcripts",
        ROOT / "海之呼唤_transcripts",
        ROOT / "赛季_transcripts",
    ]
    report_1s_roots = [p for p in (ROOT / "报告库").glob("*/逐帧1秒版")]

    records = []
    for idx, path in enumerate(report_paths, start=1):
        if not path.exists():
            raise FileNotFoundError(path)
        paragraphs, tables = read_docx(path)
        text = "\n".join(p["text"] for p in paragraphs)
        if tables:
            text += "\n" + "\n".join(" | ".join(row) for table in tables for row in table)
        stem = normalize_stem(path.stem)
        declared_paths = extract_paths(text)
        anchors = sorted(set(re.findall(r"(?<!\d)(\d{2}:\d{2})(?!\d)", text)))
        headings = [p["text"] for p in paragraphs if p["style"].startswith("Heading") or p["style"] == "Title"]
        hits = {
            key: [term for term in terms if term and term in text]
            for key, terms in vocab.items()
        }
        records.append(
            {
                "sample_id": f"R{(idx - 1) // 5 + 1}-{(idx - 1) % 5 + 1}",
                "report": str(path),
                "size_bytes": path.stat().st_size,
                "stem": stem,
                "paragraph_count": len(paragraphs),
                "table_count": len(tables),
                "headings": headings,
                "anchors": anchors,
                "declared_paths": declared_paths,
                "declared_path_status": [
                    {"path": x, "exists": Path(x.replace("/", "\\")).exists()} for x in declared_paths
                ],
                "json_candidates": find_candidates(stem, json_roots, ".json"),
                "transcript_candidates": find_candidates(stem, transcript_roots, ".json"),
                "one_second_report_candidates": find_candidates(stem, report_1s_roots, ".docx"),
                "official_term_hits": hits,
                "paragraphs": paragraphs,
                "tables": tables,
                "full_text": text,
            }
        )

    payload = {
        "meta": {
            "date": "2026-08-25",
            "seed": 2007061478,
            "pool": 90,
            "sample_count": 25,
            "read_only": True,
        },
        "records": records,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"DONE records={len(records)} out={OUT}")
    for r in records:
        missing = sum(1 for p in r["declared_path_status"] if not p["exists"])
        print(
            f"{r['sample_id']} paras={r['paragraph_count']} tables={r['table_count']} "
            f"json={len(r['json_candidates'])} trans={len(r['transcript_candidates'])} "
            f"1s={len(r['one_second_report_candidates'])} declared_missing={missing} "
            f"{Path(r['report']).name}"
        )


if __name__ == "__main__":
    main()
