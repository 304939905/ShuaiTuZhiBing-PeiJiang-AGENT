"""Extract indexed DOCX text for a traceable reading pass; never edit sources."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "资料库" / "策略知识库" / "精编全量学习_20261011"
NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
GROUPS = {
    "01_账号与资源": [1, 5, 6, 7, 8, 9, 13, 16, 26, 39, 42, 45, 55, 56, 57, 60, 61],
    "02_机制与养成": [3, 10, 14, 15, 19, 25, 27, 29, 31, 32, 37, 38, 40, 46, 58, 62, 66],
    "03_体系与防守": [2, 4, 11, 12, 17, 18, 20, 21, 22, 23, 24, 28, 30, 33, 34],
    "04_输出与触发": [35, 36, 41, 43, 44, 47, 48, 49, 50, 51, 52, 53, 54, 59, 63, 64, 65, 67],
}


def paragraph_text(element: ET.Element) -> str:
    parts = []
    for node in element.iter():
        if node.tag == NS + "t":
            parts.append(node.text or "")
        elif node.tag == NS + "tab":
            parts.append("\t")
        elif node.tag in {NS + "br", NS + "cr"}:
            parts.append("\n")
    return "".join(parts)


def main() -> None:
    rows = json.loads((ROOT / "资料库" / "reports_index_rows.json").read_text(encoding="utf-8-sig"))
    assigned = [number for numbers in GROUPS.values() for number in numbers]
    actual = [int(row["no"]) for row in rows]
    if sorted(assigned) != sorted(actual) or len(set(assigned)) != len(assigned):
        raise ValueError("Study assignments must cover every indexed report exactly once")
    if (OUT / "阅读清单.json").exists():
        raise FileExistsError("Existing study manifest; preserve it instead of overwriting")

    records, texts = [], []
    for row in rows:
        source = (ROOT / row["rel"]).resolve()
        if not source.is_relative_to(ROOT.resolve()):
            raise ValueError(f"Source outside project: {row['no']}")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest != row["content_sha256"]:
            raise ValueError(f"Indexed DOCX changed: {row['no']}")
        with zipfile.ZipFile(source) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError(f"Corrupt DOCX member: {bad}")
            xml = ET.fromstring(archive.read("word/document.xml"))
            paragraphs = [paragraph_text(p) for p in xml.findall(".//" + NS + "p")]
            media = [name for name in archive.namelist() if name.startswith("word/media/")]
            sideparts = [
                name for name in archive.namelist()
                if name.startswith(("word/footnote", "word/endnote", "word/header", "word/footer"))
                and name.endswith(".xml")
            ]
        number = int(row["no"])
        group = next(name for name, numbers in GROUPS.items() if number in numbers)
        text_file = f"阅读材料/{row['no']}.txt"
        records.append({
            "no": row["no"], "title": row.get("report_heading") or row["title"],
            "rel": row["rel"], "source_sha256": digest, "text_file": text_file,
            "group": group, "paragraph_count": len(paragraphs),
            "nonempty_paragraphs": sum(bool(p.strip()) for p in paragraphs),
            "character_count": sum(len(p) for p in paragraphs),
            "table_count": len(xml.findall(".//" + NS + "tbl")),
            "media": media, "sideparts": sideparts,
            "saved_reliability_grade": row.get("reliability_grade"),
            "saved_p0_status": row.get("p0_audit_status"),
        })
        header = [f"报告 {row['no']}：{records[-1]['title']}", f"源文件：{row['rel']}",
                  f"SHA-256：{digest}", "P为原DOCX全部w:p的顺序编号，包含表格及空段；不是页码。", ""]
        body = [f"P{index:03d} {text}" for index, text in enumerate(paragraphs, 1) if text.strip()]
        texts.append((text_file, "\n".join(header + body) + "\n"))

    (OUT / "阅读材料").mkdir(parents=True, exist_ok=True)
    for name, content in texts:
        target = OUT / name
        if target.exists():
            raise FileExistsError(f"Do not overwrite reading material: {name}")
        target.write_text(content, encoding="utf-8")
    manifest = {
        "schema_version": 1, "study_date": "2026-10-11", "timezone": "Asia/Shanghai",
        "scope": "Active learning index only; three independent account reports excluded",
        "group_assignments": GROUPS, "source_count": len(records),
        "total_characters": sum(record["character_count"] for record in records),
        "total_nonempty_paragraphs": sum(record["nonempty_paragraphs"] for record in records),
        "records": records,
    }
    (OUT / "阅读清单.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"reports": len(records), "characters": manifest["total_characters"],
                      "media": sum(len(r["media"]) for r in records),
                      "sideparts": sum(len(r["sideparts"]) for r in records),
                      "groups": {key: len(value) for key, value in GROUPS.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
