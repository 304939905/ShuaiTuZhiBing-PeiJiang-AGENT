#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从 AA率土/率土之滨数据库.xlsx 生成可安全叠加的权威补充层。

不改写 hero.json、hero_extra.json、skill_extra.json：它们仍是旧报告的原始
证据。补充层仅收录能与现有武将/战法库精确关联的数据，并保留未分类原始
记录的数量，避免把外观、兵书或系统战法误当成可配将资源。
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook


BASE = Path(__file__).resolve().parent
SOURCE = BASE.parent / "AA率土" / "率土之滨数据库.xlsx"
OUTPUT = BASE / "aa_rate_supplement.json"

COUNTRY = {1: "汉", 2: "魏", 3: "蜀", 4: "吴", 5: "群", 6: "晋"}
ARMS = {1: "弓", 2: "步", 3: "骑"}
TYPE = {1: "被动", 2: "指挥", 3: "主动", 4: "追击", 13: "被动"}


def load_json(name: str):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def rows(workbook, name: str) -> list[dict]:
    sheet = workbook[name]
    iterator = sheet.iter_rows(values_only=True)
    headers = list(next(iterator))
    return [dict(zip(headers, row)) for row in iterator]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def serializable(row: dict) -> dict:
    return {key: value for key, value in row.items() if value is not None}


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"缺少权威源文件：{SOURCE}")

    hero_legacy = load_json("hero.json")
    hero_extra = load_json("hero_extra.json")
    skill_extra = load_json("skill_extra.json")
    skill_db = load_json("official_skill_db.json")

    workbook = load_workbook(SOURCE, read_only=True, data_only=True)
    hero_raw = rows(workbook, "武将库")
    skill_raw = rows(workbook, "战法库")
    effect_raw = rows(workbook, "战法效果明细")
    state_raw = rows(workbook, "状态效果")

    old_heroes = {int(item["hero_id"]): item for item in hero_legacy if item.get("hero_id") is not None}
    skills_by_id = {int(item["skill_id"]): item for item in skill_raw if item.get("skill_id") is not None}
    skills_by_name: dict[str, list[dict]] = {}
    for item in skill_raw:
        name = str(item.get("name") or "").strip()
        if name:
            skills_by_name.setdefault(name, []).append(item)

    hero_details: dict[str, dict] = {}
    raw_hero_ids = set()
    non_hero_book_rows = 0
    for item in hero_raw:
        hero_id = int(item["heroid"])
        raw_hero_ids.add(hero_id)
        # book_type 非零是兵书/战法书配置，不能与可上阵武将混入同一资产层。
        if int(item.get("book_type") or 0) != 0:
            non_hero_book_rows += 1
            continue
        legacy = old_heroes.get(hero_id)
        if legacy is None:
            continue
        record = serializable(item)
        record.update(
            {
                "hero_id": hero_id,
                "country_name": COUNTRY.get(item.get("country"), ""),
                "arms_name": ARMS.get(item.get("hero_type"), ""),
                # AA quality is one lower than hero.json's star code on all shared IDs.
                "star": min(int(item["quality"]) + 1, 5),
                "legacy_season": legacy.get("season", ""),
                "builtin_skill_name": skills_by_id.get(int(item["skill_init"]), {}).get("name", ""),
                "source": "AA率土/率土之滨数据库.xlsx::武将库",
            }
        )
        hero_details[str(hero_id)] = record

    known_skill_ids = {int(item["id"]) for item in skill_extra if item.get("id") is not None}
    for item in hero_legacy:
        if item.get("skill_init") is not None:
            known_skill_ids.add(int(item["skill_init"]))
    for item in hero_extra:
        for key in ("methodId", "methodId1", "methodId2"):
            value = item.get(key)
            if value not in (None, ""):
                known_skill_ids.add(int(value))
    for name in skill_db.get("skills", {}):
        known_skill_ids.update(int(item["skill_id"]) for item in skills_by_name.get(name, []))

    effects_by_skill: dict[int, list[dict]] = {}
    for effect in effect_raw:
        detail_id = effect.get("detail_id")
        if detail_id is None:
            continue
        skill_id = int(detail_id) // 100
        effects_by_skill.setdefault(skill_id, []).append(serializable(effect))
    states = {str(item["effect_id"]): serializable(item) for item in state_raw if item.get("effect_id") is not None}

    skill_details: dict[str, dict] = {}
    missing_detail_ids: list[int] = []
    for skill_id in sorted(known_skill_ids & set(skills_by_id)):
        item = skills_by_id[skill_id]
        record = serializable(item)
        detail_rows = effects_by_skill.get(skill_id, [])
        if item.get("main_detail") and not detail_rows:
            missing_detail_ids.append(skill_id)
        record.update(
            {
                "skill_id": skill_id,
                "type_name": TYPE.get(item.get("skill_type"), ""),
                "effect_details": detail_rows,
                "source": "AA率土/率土之滨数据库.xlsx::战法库+战法效果明细",
            }
        )
        skill_details[str(skill_id)] = record

    output = {
        "meta": {
            "source": str(SOURCE.relative_to(BASE.parent)).replace("\\", "/"),
            "source_sha256": sha256(SOURCE),
            "source_workbook_created": str(workbook.properties.created or ""),
            "source_workbook_modified": str(workbook.properties.modified or ""),
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "merge_policy": "仅收录与现有本地武将/战法库精确关联的条目；不把未分类原始配置当作可配将资源。",
            "quality_mapping": "AA 武将 quality + 1 = 项目星级；quality=5 按项目规则归为5星。",
        },
        "heroes": hero_details,
        "skills": skill_details,
        "states": states,
        "coverage": {
            "raw_hero_rows": len(hero_raw),
            "raw_nonhero_book_rows_excluded": non_hero_book_rows,
            "hero_rows_linked_to_hero_json": len(hero_details),
            "hero_json_rows_not_in_aa": sorted(set(old_heroes) - raw_hero_ids),
            "raw_hero_rows_not_merged": len(hero_raw) - len(hero_details),
            "raw_skill_rows": len(skill_raw),
            "skill_rows_linked_to_existing_library": len(skill_details),
            "raw_skill_rows_not_merged": len(skill_raw) - len(skill_details),
            "effect_rows": len(effect_raw),
            "states": len(states),
            "linked_skills_missing_effect_detail": missing_detail_ids,
        },
    }
    # 补充库是机器读取数据；紧凑JSON可无损减少约三分之一体积。
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(
        "aa_rate_supplement.json -> "
        f"heroes={len(hero_details)}, skills={len(skill_details)}, states={len(states)}, "
        f"missing_effect_detail={len(missing_detail_ids)}"
    )


if __name__ == "__main__":
    main()
