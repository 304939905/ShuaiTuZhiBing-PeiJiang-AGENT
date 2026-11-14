#!/usr/bin/env python3
"""把百家社账号导出转换为不含登录信息的精简账号档案。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "资料库"

# 目前只把项目中已经用真实账号验证过的代码写成确定映射。
VERIFIED_SEASONS = {2002: "S2"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def unwrap_export(obj):
    if not isinstance(obj, dict):
        raise ValueError("导出文件顶层不是对象")
    if obj.get("error_code") not in (None, 0):
        raise ValueError(f"接口返回错误：error_code={obj.get('error_code')}")
    payload = obj.get("data", {}).get("data")
    if isinstance(payload, str):
        payload = json.loads(payload)
    if not isinstance(payload, dict) or not isinstance(payload.get("msg"), dict):
        raise ValueError("未找到 data.data.msg，百家社接口结构可能已经变化")
    # 当前真实导出以 code=200 表示成功；旧结构也可能省略或使用0。
    if payload.get("code") not in (None, 0, 200):
        raise ValueError(f"账号数据返回错误：code={payload.get('code')}")
    return payload["msg"]


def hero_stars(row, version_row):
    """仅用同一武将ID且自带战法一致的完整库记录判定星级。"""
    try:
        if int(row.get("methodId")) != int(version_row.get("skill_init")):
            return None
        stars = int(version_row.get("quality"))
        return stars if 2 <= stars <= 6 else None
    except (TypeError, ValueError):
        return None


def index_skill_rows(rows):
    """相同ID的完全重复行可折叠；不同内容不能静默取最后一行。"""
    indexed = {}
    for row in rows:
        if row.get("id") is None:
            continue
        skill_id = int(row["id"])
        if skill_id in indexed and indexed[skill_id] != row:
            raise ValueError(f"本地战法库ID {skill_id} 对应不同记录，须先核对资料库")
        indexed[skill_id] = row
    return indexed


def load_indexes():
    hero_extra = load_json(DB / "hero_extra.json")
    hero_raw = load_json(DB / "hero.json")
    skill_extra = load_json(DB / "skill_extra.json")
    skill_db = load_json(DB / "official_skill_db.json").get("skills", {})
    gear_rows = load_json(DB / "gear_id.json")

    heroes = {int(x["id"]): x for x in hero_extra if x.get("id") is not None}
    hero_versions = {
        int(x["hero_id"]): x for x in hero_raw if x.get("hero_id") is not None
    }
    skills = index_skill_rows(skill_extra)
    skill_meta = {
        int(x["id"]): x for x in skill_db.values() if x.get("id") is not None
    }
    gears = {int(x["id"]): x for x in gear_rows if x.get("id") is not None}
    return heroes, hero_versions, skills, skill_meta, gears


def version_tag(hero_version):
    if not hero_version:
        return None
    season = str(hero_version.get("season") or "").upper()
    if season in {"SP", "XP"}:
        return season
    if hero_version.get("is_sp_card") in (1, "1", True):
        return "SP"
    return "普通"


def parse_heroes(rows, heroes, hero_versions, skills, skill_meta):
    result, unknown, ignored = [], [], []
    for raw in rows or []:
        if not isinstance(raw, list) or not raw:
            unknown.append({"reason": "武将记录格式异常"})
            continue
        try:
            hero_id = int(raw[0])
        except (TypeError, ValueError):
            unknown.append({"reason": "武将ID无效"})
            continue
        db_row = heroes.get(hero_id)
        version_row = hero_versions.get(hero_id, {})
        if not db_row and version_row.get("name") == "侍卫":
            ignored.append({"hero_id": hero_id, "reason": "非可配将侍卫记录"})
            continue
        if not db_row:
            unknown.append({"hero_id": hero_id, "reason": "本地武将库未匹配"})
            continue
        builtin_id = db_row.get("methodId")
        stars = hero_stars(db_row, version_row)
        if stars is None:
            unknown.append({"hero_id": hero_id, "reason": "同ID武将库缺失或自带战法不一致，星级/版本未锁定"})
        builtin = skills.get(int(builtin_id)) if builtin_id not in (None, "") else None
        builtin_meta = skill_meta.get(int(builtin_id), {}) if builtin_id not in (None, "") else {}
        result.append(
            {
                "id": hero_id,
                "name": db_row.get("name"),
                "unique_name": db_row.get("uniqueName"),
                "faction": (db_row.get("uniqueName") or "--").split("-")[1]
                if (db_row.get("uniqueName") or "").count("-") >= 2
                else None,
                "troop_type": db_row.get("type"),
                "stars": stars,
                "star_source": "hero.json 同ID且skill_init=hero_extra.methodId" if stars is not None else None,
                "version_tag": version_tag(version_row) if stars is not None else None,
                "cost": float(db_row["cost"]) if db_row.get("cost") not in (None, "") else None,
                "attack_distance": db_row.get("distance"),
                "builtin_skill_id": db_row.get("methodId"),
                "builtin_skill": {
                    "id": int(builtin_id),
                    "name": builtin.get("name") if builtin else db_row.get("methodName"),
                    "type": builtin.get("type") if builtin else None,
                    "soldier_type": builtin.get("soldierType") if builtin else None,
                    "target": builtin.get("targetType") if builtin else None,
                    "distance": builtin.get("distance") if builtin else None,
                    "effect": builtin.get("effect") if builtin else builtin_meta.get("effect"),
                } if builtin_id not in (None, "") else None,
                "red": int(raw[1]) if len(raw) > 1 and str(raw[1]).isdigit() else None,
                "awakened": bool(raw[8]) if len(raw) > 8 else None,
            }
        )
    return result, unknown, ignored


def parse_skills(rows, skills, skill_meta):
    result, unknown = [], []
    for raw in rows or []:
        if not isinstance(raw, list) or not raw:
            unknown.append({"reason": "战法记录格式异常"})
            continue
        try:
            skill_id = int(raw[0])
        except (TypeError, ValueError):
            unknown.append({"reason": "战法ID无效"})
            continue
        db_row = skills.get(skill_id)
        meta = skill_meta.get(skill_id, {})
        if not db_row:
            unknown.append({"skill_id": skill_id, "reason": "本地战法库未匹配"})
            continue
        raw_flag = raw[1] if len(raw) > 1 else None
        # 百家社导出只提供左值（当前空闲份数）；右值暂按战法ID从本地库推定。
        # 用户确认 0/1 等比例的含义，0 绝不等于未拥有。
        try:
            available_copies = int(raw_flag)
            if available_copies < 0:
                available_copies = None
        except (TypeError, ValueError):
            available_copies = None
        try:
            total_copies = int(db_row.get("skillCount"))
            if total_copies <= 0:
                total_copies = None
        except (TypeError, ValueError):
            total_copies = None
        notice_match = re.search(r"可配置\s*(\d+)\s*个武将", str(db_row.get("notice") or ""))
        notice_copies = int(notice_match.group(1)) if notice_match else None
        if notice_copies is not None and notice_copies != total_copies:
            total_copies = None
            total_status = "db_notice_conflict"
        elif total_copies is None:
            total_status = "db_field_missing"
        else:
            total_status = "db_notice_agree" if notice_copies is not None else "db_field_only"
        assigned_copies = (
            total_copies - available_copies
            if total_copies is not None and available_copies is not None and available_copies <= total_copies
            else None
        )
        result.append(
            {
                "id": skill_id,
                "name": db_row.get("name"),
                "max_copies": total_copies,
                "total_copies": total_copies,
                "total_copies_source": "skill_extra.skillCount (按战法ID关联；非账号导出原字段)",
                "total_copies_status": total_status,
                "account_flag_raw": raw_flag,
                "owned": True,
                "available_copies": available_copies,
                "assigned_copies": assigned_copies,
                "availability_basis": "用户确认：左值为空闲份数，右值为总份数，差值为已分配份数；导出仅含左值",
                "type": db_row.get("type"),
                "soldier_type": db_row.get("soldierType"),
                "target": db_row.get("targetType"),
                "distance": db_row.get("distance"),
                "effect": db_row.get("effect"),
                "season_tag": meta.get("season_tag"),
                "acquisition_stage": meta.get("acquisition_stage"),
                "acquisition_stage_status": meta.get("acquisition_stage_status"),
            }
        )
    return result, unknown


def parse_gears(rows, gears):
    result, unknown = [], []
    for raw in rows or []:
        values = raw if isinstance(raw, list) else [raw]
        try:
            gear_id = int(values[0])
        except (IndexError, TypeError, ValueError):
            unknown.append({"reason": "宝物记录格式异常"})
            continue
        db_row = gears.get(gear_id)
        if not db_row:
            unknown.append({"gear_id": gear_id, "reason": "本地宝物库未匹配"})
            continue
        result.append({"id": gear_id, "name": db_row.get("name"), "quality": db_row.get("quality")})
    return result, unknown


def gear_export_status(msg):
    if msg.get("show_gear") is False and not msg.get("gear"):
        return "not_exposed"
    return "records_present" if msg.get("gear") else "empty_export"


def build_profile(source: Path, season_override=None):
    raw_bytes = source.read_bytes()
    msg = unwrap_export(json.loads(raw_bytes.decode("utf-8-sig")))
    heroes, hero_versions, skills, skill_meta, gears = load_indexes()
    hero_rows, unknown_heroes, ignored_heroes = parse_heroes(
        msg.get("hero"), heroes, hero_versions, skills, skill_meta
    )
    skill_rows, unknown_skills = parse_skills(msg.get("skill"), skills, skill_meta)
    skill_research_data_status = (
        "unparsed_extra_fields"
        if any(isinstance(row, list) and len(row) > 2 for row in msg.get("skill") or [])
        else "not_in_export"
    )
    gear_rows, unknown_gears = parse_gears(msg.get("gear"), gears)
    gear_data_status = gear_export_status(msg)
    season_code = msg.get("season")
    if season_override and season_code in VERIFIED_SEASONS and season_override != VERIFIED_SEASONS[season_code]:
        raise ValueError(
            f"用户指定赛季 {season_override} 与已验证的原始赛季代码 {season_code}"
            f"（{VERIFIED_SEASONS[season_code]}）冲突；请复核数据来源或更新映射"
        )
    season = season_override or VERIFIED_SEASONS.get(season_code)
    warnings = []
    if not season:
        warnings.append(f"赛季代码 {season_code!r} 尚无已验证映射，请用 --season-label 明确指定")
    if unknown_heroes:
        warnings.append(f"有 {len(unknown_heroes)} 条武将记录未匹配")
    if unknown_skills:
        warnings.append(f"有 {len(unknown_skills)} 条战法记录未匹配")
    if unknown_gears:
        warnings.append(f"有 {len(unknown_gears)} 条宝物记录未匹配")
    if gear_data_status == "not_exposed":
        warnings.append("本次导出 show_gear=false 且没有宝物记录；不能据此断定账号没有宝物")
    if skill_research_data_status == "unparsed_extra_fields":
        warnings.append("战法记录出现新的额外字段，研究状态等信息尚未解析；须先核对导出结构")
    unknown_skill_flags = [x for x in skill_rows if x.get("available_copies") is None]
    if unknown_skill_flags:
        warnings.append(f"有 {len(unknown_skill_flags)} 条战法的可用数量无法解析")
    inconsistent_skill_counts = [
        x for x in skill_rows
        if x.get("available_copies") is not None
        and x.get("total_copies") is not None
        and x["available_copies"] > x["total_copies"]
    ]
    if inconsistent_skill_counts:
        warnings.append(f"有 {len(inconsistent_skill_counts)} 条战法的导出空闲数大于资料库总份数，须逐项核对")
    conflicted_skill_totals = [x for x in skill_rows if x.get("total_copies_status") == "db_notice_conflict"]
    if conflicted_skill_totals:
        warnings.append(f"有 {len(conflicted_skill_totals)} 条战法的资料库总份数与说明文字冲突，已停止推定总份数")
    missing_skill_totals = [x for x in skill_rows if x.get("total_copies_status") == "db_field_missing"]
    if missing_skill_totals:
        warnings.append(f"有 {len(missing_skill_totals)} 条战法缺少可分配总份数，配将前须核对")
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_modified_at": datetime.fromtimestamp(source.stat().st_mtime, timezone.utc).isoformat(timespec="seconds"),
        "source_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "season": {"raw_code": season_code, "label": season, "status": "verified" if season_code in VERIFIED_SEASONS and not season_override else "user_override" if season_override else "unresolved"},
        "heroes": hero_rows,
        "skills": skill_rows,
        "gears": gear_rows,
        "gear_data_status": gear_data_status,
        "skill_research_data_status": skill_research_data_status,
        "unresolved": {"heroes": unknown_heroes, "skills": unknown_skills, "gears": unknown_gears},
        "ignored": {"heroes": ignored_heroes},
        "warnings": warnings,
        "summary": {
            "heroes": len(hero_rows),
            "five_star_heroes": sum(x.get("stars") == 5 for x in hero_rows),
            "awakened_five_star_heroes": sum(x.get("stars") == 5 and x.get("awakened") for x in hero_rows),
            "skills": len(skill_rows),
            "currently_available_skill_types": sum((x.get("available_copies") or 0) > 0 for x in skill_rows),
            "owned_but_zero_available_skill_types": sum(x.get("available_copies") == 0 for x in skill_rows),
            "total_copies_notice_agreed_types": sum(x.get("total_copies_status") == "db_notice_agree" for x in skill_rows),
            "total_copies_db_field_only_types": sum(x.get("total_copies_status") == "db_field_only" for x in skill_rows),
            "gears": len(gear_rows),
            "gear_data_status": gear_data_status,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="百家社导出的账号数据.json")
    parser.add_argument("output", type=Path, nargs="?", help="精简档案输出路径；不填则只检查并显示统计")
    parser.add_argument("--season-label", help="当原始赛季代码无法确认时，由用户明确提供，如 S1")
    args = parser.parse_args()
    try:
        profile = build_profile(args.input, args.season_label)
    except Exception as exc:
        print(f"解析失败：{exc}", file=sys.stderr)
        return 2
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已生成安全账号档案：{args.output}")
    else:
        print("检查通过；未写出账号档案。")
    print(json.dumps({"season": profile["season"], "summary": profile["summary"], "warnings": profile["warnings"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
