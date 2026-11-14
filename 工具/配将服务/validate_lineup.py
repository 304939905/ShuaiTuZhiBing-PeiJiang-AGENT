#!/usr/bin/env python3
"""对配将方案执行账号资源、觉醒、赛季、冲突和拆解影响检查。"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from season_gate import STAGE_ORDER, evaluate_requests, load_catalog


POSITION_DISTANCE = {"前锋": 1, "中军": 2, "大营": 3}
CONTINUOUS_EFFECTS = {"动摇", "恐慌", "妖术", "火攻", "休整", "持续性急救"}
GLOBAL_STATES = {"连击", "分兵", "规避"}
NON_STACK_EFFECTS = {
    "先攻", "先手", "援护", "洞察", "混乱", "犹豫", "暴走", "怯战", "挑衅",
    "攻击伤害提高", "攻击伤害降低", "策略攻击伤害提高", "策略攻击伤害降低",
    "受到攻击伤害提高", "受到攻击伤害降低", "受到策略攻击伤害提高", "受到策略攻击伤害降低",
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def norm_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def issue(bucket, code, message, team=None, **extra):
    item = {"code": code, "message": message}
    if team:
        item["team"] = team
    item.update(extra)
    bucket.append(item)


def skill_ref_id(skill_ref):
    if isinstance(skill_ref, dict):
        return norm_id(skill_ref.get("skill_id")), bool(skill_ref.get("core"))
    return norm_id(skill_ref), False


def normalize_effect(value):
    value = re.sub(r"[（(](预备|自身|设施)[）)]", "", str(value or "")).strip()
    return "持续性急救" if value == "持续型急救" else value


def split_effects(skill):
    return {normalize_effect(x) for x in str(skill.get("effect") or "").split(";") if normalize_effect(x)}


def conflict_kind(effect):
    if effect in CONTINUOUS_EFFECTS or re.search(r"(攻击|防御|谋略|速度|攻城)属性(提高|降低)$", effect):
        return "数值替换"
    if effect in GLOBAL_STATES or effect in NON_STACK_EFFECTS:
        return "不可叠加"
    return None


def targets_can_overlap(hero_a, skill_a, hero_b, skill_b):
    target_a = str(skill_a.get("target") or "")
    target_b = str(skill_b.get("target") or "")
    if "自己" in target_a and "自己" in target_b and hero_a.get("id") != hero_b.get("id"):
        return False
    a_enemy, b_enemy = "敌军" in target_a or "攻击目标" in target_a, "敌军" in target_b or "攻击目标" in target_b
    a_ally = any(x in target_a for x in ("我军", "友军", "自己"))
    b_ally = any(x in target_b for x in ("我军", "友军", "自己"))
    if (a_enemy and b_ally) or (b_enemy and a_ally):
        return False
    return True


def validate(profile, plan, catalog=None):
    errors, warnings, notes = [], [], []
    hero_rows, skill_rows = profile.get("heroes", []), profile.get("skills", [])
    heroes = {x["id"]: x for x in hero_rows}
    skills = {x["id"]: x for x in skill_rows}
    hero_names, skill_names = defaultdict(list), defaultdict(list)
    for row in hero_rows:
        hero_names[row.get("name")].append(row["id"])
    for row in skill_rows:
        skill_names[row.get("name")].append(row["id"])

    current_season = plan.get("season") or profile.get("season", {}).get("label")
    if not current_season:
        issue(errors, "SEASON_UNKNOWN", "当前赛季未确定，无法执行赛季门禁")
    elif plan.get("season") and profile.get("season", {}).get("label") and plan["season"] != profile["season"]["label"]:
        issue(errors, "SEASON_MISMATCH", f"方案赛季 {plan['season']} 与账号档案 {profile['season']['label']} 不一致")

    occupancy = plan.get("existing_occupancy") or {}
    used_heroes, used_skills = [], []
    for row in occupancy.get("heroes", []):
        hero_id = norm_id(row.get("hero_id"))
        if hero_id not in heroes:
            issue(errors, "HERO_OCCUPANCY_NOT_OWNED", f"保留旧队引用的武将ID {hero_id}不在本次账号档案")
            continue
        used_heroes.append((hero_id, row.get("team") or "现有队伍"))
    for row in occupancy.get("skills", []):
        skill_id = norm_id(row.get("skill_id"))
        if skill_id not in skills:
            issue(errors, "SKILL_OCCUPANCY_NOT_OWNED", f"保留旧队引用的战法ID {skill_id}不在本次账号档案")
            continue
        raw_copies = row.get("copies", 1)
        copies = (
            raw_copies if type(raw_copies) is int
            else int(raw_copies) if isinstance(raw_copies, str) and raw_copies.isdecimal()
            else 0
        )
        if copies <= 0:
            issue(errors, "OCCUPANCY_COPIES_INVALID", f"保留旧队的{skills[skill_id]['name']}占用份数必须为正整数")
            continue
        used_skills.extend([(skill_id, row.get("team") or "现有队伍", False, True)] * copies)

    team_summaries, rank_by_team = [], {}
    five_star_awakenings = four_star_awakenings = 0
    teams = plan.get("teams", [])
    main_ranks = []
    for team_index, team in enumerate(teams, 1):
        team_name = team.get("name") or f"第{team_index}队"
        try:
            rank = int(team.get("priority_rank", team_index))
        except (TypeError, ValueError):
            issue(errors, "PRIORITY_RANK", "priority_rank必须是正整数", team_name)
            rank = team_index
        if rank <= 0:
            issue(errors, "PRIORITY_RANK", "priority_rank必须是正整数", team_name)
        rank_by_team[team_name] = rank
        if team.get("priority") == "主力":
            main_ranks.append(rank)
            if rank not in {1, 2, 3}:
                issue(errors, "MAIN_PRIORITY", "主力队必须占用1至3的优先级", team_name)

        members = team.get("members") or []
        if len(members) != 3:
            issue(errors, "TEAM_SIZE", f"应为3名武将，当前为{len(members)}名", team_name)
        positions = [x.get("position") for x in members]
        if set(positions) != set(POSITION_DISTANCE) or len(positions) != len(set(positions)):
            issue(errors, "POSITIONS", "必须且只能各有一个大营、中军、前锋", team_name)
        cost_total, team_skill_rows, member_ids, speed_values = 0.0, [], [], {}
        for member in members:
            hero_id = norm_id(member.get("hero_id"))
            if hero_id is None and member.get("hero_name"):
                ids = hero_names.get(member["hero_name"], [])
                if len(ids) == 1:
                    hero_id = ids[0]
                else:
                    issue(errors, "HERO_NAME_AMBIGUOUS", f"武将名“{member['hero_name']}”匹配{len(ids)}个版本，请改用hero_id", team_name)
                    continue
            hero = heroes.get(hero_id)
            if not hero:
                issue(errors, "HERO_NOT_OWNED", f"账号档案中没有武将ID {hero_id}", team_name)
                continue
            if hero.get("stars") is None or ("version_tag" in hero and hero["version_tag"] is None):
                issue(errors, "HERO_VERSION_UNRESOLVED", f"{hero.get('name') or hero_id}的星级或版本未通过同ID自带战法核验", team_name)
            used_heroes.append((hero_id, team_name))
            member_ids.append(hero_id)
            cost_total += float(hero.get("cost") or 0)
            learned = member.get("learned_skills") or []
            if len(learned) > 2:
                issue(errors, "SKILL_SLOTS", f"{hero['unique_name']}最多只能配置2个学习战法", team_name)
            if len(learned) > (2 if hero.get("awakened") else 1):
                if member.get("will_awaken") and len(learned) <= 2:
                    if hero.get("stars") == 5:
                        five_star_awakenings += 1
                    elif hero.get("stars") == 4:
                        four_star_awakenings += 1
                    else:
                        issue(errors, "AWAKENING_UNSUPPORTED", f"{hero['unique_name']}星级无法按当前规则核算觉醒资源", team_name)
                else:
                    issue(errors, "AWAKENING_SLOT", f"{hero['unique_name']}未觉醒，却配置了2个学习战法且未声明will_awaken", team_name)
            if member.get("speed") is not None:
                speed_values[hero_id] = float(member["speed"])
            builtin = hero.get("builtin_skill")
            if isinstance(builtin, dict) and builtin.get("id"):
                team_skill_rows.append((hero, member.get("position"), builtin, "自带"))
            for skill_ref in learned:
                skill_id, core = skill_ref_id(skill_ref)
                if skill_id is None and isinstance(skill_ref, str):
                    ids = skill_names.get(skill_ref, [])
                    if len(ids) == 1:
                        skill_id = ids[0]
                    else:
                        issue(errors, "SKILL_NAME_AMBIGUOUS", f"战法名“{skill_ref}”匹配{len(ids)}条账号记录，请改用战法ID", team_name)
                        continue
                skill = skills.get(skill_id)
                if not skill:
                    issue(errors, "SKILL_NOT_OWNED", f"账号档案中没有战法ID {skill_id}", team_name)
                    continue
                used_skills.append((skill_id, team_name, core, False))
                team_skill_rows.append((hero, member.get("position"), skill, "学习"))
                soldier = str(skill.get("soldier_type") or "")
                if soldier and hero.get("troop_type") and hero["troop_type"] not in soldier:
                    issue(errors, "TROOP_RESTRICTION", f"{hero['unique_name']}不能学习{skill['name']}：兵种限制为{soldier}", team_name)
                target, distance = str(skill.get("target") or ""), skill.get("distance")
                minimum = POSITION_DISTANCE.get(member.get("position"))
                if not target:
                    issue(warnings, "TARGET_METADATA_MISSING", f"{skill['name']}缺少目标类型，需读取当前战法文本复核", team_name)
                if "敌军" in target and not isinstance(distance, (int, float)):
                    issue(warnings, "SKILL_DISTANCE_MISSING", f"{skill['name']}缺少有效距离，无法验证站位", team_name)
                elif "敌军" in target and minimum and distance < minimum:
                    issue(errors, "SKILL_RANGE", f"{hero['unique_name']}位于{member.get('position')}，{skill['name']}距离{distance}不足以触及敌军前锋", team_name)
                if skill.get("acquisition_stage_status") == "provisional_default":
                    issue(notes, "OWNED_SEASON_PROVISIONAL", f"{skill['name']}已在账号档案中，允许继续使用；其新获取阶段仍为暂定值", team_name)
                stage = skill.get("acquisition_stage")
                if current_season in STAGE_ORDER and stage in STAGE_ORDER and STAGE_ORDER[stage] > STAGE_ORDER[current_season]:
                    issue(warnings, "OWNED_LATER_STAGE", f"{skill['name']}显示已拥有，但本地新获取阶段为{stage}、当前赛季为{current_season}；使用本身不受阻，仍需核对赛季或资产来源", team_name)
            normal_range, minimum = hero.get("attack_distance"), POSITION_DISTANCE.get(member.get("position"))
            if isinstance(normal_range, (int, float)) and minimum and normal_range < minimum:
                issue(warnings, "NORMAL_ATTACK_RANGE", f"{hero['unique_name']}位于{member.get('position')}时普通攻击距离不足；若依赖普攻/追击需调整", team_name)

        max_cost = plan.get("cost_limit")
        if max_cost is not None and cost_total > float(max_cost):
            issue(errors, "COST_LIMIT", f"总COST {cost_total:g} 超过上限 {max_cost}", team_name)
        for i, (a_hero, _, a, a_source) in enumerate(team_skill_rows):
            for b_hero, _, b, b_source in team_skill_rows[i + 1:]:
                if not targets_can_overlap(a_hero, a, b_hero, b):
                    continue
                for effect in sorted(split_effects(a) & split_effects(b)):
                    kind = conflict_kind(effect)
                    same_type = a.get("type") == b.get("type") and a.get("type")
                    if kind and (same_type or effect in GLOBAL_STATES):
                        code = "EFFECT_VALUE_REPLACEMENT" if kind == "数值替换" else "EFFECT_NON_STACK"
                        issue(warnings, code, f"{a['name']}（{a_source}）与{b['name']}（{b_source}）的“{effect}”存在{kind}风险；须保留独立副效果后再决定是否替换", team_name, effect=effect)

        speed_order = [norm_id(x) for x in team.get("speed_order", [])]
        if speed_order:
            if any(x not in member_ids for x in speed_order) or len(speed_order) != len(set(speed_order)):
                issue(errors, "SPEED_ORDER_MEMBERS", "speed_order必须只包含本队武将且不能重复", team_name)
            elif not all(x in speed_values for x in speed_order):
                issue(warnings, "SPEED_UNVERIFIED", "填写了行动顺序要求，但没有完整speed数值，无法验证", team_name)
            elif any(speed_values[speed_order[i]] <= speed_values[speed_order[i + 1]] for i in range(len(speed_order) - 1)):
                issue(errors, "SPEED_ORDER", "实际speed数值不满足speed_order从快到慢的要求", team_name)
        team_summaries.append({"name": team_name, "priority": team.get("priority"), "priority_rank": rank, "cost": cost_total, "heroes": len(member_ids), "learned_skills": sum(x[3] == "学习" for x in team_skill_rows)})

    if len(main_ranks) > 3:
        issue(errors, "MAIN_TEAM_COUNT", f"标为主力的队伍有{len(main_ranks)}支，超过最多3支")
    if len(main_ranks) != len(set(main_ranks)):
        issue(errors, "MAIN_PRIORITY_DUPLICATE", "主力队priority_rank不能重复")
    if len(rank_by_team) != len(teams) or len(set(rank_by_team.values())) != len(rank_by_team):
        issue(errors, "TEAM_PRIORITY_DUPLICATE", "队伍名称与priority_rank均须唯一")
    if main_ranks and sorted(main_ranks) != list(range(1, len(main_ranks) + 1)):
        issue(errors, "MAIN_PRIORITY_GAP", "主力队优先级必须从1连续排列，才能保证先分配资源")
    team_limit = plan.get("team_limit")
    if team_limit is not None and len(teams) > int(team_limit):
        issue(errors, "TEAM_LIMIT", f"方案有{len(teams)}支队伍，超过本次上限{team_limit}")

    awakening = plan.get("awakening_resources") or {}
    available_five = int(awakening.get("five_star_slots") or 0)
    if five_star_awakenings > available_five:
        issue(errors, "FIVE_STAR_AWAKENING_BUDGET", f"方案需要{five_star_awakenings}个5星觉醒名额，当前只声明{available_five}个")
    if four_star_awakenings and not awakening.get("four_star_unlimited"):
        issue(warnings, "FOUR_STAR_AWAKENING_BUDGET", f"方案需要觉醒{four_star_awakenings}名4星武将，但未声明4星觉醒资源充足")

    hero_usage = defaultdict(list)
    for hero_id, team_name in used_heroes:
        hero_usage[hero_id].append(team_name)
    for hero_id, team_names in hero_usage.items():
        if len(team_names) > 1:
            name = heroes.get(hero_id, {}).get("unique_name") or f"武将ID {hero_id}"
            issue(errors, "HERO_DUPLICATE", f"{name}被重复占用：{'、'.join(team_names)}")
    skill_usage = defaultdict(list)
    for skill_id, team_name, core, existing in used_skills:
        skill_usage[skill_id].append((team_name, core, existing))
    if plan.get("reallocated_skill_copies"):
        issue(notes, "SKILL_RELEASE_LEGACY_IGNORED", "旧版reallocated_skill_copies不再用于计算；未列入existing_occupancy的旧队战法按可收回处理")
    for skill_id, refs in skill_usage.items():
        skill = skills.get(skill_id, {})
        total = skill.get("max_copies_override", skill.get("total_copies", skill.get("max_copies")))
        available = skill.get("available_copies")
        preserved = sum(ref[2] for ref in refs)
        new_assignments = len(refs) - preserved
        if not isinstance(total, int) or total <= 0:
            issue(warnings, "SKILL_TOTAL_UNKNOWN", f"{skill.get('name') or skill_id}可分配总份数未知，无法完成全局战法数量验收")
        if isinstance(total, int) and isinstance(available, int) and not 0 <= available <= total:
            issue(errors, "SKILL_COUNT_INCONSISTENT", f"{skill.get('name') or skill_id}空闲{available}份、总份数{total}份，数量关系不成立；须核对账号页面")
        if isinstance(total, int) and len(refs) > total:
            refs_sorted = sorted(refs, key=lambda x: rank_by_team.get(x[0], 999))
            lower = refs_sorted[total:]
            issue(errors, "SKILL_COUNT", f"{skill.get('name') or skill_id}保留旧队加新编队共使用{len(refs)}份，超过总份数{total}份；应先保障高优先级主力，需释放：{'、'.join(x[0] for x in lower)}")
        if isinstance(available, int) and isinstance(total, int) and 0 <= available <= total:
            previously_assigned = total - available
            if preserved > previously_assigned:
                issue(errors, "SKILL_PRESERVED_COUNT", f"{skill.get('name') or skill_id}声明保留旧队{preserved}份，但当前已分配仅{previously_assigned}份")
            reclaim_needed = max(0, new_assignments - available)
            reclaimable = max(0, previously_assigned - preserved)
            if reclaim_needed > reclaimable and not (isinstance(total, int) and len(refs) > total):
                issue(errors, "SKILL_COUNT", f"{skill.get('name') or skill_id}新编队还需回收{reclaim_needed}份，未保留旧队最多可回收{reclaimable}份")
            elif reclaim_needed:
                issue(notes, "SKILL_REALLOCATION", f"{skill.get('name') or skill_id}当前空闲{available}/{total}；新方案须从不保留的旧队收回{reclaim_needed}份")
        elif "available_copies" in skill and not isinstance(available, int):
            issue(warnings, "SKILL_AVAILABLE_UNKNOWN", f"{skill.get('name') or skill_id}当前可用数量未知，需核实")

    for row in plan.get("planned_dismantles", []):
        hero_id = norm_id(row.get("hero_id"))
        hero = heroes.get(hero_id)
        if not hero:
            issue(errors, "DISMANTLE_NOT_OWNED", f"计划拆解的武将ID {hero_id}不在账号档案")
            continue
        needed, spare = int(row.get("count") or 1), hero.get("spare_copies")
        if hero_id in hero_usage and (spare is None or spare < needed):
            issue(errors, "DISMANTLE_IN_USE", f"{hero['unique_name']}同时被编队和计划拆解，且没有已核实的足量副卡")
        if spare is None:
            issue(warnings, "DISMANTLE_SPARE_UNKNOWN", f"{hero['unique_name']}缺少闲置副卡数量，不能证明拆解后仍保留本体/觉醒选择")
        elif spare < needed:
            issue(errors, "DISMANTLE_SPARE_SHORTAGE", f"{hero['unique_name']}计划拆{needed}张，但闲置副卡只有{spare}张")
        if hero.get("stars") == 5:
            issue(warnings, "DISMANTLE_FIVE_STAR_COST", f"拆解5星{hero['unique_name']}会消耗觉醒/进阶资源，正式报告必须列明机会成本")

    owned_skill_ids = set(skills)
    requests = [{**x, "purpose": "acquire"} for x in plan.get("planned_acquisitions", [])]
    requests += [{**x, "purpose": "counter"} for x in plan.get("counter_tactics", [])]
    season_result = evaluate_requests(requests, current_season, owned_skill_ids, catalog if catalog is not None else load_catalog())
    for row in season_result["results"]:
        if row.get("purpose") == "acquire" and row.get("allowed") is not True:
            issue(errors, "SEASON_ACQUISITION_BLOCKED", f"不能把{row['name']}写成当前可获取方案：{row['reason']}")
        elif row.get("purpose") == "counter" and row.get("allowed") is False:
            issue(notes, "COUNTER_FILTERED_BY_SEASON", f"当前环境分析已排除{row['name']}：{row['reason']}")
        elif row.get("owned") and row.get("acquisition_stage"):
            issue(notes, "OWNED_CROSS_SEASON_USABLE", f"{row['name']}已拥有，可在{current_season}继续使用；获取阶段不构成使用限制")

    return {
        "passed": not errors,
        "summary": {"teams": len(teams), "errors": len(errors), "warnings": len(warnings), "notes": len(notes)},
        "resource_summary": {
            "five_star_awakenings_required": five_star_awakenings,
            "five_star_awakenings_available": available_five,
            "four_star_awakenings_required": four_star_awakenings,
            "main_team_priority_order": [x["name"] for x in sorted(team_summaries, key=lambda x: x["priority_rank"]) if x["priority"] == "主力"],
        },
        "season_gate": season_result,
        "team_summary": team_summaries,
        "errors": errors,
        "warnings": warnings,
        "notes": notes,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(load(args.profile), load(args.plan))
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"检查结果已写入：{args.output}")
    print(text)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
