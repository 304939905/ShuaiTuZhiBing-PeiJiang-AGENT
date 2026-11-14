# -*- coding: utf-8 -*-
"""只读扫描：用母本「武将名 + 自带战法」复核成品中同名武将的版本标签。

输出的是待复核候选，不直接修改历史报告：同一报告中可能会同时谈到推荐队、
对手队或替代队，需结合画面与语境定案。
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from docx import Document
from hero_version_resolver import resolve_label


ROOT = Path(r"D:/Desktop/shandou")
LIB = ROOT / "资料库"
SOURCE_DIRS = [LIB / "frame_json", LIB / "hzh_frame_json", LIB / "saiji_frame_json", LIB / "frame_json_kaihuang"]
DOCS = list((ROOT / "报告库").rglob("*.docx"))
LABEL = re.compile(r"([\u4e00-\u9fff]{1,8})（([^-（）\n]{1,4})-([^-（）\n]{1,4})-([45]星)）")


def candidate_docs(title: str) -> list[Path]:
    return [path for path in DOCS if title in path.name and "精修" in path.name]


def hero_skills(data: dict) -> dict[str, set[str]]:
    heroes = ((data.get("entities") or {}).get("heroes") or [])
    result: dict[str, set[str]] = defaultdict(set)
    for hero in heroes:
        if not isinstance(hero, dict):
            continue
        name = str(hero.get("name") or "").strip()
        innate = str(hero.get("built_in_skill") or hero.get("method_name") or "").strip()
        if name and innate:
            result[name].add(innate)
    for team in ((data.get("entities") or {}).get("teams") or []):
        for pos in (team.get("positions") or []):
            name = str(pos.get("hero") or "").strip()
            skills = pos.get("skills") or []
            if name and skills and str(skills[0]).strip():
                result[name].add(str(skills[0]).strip())
    return result


def scan() -> list[dict]:
    findings = []
    for directory in SOURCE_DIRS:
        for source in sorted(directory.glob("*.json")):
            try:
                data = json.loads(source.read_text(encoding="utf-8"))
            except Exception:
                continue
            title = str(data.get("video_title") or source.stem)
            docs = candidate_docs(title)
            if not docs:
                continue
            for name, skills in hero_skills(data).items():
                expected = {resolve_label(name, skill) for skill in skills}
                expected.discard("版本待核实")
                if len(expected) != 1:
                    continue
                expected_label = expected.pop()
                for doc in docs:
                    text = "\n".join(p.text for p in Document(doc).paragraphs)
                    actual = {f"{m.group(2)}-{m.group(3)}-{m.group(4)}" for m in LABEL.finditer(text) if m.group(1) == name}
                    mismatch = sorted(label for label in actual if label != expected_label)
                    if mismatch:
                        findings.append({
                            "source": source.name,
                            "report": str(doc.relative_to(ROOT)),
                            "hero": name,
                            "innate_skills": sorted(skills),
                            "expected": expected_label,
                            "actual_labels": sorted(actual),
                            "mismatch": mismatch,
                        })
    return findings


def scan_index_risks() -> list[dict]:
    """没有结构化母本时的保守风险清单：只找精编首页的多版本标签。

    这不是错误判定；后续必须回到对应视频帧与自带战法再定案。
    """
    risks = []
    for doc in DOCS:
        if "精编" not in doc.parts:
            continue
        paragraphs = Document(doc).paragraphs[:12]
        text = "\n".join(p.text for p in paragraphs)
        labels = defaultdict(set)
        for m in LABEL.finditer(text):
            labels[m.group(1)].add(f"{m.group(2)}-{m.group(3)}-{m.group(4)}")
        for name, actual in labels.items():
            if resolve_label(name) == "版本待核实":
                risks.append({
                    "report": str(doc.relative_to(ROOT)),
                    "hero": name,
                    "actual_labels": sorted(actual),
                    "reason": "同名存在多版本；首页标签缺少自带战法证据链，需回帧复核",
                })
    return risks


if __name__ == "__main__":
    direct = scan()
    risks = scan_index_risks()
    print(json.dumps({"direct_mismatch": direct, "index_risks": risks}, ensure_ascii=False, indent=2))
    print(f"DIRECT_MISMATCH_COUNT={len(direct)}")
    print(f"INDEX_RISK_COUNT={len(risks)}")
