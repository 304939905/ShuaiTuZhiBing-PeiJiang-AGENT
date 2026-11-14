#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""武将版本标签解析：禁止仅按姓名猜版本。

标签优先级：画面已确认的自带战法 > 完整卡面证据（阵营、总星数、SP/XP/无标识）>
版本待核实。仅“官方库同名唯一”或人工填写的标签都不构成版本证据。
星级使用 hero.json 中与 hero_id/skill_init 对应的记录；quality=6 按项目规则归为5星，"极"不是第6星。
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

LIB = Path(__file__).resolve().parent


def _load(name: str):
    return json.loads((LIB / name).read_text(encoding="utf-8"))


_extra = _load("hero_extra.json")
_hero = _load("hero.json")


def _aa_supplement_rows() -> list[dict]:
    """将经过精确关联的 AA 武将补充数据接入版本候选池。"""
    path = LIB / "aa_rate_supplement.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    converted = []
    for item in data.get("heroes", {}).values():
        name = str(item.get("name") or "").strip()
        skill = str(item.get("builtin_skill_name") or "").strip()
        country = str(item.get("country_name") or "").strip()
        arms = str(item.get("arms_name") or "").strip()
        if not (name and skill and country and arms):
            continue
        converted.append({
            "id": item.get("hero_id"),
            "name": name,
            "country": country,
            "type": arms,
            "methodId": item.get("skill_init"),
            "methodName": skill,
        })
    return converted


_extra = _extra + _aa_supplement_rows()
_COUNTRY_CODE = {"1": "汉", "2": "魏", "3": "蜀", "4": "吴", "5": "群", "6": "晋"}
_quality_by_id = {}
_quality_by_skill = defaultdict(set)
for row in _hero:
    hero_id = row.get("hero_id")
    skill_id = row.get("skill_init")
    try:
        quality = min(int(row.get("quality")), 5)
    except (TypeError, ValueError):
        continue
    if hero_id is not None:
        _quality_by_id[hero_id] = quality
    if skill_id is not None:
        _quality_by_skill[skill_id].add(quality)


def _label(row: dict) -> str | None:
    name = (row.get("name") or "").strip()
    country = (row.get("country") or "").strip()
    arms = (row.get("type") or "").strip()
    skill_id = row.get("methodId")
    star = _quality_by_id.get(row.get("id"))
    if star is None and skill_id is not None:
        values = _quality_by_skill.get(skill_id, set())
        if len(values) == 1:
            star = next(iter(values))
    if not name or not country or not arms or star is None:
        return None
    return f"{country}-{arms}-{star}星"


ROWS_BY_NAME: dict[str, list[dict]] = defaultdict(list)
ROWS_BY_NAME_SKILL: dict[tuple[str, str], list[dict]] = defaultdict(list)
for item in _extra:
    name = (item.get("name") or "").strip()
    skill = (item.get("methodName") or "").strip()
    if not name:
        continue
    ROWS_BY_NAME[name].append(item)
    if skill:
        ROWS_BY_NAME_SKILL[(name, skill)].append(item)

HERO_NAMES = set(ROWS_BY_NAME)
_STANDARD_LABEL = re.compile(r"^(汉|魏|蜀|吴|群|晋)-(骑|步|弓)-[345]星(?:\((?:SP|XP)\))?$")


def _unique_label(rows: list[dict]) -> str | None:
    labels = {_label(row) for row in rows}
    labels.discard(None)
    return next(iter(labels)) if len(labels) == 1 else None


def _builtin_label(row: dict) -> str | None:
    """自带战法对应的原始卡若本身是 XP/SP，标签中必须保留该版本标识。"""
    label = _label(row)
    if not label:
        return None
    direct_tags = {
        str(hero.get("season") or "").upper()
        for hero in _hero
        if hero.get("hero_id") == row.get("id") and str(hero.get("season") or "").upper() in {"SP", "XP"}
    }
    return f"{label}({next(iter(direct_tags))})" if len(direct_tags) == 1 else label


def _unique_builtin_label(rows: list[dict]) -> str | None:
    labels = {_builtin_label(row) for row in rows}
    labels.discard(None)
    return next(iter(labels)) if len(labels) == 1 else None


