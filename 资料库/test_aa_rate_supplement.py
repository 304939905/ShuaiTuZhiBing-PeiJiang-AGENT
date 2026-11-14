#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""AA率土补充层的轻量完整性检查。"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


BASE = Path(__file__).resolve().parent
SOURCE = BASE.parent / "AA率土" / "率土之滨数据库.xlsx"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def load(name: str):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


data = load("aa_rate_supplement.json")
hero_ids = {str(item["hero_id"]) for item in load("hero.json")}
skill_ids = {str(item["id"]) for item in load("skill_extra.json")}

stored_source_hash = data["meta"].get("source_sha256", "")
assert len(stored_source_hash) == 64 and all(ch in "0123456789abcdef" for ch in stored_source_hash.lower()), "补充库缺少有效的源文件哈希"
if SOURCE.exists():
    assert stored_source_hash == digest(SOURCE), "源 Excel 已变更，请先重新执行同步脚本"
else:
    # 项目已进入源材料退役模式：原始 Excel 不再是运行时依赖。
    # 仍保留当时的来源哈希，并继续执行下方结构与覆盖范围检查。
    assert data["meta"].get("source"), "源文件已退役，但补充库缺少来源说明"
assert set(data["heroes"]).issubset(hero_ids), "补充武将包含未精确关联的 ID"
assert data["coverage"]["raw_nonhero_book_rows_excluded"] == 932, "兵书/战法书排除数异常"
assert all(int(item.get("book_type", 0)) == 0 for item in data["heroes"].values()), "补充武将混入非武将记录"
assert skill_ids.issubset(set(data["skills"])), "现有可配战法未被完整补充"
assert len(data["states"]) == 206, "状态效果记录数异常"
assert set(data["coverage"]["linked_skills_missing_effect_detail"]) == {202097, 202098, 202099}
print("aa_rate_supplement: PASS" + (" (source-retired mode)" if not SOURCE.exists() else ""))
