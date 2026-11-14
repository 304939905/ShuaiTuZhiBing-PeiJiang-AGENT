#!/usr/bin/env python3
"""把硬规则检查与配将报告完整性检查合并为一次交付验收。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analyze_battle_reports import analyze as analyze_battles
from parse_account import build_profile
from validate_lineup import norm_id, validate


TEAM_FIELDS = {
    "core_logic": "核心逻辑",
    "speed_requirements": "速度要求",
    "strengths": "优势",
    "major_counters": "主要克制/被克制关系",
    "alternatives": "替代战法与代价",
    "awakening_cost": "觉醒成本",
    "dismantling_cost": "拆解成本",
    "resource_conflicts": "与其他队伍的资源冲突",
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _has_governance_content(value):
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(_has_governance_content(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_governance_content(item) for item in value)
    return False


def _governance_content(row):
    for field in ("plan", "details"):
        value = row.get(field)
        if isinstance(value, (str, dict, list)) and _has_governance_content(value):
            return value
    return None


def audit(profile, plan, battle_reports=None):
    hard = validate(profile, plan)
    errors, warnings = [], []
    teams = plan.get("teams", [])
    if plan.get("consultation_type") == "full_account":
        required_constraints = {
            "requested_main_teams": plan.get("requested_main_teams"),
            "cost_limit": plan.get("cost_limit"),
            "team_limit": plan.get("team_limit"),
            "awakening_resources.five_star_slots": (plan.get("awakening_resources") or {}).get("five_star_slots"),
        }
        for field, value in required_constraints.items():
            if value is None:
                errors.append({"code": "ACCOUNT_CONSTRAINT_MISSING", "field": field, "message": f"完整账号咨询缺少{field}，无法证明阵容符合本次账号约束"})
    requested_main = plan.get("requested_main_teams")
    if requested_main is not None:
        actual_main = sum(x.get("priority") == "主力" for x in teams)
        try:
            required = int(requested_main)
        except (TypeError, ValueError):
            required = -1
        if actual_main != required:
            errors.append({"code": "REQUESTED_MAIN_TEAMS_MISSING", "message": f"要求{requested_main}支主力，方案只标注{actual_main}支"})
    for index, team in enumerate(teams, 1):
        name = team.get("name") or f"第{index}队"
        for key, label in TEAM_FIELDS.items():
            if key not in team or team.get(key) in (None, "", []):
                errors.append({"code": "REPORT_FIELD_MISSING", "team": name, "field": key, "message": f"缺少{label}"})
        alternatives = team.get("alternatives")
        if isinstance(alternatives, list):
            for alternative in alternatives:
                if not isinstance(alternative, dict) or not alternative.get("replacement_cost"):
                    errors.append({"code": "ALTERNATIVE_COST_MISSING", "team": name, "message": "替代方案必须说明replacement_cost"})
        elif alternatives not in (None, "", []):
            errors.append({"code": "ALTERNATIVE_FORMAT", "team": name, "message": "alternatives应为对象列表，若无替代请写入说明对象"})
        for member in team.get("members", []):
            learned = member.get("learned_skills") or []
            if team.get("priority") == "主力" and len(learned) != 2:
                errors.append({"code": "MAIN_TACTICS_INCOMPLETE", "team": name, "message": "主力队每名武将必须给出完整的2个学习战法"})
            if team.get("priority") != "主力" and len(learned) < 2 and not member.get("incomplete_reason"):
                warnings.append({"code": "SECONDARY_TACTICS_INCOMPLETE", "team": name, "message": "非主力队战法未满，需说明incomplete_reason"})

    used_ids = {norm_id(m.get("hero_id")) for t in teams for m in t.get("members", []) if norm_id(m.get("hero_id")) is not None}
    reason_rows = {norm_id(x.get("hero_id")): x for x in plan.get("unused_five_star_reasons", []) if norm_id(x.get("hero_id")) is not None}
    for hero in profile.get("heroes", []):
        if hero.get("stars") == 5 and hero.get("id") not in used_ids:
            row = reason_rows.get(int(hero["id"]))
            if not row or not row.get("reason"):
                errors.append({
                    "code": "UNUSED_FIVE_STAR_UNEXPLAINED",
                    "hero_id": hero["id"],
                    "hero": hero.get("unique_name") or hero.get("name"),
                    "message": "未编队的5星武将必须说明未采用原因",
                })

    reviewed = {
        (x.get("code"), x.get("team"), x.get("message"))
        for x in plan.get("reviewed_warnings", [])
        if x.get("decision") and x.get("reason")
    }
    pending_warnings = [
        x for x in hard["warnings"]
        if (x.get("code"), x.get("team"), x.get("message")) not in reviewed
    ]
    if pending_warnings:
        warnings.append({"code": "WARNINGS_NOT_REVIEWED", "message": f"仍有{len(pending_warnings)}条硬规则警告未人工判断"})

    manual = hard.get("season_gate", {}).get("manual_checks", [])
    non_waivable = {"SKILL_TOTAL_UNKNOWN", "SKILL_AVAILABLE_UNKNOWN", "DISMANTLE_SPARE_UNKNOWN"}
    unresolved_resources = [x for x in hard["warnings"] if x.get("code") in non_waivable]
    lineup_ready = hard["passed"] and not errors and not warnings and not unresolved_resources and not manual

    governance = plan.get("governance_plans")
    if plan.get("consultation_type") == "full_account" and not governance:
        errors.append({"code": "GOVERNANCE_MISSING", "message": "完整账号咨询须在配将后给出两套施政方案"})
    if governance is not None and not isinstance(governance, list):
        errors.append({"code": "GOVERNANCE_FORMAT", "message": "governance_plans必须为施政方案对象列表"})
    elif governance:
        directions = {x.get("direction") for x in governance if isinstance(x, dict) and isinstance(x.get("direction"), str)}
        if len(governance) != 2 or "金币获取" not in directions or "自由建议" not in directions:
            errors.append({"code": "GOVERNANCE_FORMAT", "message": "施政必须恰好包含“金币获取”和“自由建议”两个方案"})
        for index, row in enumerate(governance, 1):
            if not isinstance(row, dict):
                errors.append({"code": "GOVERNANCE_FORMAT", "plan": index, "message": "每套施政方案必须为对象"})
                continue
            if _governance_content(row) is None:
                errors.append({"code": "GOVERNANCE_CONTENT_MISSING", "plan": index, "message": "施政方案必须在plan或details填写非空实际内容"})

    delivery_ready = lineup_ready and not errors
    return {
        "lineup_ready": lineup_ready,
        "delivery_ready": delivery_ready,
        "next_stage": "可以交付" if delivery_ready else "阵容已验收，下一步补施政两案" if lineup_ready and not governance else "先修正阵容/报告或完成必要核验",
        "lineup_validation": hard,
        "report_audit": {"errors": errors, "warnings": warnings},
        "unresolved_resources": unresolved_resources,
        "manual_checks": manual,
        "battle_feedback": analyze_battles(battle_reports) if battle_reports is not None else None,
        "workflow_order": [
            "读取本次账号与赛季",
            "建立不占用资源的候选池",
            "先为前三主力分配武将与核心战法",
            "再用剩余资源安排第四队以后",
            "执行全局合法性、冲突与报告完整性检查",
            "阵容通过后再安排施政",
        ],
    }


def _cell(value):
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    return str(value if value is not None else "—").replace("|", "\\|").replace("\n", " ")


def render_report(profile, plan, result):
    if not result["delivery_ready"]:
        raise ValueError("验收未通过，不生成正式咨询报告")
    heroes = {x["id"]: x for x in profile.get("heroes", [])}
    skills = {x["id"]: x for x in profile.get("skills", [])}
    season = plan.get("season") or profile.get("season", {}).get("label")
    lines = ["# 配将咨询报告", "", f"赛季：{season}。本报告只对本次账号数据和方案有效。", ""]
    if profile.get("source_modified_at"):
        lines.extend([f"账号导出文件修改时间：{profile['source_modified_at']}（UTC；仅表示文件时间，不保证账号资产未变化）。", ""])
    for team in sorted(plan.get("teams", []), key=lambda x: x.get("priority_rank", 999)):
        lines.extend([f"## {team.get('name') or '未命名队伍'}（{team.get('priority') or '补充队伍'}）", "",
                      "| 位置 | 武将版本 | 自带战法 | 学习战法1 | 学习战法2 |", "|---|---|---|---|---|"])
        for member in team.get("members", []):
            hero = heroes.get(norm_id(member.get("hero_id")), {})
            learned = member.get("learned_skills") or []
            names = []
            for ref in learned[:2]:
                skill_id = norm_id(ref.get("skill_id")) if isinstance(ref, dict) else norm_id(ref)
                names.append(skills.get(skill_id, {}).get("name") or str(skill_id or ref))
            while len(names) < 2:
                names.append("—")
            builtin = hero.get("builtin_skill") or {}
            lines.append("| " + " | ".join(map(_cell, [member.get("position"), hero.get("unique_name") or hero.get("name"), builtin.get("name"), *names])) + " |")
        lines.append("")
        for key, label in TEAM_FIELDS.items():
            lines.append(f"- {label}：{_cell(team.get(key))}")
        lines.append("")
    unused = plan.get("unused_five_star_reasons") or []
    if unused:
        lines.extend(["## 未上队的五星武将", ""])
        for row in unused:
            hero = heroes.get(norm_id(row.get("hero_id")), {})
            lines.append(f"- {hero.get('unique_name') or hero.get('name') or row.get('hero_id')}：{row.get('reason')}")
        lines.append("")
    governance = plan.get("governance_plans") or []
    if governance:
        lines.extend(["## 施政方案（阵容分配后）", ""])
        for row in governance:
            lines.append(f"- {row.get('direction')}：{_cell(_governance_content(row))}")
        lines.append("")
    feedback = result.get("battle_feedback")
    if feedback:
        lines.extend(["## 战报反馈（不以单场胜负改队）", ""])
        for team, row in feedback.get("teams", {}).items():
            evidence = row.get("evidence_status_counts") or {}
            basis = row.get("action_basis") or {}
            lines.append(
                f"- {team}：{row['sample_count']}份代表战报，其中{row['diagnostic_sample_count']}份含事件证据；"
                f"证据完整/部分/摘要={evidence.get('complete', 0)}/{evidence.get('partial', 0)}/{evidence.get('summary_only', 0)}；"
                f"前三回合爆头{len(row.get('early_headshots_round_1_to_3') or [])}份；"
                f"重复问题{_cell(row.get('repeated_issue_tags'))}。"
            )
            action_reasons = []
            if basis.get("confirmed_hard_fault"):
                action_reasons.append("已确认确定性硬错误")
            if basis.get("representative_sample"):
                action_reasons.append("代表样本达到门槛")
            lines.append(f"  - 调整依据：{'、'.join(action_reasons) if action_reasons else '证据尚不足，继续收集战报'}。")
            abnormal_events = row.get("first_abnormal_events") or {}
            if abnormal_events:
                lines.append(f"  - 首个异常事件：{_cell(abnormal_events)}。")
            observations = row.get("mechanism_observation_reports") or {}
            if observations:
                lines.append(f"  - 机制观察：{_cell(observations)}。")
            for fault in row.get("confirmed_hard_faults") or []:
                round_text = f"，第{fault['round']}回合" if fault.get("round") is not None else ""
                lines.append(
                    f"  - 已确认硬错误：{_cell(fault.get('category'))}"
                    f"（战报{_cell(fault.get('report'))}{round_text}）——{_cell(fault.get('evidence'))}"
                )
            for recommendation in row.get("recommendations", []):
                lines.append(f"  - 调整建议：{recommendation}")
        lines.append("")
    lines.extend(["## 证据边界", "", "- 账号导出事实：本次文件中的武将ID、觉醒字段、战法当前空闲份数；不等于当前实时资产保证。",
                  "- 资料库推定：战法可分配总份数按ID取自本地skill_extra.skillCount，不是账号导出直接提供的右值。",
                  "- 结构判断：队伍逻辑、速度需求、克制与替代，须结合当前战法文本和实战复核。"])
    if profile.get("gear_data_status") == "not_exposed":
        lines.append("- 宝物边界：本次文件未展示宝物，不能断定账号没有宝物。")
    elif profile.get("gear_data_status") == "empty_export":
        lines.append("- 宝物边界：本次文件的宝物记录为空；如需宝物建议，应另以当前页面核对。")
    if profile.get("skill_research_data_status") == "not_in_export":
        lines.append("- 研究状态：本次战法记录未单列研究进度，不能据此判断尚未研究战法的进度。")
    lines.extend(["- 待复核：" + ("；".join(_cell(x.get("message")) for x in result["lineup_validation"]["notes"]) or "本次无阻断项。"), ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path, help="脱敏档案；加--raw-account时可直接传百家社原始导出，只在内存解析")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--raw-account", action="store_true", help="输入是原始导出；不写出账号档案")
    parser.add_argument("--season-label", help="仅--raw-account时使用；需有用户提供的明确赛季")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--render-md", type=Path, help="验收通过后生成正式Markdown咨询报告")
    parser.add_argument("--battle-reports", type=Path, help="可选：结构化战报JSON；用于后续复盘，不影响初次配将的硬规则验收")
    args = parser.parse_args()
    profile = build_profile(args.profile, args.season_label) if args.raw_account else load(args.profile)
    result = audit(profile, load(args.plan), load(args.battle_reports) if args.battle_reports else None)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    if args.render_md and result["delivery_ready"]:
        args.render_md.parent.mkdir(parents=True, exist_ok=True)
        args.render_md.write_text(render_report(profile, load(args.plan), result), encoding="utf-8")
    print(text)
    return 0 if result["delivery_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