def _variant_tags(row: dict) -> set[str]:
    """返回该 hero_extra 记录可对应的卡面特殊标识。"""
    row_id = row.get("id")
    tags = set()
    direct = [hero for hero in _hero if hero.get("hero_id") == row_id]
    # 普通卡经常被 SP 卡以 base_hero_id/icon_hero_id 引用。若直接记录存在，
    # 只能读直接记录，否则会把普通卡错误标成 SP。
    candidates = direct or [
        hero for hero in _hero
        if row_id in {hero.get("icon_hero_id"), hero.get("base_hero_id")}
    ]
    for hero in candidates:
        season = str(hero.get("season") or "").upper()
        if season in {"SP", "XP"}:
            tags.add(season)
        elif str(hero.get("name") or "").strip() == (row.get("name") or "").strip():
            tags.add("NORMAL")
    return tags


def _visual_label(name: str, evidence: dict | None) -> str | None:
    """用已记录的同帧卡面五要素锁定；缺任一关键字段一律不推断。"""
    if not isinstance(evidence, dict) or not str(evidence.get("source_frame") or "").strip():
        return None
    country = str(evidence.get("country") or "").strip()
    try:
        star = int(evidence.get("star"))
    except (TypeError, ValueError):
        return None
    tag = str(evidence.get("variant") or evidence.get("tag") or "").strip().upper()
    tag = {"无": "NORMAL", "无标识": "NORMAL", "普通": "NORMAL", "NONE": "NORMAL"}.get(tag, tag)
    arms = str(evidence.get("arms") or evidence.get("type") or "").strip()
    if country not in _COUNTRY_CODE.values() or star not in {3, 4, 5} or tag not in {"NORMAL", "SP", "XP"}:
        return None
    if arms and arms not in {"弓", "步", "骑"}:
        return None

    labels = set()
    for row in ROWS_BY_NAME.get(name, []):
        label = _label(row)
        if not label or not label.startswith(f"{country}-") or not label.endswith(f"-{star}星"):
            continue
        if arms and not label.startswith(f"{country}-{arms}-"):
            continue
        if tag not in _variant_tags(row):
            continue
        labels.add(label if tag == "NORMAL" else f"{label}({tag})")
    return next(iter(labels)) if len(labels) == 1 else None


def _visual_builtin_label(rows: list[dict], evidence: dict | None) -> str | None:
    """同名同自带战法的普通/SP/XP 候选，必须用卡面标识（必要时兵种）消歧。"""
    if not isinstance(evidence, dict) or not str(evidence.get("source_frame") or "").strip():
        return None
    country = str(evidence.get("country") or "").strip()
    try:
        star = int(evidence.get("star"))
    except (TypeError, ValueError):
        return None
    tag = str(evidence.get("variant") or evidence.get("tag") or "").strip().upper()
    tag = {"无": "NORMAL", "无标识": "NORMAL", "普通": "NORMAL", "NONE": "NORMAL"}.get(tag, tag)
    arms = str(evidence.get("arms") or evidence.get("type") or "").strip()
    if country not in _COUNTRY_CODE.values() or star not in {3, 4, 5} or tag not in {"NORMAL", "SP", "XP"}:
        return None
    if arms and arms not in {"弓", "步", "骑"}:
        return None

    labels = set()
    for row in rows:
        base_label = _label(row)
        label = _builtin_label(row)
        if not base_label or not label:
            continue
        if not base_label.startswith(f"{country}-") or not base_label.endswith(f"-{star}星"):
            continue
        if arms and not base_label.startswith(f"{country}-{arms}-"):
            continue
        if tag in _variant_tags(row):
            labels.add(label)
    return next(iter(labels)) if len(labels) == 1 else None


def resolve_label(
    name: str,
    builtin_skill: str = "",
    explicit_label: str = "",
    star_override: str = "",
    visual_evidence: dict | None = None,
) -> str:
    """返回可溯源的唯一版本标签；否则返回“版本待核实”。"""
    name = (name or "").strip()
    builtin_skill = (builtin_skill or "").strip()
    explicit_label = (explicit_label or "").strip()
    rows = ROWS_BY_NAME.get(name, [])
    if not rows:
        return "版本待核实"
    if builtin_skill:
        candidates = ROWS_BY_NAME_SKILL.get((name, builtin_skill), [])
        label = _unique_builtin_label(candidates)
        if not label:
            label = _visual_builtin_label(candidates, visual_evidence)
        if label:
            if star_override and str(star_override).isdigit():
                label = re.sub(r"[45]星$", f"{int(star_override)}星", label)
            return label
        return "版本待核实"
    # explicit_label 只是历史字段，不可单独作为版本依据；必须重走卡面证据。
    return _visual_label(name, visual_evidence) or "版本待核实"
