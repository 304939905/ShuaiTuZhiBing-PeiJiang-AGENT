#!/usr/bin/env python3
"""按证据质量与机制事件汇总战报，形成可复核的配将反馈。"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


REQUIRED = {"id", "team", "opponent_archetype", "result", "rounds", "action_order", "main_damage_source", "diagnosis_tags"}
EVIDENCE_STATUSES = {"complete", "partial", "summary_only"}
OBSERVATION_CONFIDENCE = {"confirmed", "probable", "unknown"}
STANDARD_CATEGORIES = {
    "行动顺序", "触发前提", "目标或距离", "战法冲突", "控制链", "增减伤通道",
    "输出结构", "生存保护", "恢复链", "兵种相克", "兵力衰减", "随机波动", "其他",
}
DETERMINISTIC_CATEGORIES = {"行动顺序", "触发前提", "目标或距离", "战法冲突"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _validate_observations(row):
    observations = row.get("mechanism_observations") or []
    if not isinstance(observations, list):
        return False
    for item in observations:
        if not isinstance(item, dict):
            return False
        if not isinstance(item.get("category"), str) or not item["category"].strip():
            return False
        if not isinstance(item.get("evidence"), str) or not item["evidence"].strip():
            return False
        if item.get("confidence") not in OBSERVATION_CONFIDENCE:
            return False
        event_round = item.get("round")
        if event_round is not None and (
            type(event_round) is not int or event_round < 0 or event_round > row["rounds"]
        ):
            return False
        for field in ("current_text_checked", "controlled_reproduction"):
            if field in item and type(item[field]) is not bool:
                return False
    return True


def analyze(payload):
    errors, warnings = [], []
    reports = payload.get("reports") or []
    valid, seen_ids = [], set()
    for index, row in enumerate(reports, 1):
        if not isinstance(row, dict):
            errors.append({"code": "REPORT_FORMAT_INVALID", "report": index})
            continue
        missing = sorted(x for x in REQUIRED if x not in row or row.get(x) in (None, "", []))
        if missing:
            errors.append({"code": "REPORT_FIELDS_MISSING", "report": row.get("id") or index, "fields": missing})
            continue
        report_id = str(row["id"])
        if report_id in seen_ids:
            errors.append({"code": "DUPLICATE_REPORT_ID", "report": report_id})
            continue
        seen_ids.add(report_id)
        evidence_status = row.get("evidence_status", "summary_only")
        invalid = (
            type(row["rounds"]) is not int or row["rounds"] <= 0
            or not isinstance(row["action_order"], list)
            or not isinstance(row["diagnosis_tags"], list)
            or any(not isinstance(tag, str) or not tag.strip() for tag in row["diagnosis_tags"])
            or evidence_status not in EVIDENCE_STATUSES
            or not _validate_observations(row)
        )
        headshot_round = row.get("headshot_round")
        if headshot_round is not None and (
            type(headshot_round) is not int or headshot_round < 1
            or (type(row["rounds"]) is int and headshot_round > row["rounds"])
        ):
            invalid = True
        if invalid:
            errors.append({"code": "REPORT_FIELD_INVALID", "report": report_id, "message": "回合数、行动顺序、问题标签、证据状态、机制观察或爆头回合格式无效"})
            continue
        row = dict(row)
        row["evidence_status"] = evidence_status
        nonstandard = sorted({
            item["category"].strip()
            for item in row.get("mechanism_observations") or []
            if item["category"].strip() not in STANDARD_CATEGORIES
        })
        if nonstandard:
            warnings.append({
                "code": "NONSTANDARD_MECHANISM_CATEGORY",
                "report": report_id,
                "categories": nonstandard,
                "message": "存在非标准机制类别；允许保留，但可能导致跨战报统计分散",
            })
        valid.append(row)
    representative = [x for x in valid if x.get("representative", True)]
    diagnostic_representative = [x for x in representative if x["evidence_status"] != "summary_only"]
    if len(diagnostic_representative) < 5:
        warnings.append({"code": "SAMPLE_TOO_SMALL", "message": f"只有{len(diagnostic_representative)}份含事件证据的代表战报；一般调整至少需5份complete/partial样本，摘要只统计结果"})
    if len(representative) > 10:
        warnings.append({"code": "SAMPLE_TOO_LARGE", "message": f"有{len(representative)}份代表战报；建议选取10份覆盖不同对手的样本，避免同类战报淹没问题"})

    by_team = defaultdict(list)
    for row in representative:
        by_team[row["team"]].append(row)
    team_results = {}
    sufficient_global_sample = len(diagnostic_representative) >= 5 and not errors
    for team, rows in by_team.items():
        diagnostic_rows = [row for row in rows if row["evidence_status"] != "summary_only"]
        sample_actionable = sufficient_global_sample and len(diagnostic_rows) >= 5
        if sufficient_global_sample and not sample_actionable:
            warnings.append({"code": "TEAM_SAMPLE_TOO_SMALL", "team": team, "message": f"本队只有{len(diagnostic_rows)}份含事件证据的代表战报，暂不据此改队"})
        tags = Counter(tag for row in diagnostic_rows for tag in row.get("diagnosis_tags", []))
        headshots = [row for row in diagnostic_rows if isinstance(row.get("headshot_round"), int) and row["headshot_round"] <= 3]
        order_mismatches = []
        for row in diagnostic_rows:
            expected = row.get("expected_action_order") or []
            if expected and row.get("action_order") != expected:
                order_mismatches.append(row["id"])
        damage_sources = Counter(row.get("main_damage_source") for row in diagnostic_rows if row.get("main_damage_source"))
        first_controls = Counter(row.get("first_control") for row in diagnostic_rows if row.get("first_control"))
        first_buffs = Counter(row.get("first_buff") for row in diagnostic_rows if row.get("first_buff"))
        first_abnormal_events = Counter(row.get("first_abnormal_event") for row in diagnostic_rows if row.get("first_abnormal_event"))
        evidence_statuses = Counter(row.get("evidence_status", "summary_only") for row in rows)
        observation_reports = defaultdict(list)
        confirmed_hard_faults = []
        for row in diagnostic_rows:
            for observation in row.get("mechanism_observations") or []:
                category = observation["category"].strip()
                if observation["confidence"] != "unknown":
                    observation_reports[category].append(row["id"])
                if (
                    category in DETERMINISTIC_CATEGORIES
                    and observation["confidence"] == "confirmed"
                    and observation.get("current_text_checked") is True
                    and row.get("evidence_status") == "complete"
                ):
                    confirmed_hard_faults.append({
                        "report": row["id"],
                        "category": category,
                        "evidence": observation["evidence"],
                        "round": observation.get("round"),
                    })
        hard_fault_actionable = bool(confirmed_hard_faults) and not errors
        team_actionable = sample_actionable or hard_fault_actionable
        if evidence_statuses.get("summary_only", 0) == len(rows):
            warnings.append({
                "code": "NO_DEEP_MECHANISM_EVIDENCE",
                "team": team,
                "message": "本队只有结果摘要，没有完整事件链；可统计胜负，不能据此解释伤害、恢复或战法机制",
            })
        repeated = {key: count for key, count in tags.items() if count >= 2}
        recommendations = []
        if hard_fault_actionable:
            kinds = "、".join(sorted({x["category"] for x in confirmed_hard_faults}))
            recommendations.append(f"完整战报与当前文本已锁定确定性硬错误（{kinds}）；先纠正该错误，再收集改动后战报，不据此重做整队")
        if sample_actionable:
            if tags.get("速度", 0) >= 2 or len(order_mismatches) >= 2:
                recommendations.append("复核速度加点、宝物与先后手目标；先修正实际行动顺序，再判断是否换战法")
            if tags.get("生存", 0) >= 2 or len(headshots) >= 2:
                recommendations.append("优先补前三回合生存与大营保护，避免把爆头误判为输出不足")
            if tags.get("输出", 0) >= 2:
                recommendations.append("单独核对主输出战法是否发动、目标是否有效以及兵力衰减，确认后再补输出")
            if not recommendations and repeated:
                recommendations.append("重复问题已出现，但不属于速度/生存/输出三类；回看对应战报的首个异常事件")
        team_results[team] = {
            "sample_count": len(rows),
            "diagnostic_sample_count": len(diagnostic_rows),
            "actionable": team_actionable,
            "action_basis": {
                "confirmed_hard_fault": hard_fault_actionable,
                "representative_sample": sample_actionable,
            },
            "results": dict(Counter(row["result"] for row in rows)),
            "evidence_status_counts": dict(evidence_statuses),
            "actual_action_orders": {row["id"]: row["action_order"] for row in diagnostic_rows},
            "action_order_mismatch_reports": order_mismatches,
            "first_controls": dict(first_controls),
            "first_buffs": dict(first_buffs),
            "first_abnormal_events": dict(first_abnormal_events),
            "main_damage_sources": dict(damage_sources),
            "early_headshots_round_1_to_3": [row["id"] for row in headshots],
            "repeated_issue_tags": repeated,
            "mechanism_observation_reports": {key: value for key, value in observation_reports.items()},
            "confirmed_hard_faults": confirmed_hard_faults,
            "recommendations": recommendations,
        }

    opponents = Counter(x.get("opponent_archetype") for x in representative)
    return {
        "actionable": any(x["actionable"] for x in team_results.values()),
        "sample": {
            "total": len(reports),
            "valid_representative": len(representative),
            "diagnostic_representative": len(diagnostic_representative),
            "opponent_coverage": dict(opponents),
            "target": "每队至少5份complete/partial代表样本，建议5至10份且覆盖不同常见对手；摘要只统计结果",
        },
        "teams": team_results,
        "errors": errors,
        "warnings": warnings,
        "decision_rule": "单场胜负不触发改队；完整事件链加当前文本可立即纠正确认的目标/距离、触发前提、冲突或行动顺序硬错误；随机性与强度问题仍需每队至少5份代表战报。",
        "reading_rule": "先记录准备回合与行动链，定位第一个异常事件，再解释伤害、恢复和最终胜负。",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(load(args.input))
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
