import json
import unittest

from analyze_battle_reports import analyze
from audit_consultation import audit, render_report
from parse_account import gear_export_status, hero_stars, index_skill_rows, load_indexes, parse_skills, unwrap_export
from season_gate import STAGE_ORDER, evaluate_requests, evaluate_skill, load_catalog
from validate_lineup import validate


def profile():
    return {
        "season": {"label": "S1"},
        "heroes": [
            {"id": 1, "name": "甲", "unique_name": "甲-魏-骑", "troop_type": "骑", "stars": 5, "awakened": False, "cost": 3, "attack_distance": 3,
             "builtin_skill": {"id": 101, "name": "自带甲", "type": "主动", "target": "敌军单体", "distance": 4, "effect": "混乱"}},
            {"id": 2, "name": "乙", "unique_name": "乙-魏-骑", "troop_type": "骑", "stars": 5, "awakened": True, "cost": 3, "attack_distance": 2},
            {"id": 3, "name": "丙", "unique_name": "丙-魏-骑", "troop_type": "骑", "stars": 4, "awakened": True, "cost": 3, "attack_distance": 1},
        ],
        "skills": [
            {"id": 11, "name": "战法甲", "max_copies": 1, "soldier_type": "骑", "target": "敌军单体", "distance": 4, "type": "主动", "effect": "混乱"},
            {"id": 12, "name": "战法乙", "max_copies": 1, "soldier_type": "弓", "target": "敌军单体", "distance": 1, "type": "主动", "effect": "混乱"},
            {"id": 13, "name": "战法丙", "max_copies": 1, "soldier_type": "骑", "target": "我军单体", "distance": 1, "type": "指挥", "effect": "休整"},
        ],
    }


def full_consultation():
    p = profile()
    p["heroes"][0]["awakened"] = True
    p["heroes"][0]["builtin_skill"]["effect"] = ""
    p["skills"] = [
        {"id": i, "name": f"战法{i}", "max_copies": 1, "available_copies": 1,
         "soldier_type": "骑", "target": "我军单体", "distance": 2, "type": "被动", "effect": ""}
        for i in range(11, 17)
    ]
    team = {
        "name": "第一主力", "priority": "主力", "priority_rank": 1,
        "members": [
            {"position": "大营", "hero_id": 1, "learned_skills": [11, 12]},
            {"position": "中军", "hero_id": 2, "learned_skills": [13, 14]},
            {"position": "前锋", "hero_id": 3, "learned_skills": [15, 16]},
        ],
        "core_logic": "输出与保护", "speed_requirements": "以实战确认", "strengths": "稳定",
        "major_counters": "爆头", "alternatives": [{"skill": "战法11", "replacement_cost": "降低输出"}],
        "awakening_cost": "无", "dismantling_cost": "无", "resource_conflicts": "无",
    }
    plan = {"season": "S1", "cost_limit": 10, "team_limit": 10, "awakening_resources": {"five_star_slots": 0}, "requested_main_teams": 1, "consultation_type": "full_account",
            "teams": [team], "governance_plans": [{"direction": "金币获取", "plan": "方案甲"}, {"direction": "自由建议", "plan": "方案乙"}]}
    return p, plan


def battle_reports(count, evidence_status):
    return [{
        "id": f"R{i}", "team": "第一主力", "opponent_archetype": "常规队", "result": "负",
        "rounds": 4, "action_order": ["敌方", "我方"], "expected_action_order": ["我方", "敌方"],
        "main_damage_source": "敌方", "diagnosis_tags": ["输出"], "evidence_status": evidence_status,
    } for i in range(count)]


class ServiceTests(unittest.TestCase):
    def test_export_code_200_is_success(self):
        wrapped = {"error_code": 0, "data": {"data": json.dumps({"code": 200, "msg": {"hero": [], "skill": []}})}}
        self.assertEqual(unwrap_export(wrapped)["hero"], [])

    def test_hidden_gear_export_is_not_zero_owned_gears(self):
        self.assertEqual(gear_export_status({"show_gear": False, "gear": []}), "not_exposed")
        self.assertEqual(gear_export_status({"show_gear": True, "gear": []}), "empty_export")

    def test_star_uses_exact_hero_version_not_extra_quality_prefix(self):
        extra = {"quality": "4-SR", "methodId": 200111}
        self.assertEqual(hero_stars(extra, {"quality": 5, "skill_init": 200111}), 5)
        self.assertIsNone(hero_stars(extra, {"quality": 5, "skill_init": 200112}))

    def test_local_hero_indexes_keep_exact_star_link(self):
        heroes, versions, _, _, _ = load_indexes()
        self.assertTrue(heroes)
        unresolved = [hero_id for hero_id, hero in heroes.items() if hero_stars(hero, versions.get(hero_id, {})) is None]
        self.assertEqual(unresolved, [])

    def test_zero_means_no_free_copy_not_unowned(self):
        rows, unknown = parse_skills(
            [[99, 0]],
            {99: {"id": 99, "name": "先驱突击", "skillCount": 1}},
            {},
        )
        self.assertFalse(unknown)
        self.assertTrue(rows[0]["owned"])
        self.assertEqual(rows[0]["available_copies"], 0)
        self.assertEqual(rows[0]["total_copies"], 1)
        self.assertEqual(rows[0]["assigned_copies"], 1)
        self.assertIn("skill_extra.skillCount", rows[0]["total_copies_source"])

    def test_skill_database_duplicate_id_must_be_identical(self):
        row = {"id": 99, "name": "测试", "skillCount": 1}
        self.assertEqual(len(index_skill_rows([row, dict(row)])), 1)
        with self.assertRaisesRegex(ValueError, "99"):
            index_skill_rows([row, {**row, "skillCount": 2}])

    def test_total_notice_corroboration_and_conflict(self):
        rows, _ = parse_skills(
            [[98, 0], [99, 0]],
            {
                98: {"id": 98, "name": "一致", "skillCount": 2, "notice": "战法研究成功后，可配置2个武将"},
                99: {"id": 99, "name": "冲突", "skillCount": 2, "notice": "战法研究成功后，可配置1个武将"},
            },
            {},
        )
        self.assertEqual(rows[0]["total_copies_status"], "db_notice_agree")
        self.assertEqual(rows[1]["total_copies_status"], "db_notice_conflict")
        self.assertIsNone(rows[1]["total_copies"])

    def test_used_skill_without_total_cannot_pass_delivery_audit(self):
        p = profile()
        p["skills"][0].update({"total_copies": None, "available_copies": 1})
        plan = {"season": "S1", "teams": [{"name": "待核队", "members": [
            {"position": "大营", "hero_id": 1, "learned_skills": [11]},
            {"position": "中军", "hero_id": 2, "learned_skills": []},
            {"position": "前锋", "hero_id": 3, "learned_skills": []},
        ]}]}
        self.assertIn("SKILL_TOTAL_UNKNOWN", {x["code"] for x in validate(p, plan, catalog={})["warnings"]})
        result = audit(p, plan)
        self.assertFalse(result["delivery_ready"])
        self.assertIn("SKILL_TOTAL_UNKNOWN", {x["code"] for x in result["unresolved_resources"]})

    def test_valid_plan_passes(self):
        plan = {"season": "S1", "cost_limit": 10, "awakening_resources": {"five_star_slots": 0}, "teams": [{"name": "测试", "priority_rank": 1, "members": [
            {"position": "大营", "hero_id": 1, "learned_skills": [11]},
            {"position": "中军", "hero_id": 2, "learned_skills": []},
            {"position": "前锋", "hero_id": 3, "learned_skills": []},
        ]}]}
        self.assertTrue(validate(profile(), plan, catalog={})["passed"])

    def test_hard_failures_are_detected(self):
        plan = {"season": "S1", "cost_limit": 8, "awakening_resources": {"five_star_slots": 0}, "teams": [{"name": "错误队", "members": [
            {"position": "大营", "hero_id": 1, "learned_skills": [11, 12]},
            {"position": "中军", "hero_id": 1, "learned_skills": [11]},
            {"position": "前锋", "hero_id": 3, "learned_skills": []},
        ]}]}
        result = validate(profile(), plan, catalog={})
        codes = {x["code"] for x in result["errors"]}
        self.assertFalse(result["passed"])
        self.assertTrue({"AWAKENING_SLOT", "TROOP_RESTRICTION", "SKILL_RANGE", "COST_LIMIT", "HERO_DUPLICATE", "SKILL_COUNT"} <= codes)

    def test_awakening_budget_and_dismantle_impact(self):
        plan = {"season": "S1", "cost_limit": 10, "awakening_resources": {"five_star_slots": 0}, "planned_dismantles": [{"hero_id": 1}], "teams": [{"name": "主力", "priority": "主力", "priority_rank": 1, "members": [
            {"position": "大营", "hero_id": 1, "will_awaken": True, "learned_skills": [11, 13]},
            {"position": "中军", "hero_id": 2, "learned_skills": []},
            {"position": "前锋", "hero_id": 3, "learned_skills": []},
        ]}]}
        result = validate(profile(), plan, catalog={})
        codes = {x["code"] for x in result["errors"]}
        warnings = {x["code"] for x in result["warnings"]}
        self.assertIn("FIVE_STAR_AWAKENING_BUDGET", codes)
        self.assertIn("DISMANTLE_IN_USE", codes)
        self.assertTrue({"DISMANTLE_SPARE_UNKNOWN", "DISMANTLE_FIVE_STAR_COST"} <= warnings)

    def test_conflict_includes_builtin_skill(self):
        plan = {"season": "S1", "cost_limit": 10, "teams": [{"name": "冲突队", "members": [
            {"position": "大营", "hero_id": 1, "learned_skills": [11]},
            {"position": "中军", "hero_id": 2, "learned_skills": []},
            {"position": "前锋", "hero_id": 3, "learned_skills": []},
        ]}]}
        result = validate(profile(), plan, catalog={})
        self.assertIn("EFFECT_NON_STACK", {x["code"] for x in result["warnings"]})

    def test_same_self_state_on_different_heroes_is_not_conflict(self):
        p = profile()
        p["heroes"][0]["builtin_skill"] = {"id": 101, "name": "甲自带", "type": "被动", "target": "自己", "effect": "连击"}
        p["heroes"][1]["builtin_skill"] = {"id": 102, "name": "乙自带", "type": "被动", "target": "自己", "effect": "连击"}
        plan = {"season": "S1", "cost_limit": 10, "teams": [{"name": "各自连击", "members": [
            {"position": "大营", "hero_id": 1, "learned_skills": []},
            {"position": "中军", "hero_id": 2, "learned_skills": []},
            {"position": "前锋", "hero_id": 3, "learned_skills": []},
        ]}]}
        result = validate(p, plan, catalog={})
        self.assertNotIn("EFFECT_NON_STACK", {x["code"] for x in result["warnings"]})

    def test_season_gate_owned_and_unowned(self):
        skill = {"id": 99, "name": "晚季战法", "acquisition_stage": "征服赛季", "acquisition_stage_status": "confirmed"}
        self.assertTrue(evaluate_skill(skill, "S1", owned=True)["allowed"])
        self.assertFalse(evaluate_skill(skill, "S1", owned=False)["allowed"])
        provisional = {**skill, "acquisition_stage_status": "provisional_default"}
        row = evaluate_skill(provisional, "S1", owned=False, material=True)
        self.assertFalse(row["allowed"])
        self.assertTrue(row["needs_manual_check"])
        requests = evaluate_requests(
            [{"skill_id": 99, "purpose": "acquire"}, {"skill_id": 99, "purpose": "use"}, {"skill_id": 99, "purpose": "counter"}],
            "S1", {99}, {99: skill},
        )
        self.assertEqual([x["allowed"] for x in requests["results"]], [False, True, False])

    def test_stage_without_confirmed_status_is_not_asserted_acquirable(self):
        row = evaluate_skill({"id": 99, "name": "待核战法", "acquisition_stage": "S1"}, "S1", material=True)
        self.assertIsNone(row["allowed"])
        self.assertTrue(row["needs_manual_check"])

    def test_real_catalog_preserves_name_key_and_s3_gate(self):
        catalog = load_catalog()
        pan = next(x for x in catalog.values() if x["name"] == "磐阵善守")
        self.assertEqual(pan["acquisition_stage"], "S3")
        self.assertFalse(evaluate_skill(pan, "S1", owned=False)["allowed"])

    def test_all_confirmed_catalog_stages_obey_season_order(self):
        catalog = load_catalog()
        confirmed = [x for x in catalog.values() if x.get("acquisition_stage_status") == "confirmed"]
        self.assertTrue(confirmed)
        for skill in confirmed:
            stage = skill["acquisition_stage"]
            self.assertIn(stage, STAGE_ORDER)
            for season in STAGE_ORDER:
                row = evaluate_skill(skill, season, owned=False)
                self.assertEqual(row["allowed"], STAGE_ORDER[stage] <= STAGE_ORDER[season], skill["name"])

    def test_zero_available_copy_can_be_reallocated_in_full_rebuild(self):
        p = profile()
        p["skills"][0]["available_copies"] = 0
        plan = {"season": "S1", "cost_limit": 10, "teams": [{"name": "重组", "members": [
            {"position": "大营", "hero_id": 1, "learned_skills": [11]},
            {"position": "中军", "hero_id": 2, "learned_skills": []},
            {"position": "前锋", "hero_id": 3, "learned_skills": []},
        ]}]}
        result = validate(p, plan, catalog={})
        self.assertTrue(result["passed"])
        self.assertIn("SKILL_REALLOCATION", {x["code"] for x in result["notes"]})

    def test_ratio_0_3_allows_three_after_rebuild_but_not_four(self):
        p = profile()
        p["skills"][0].update({"total_copies": 3, "available_copies": 0})
        members = [
            {"position": position, "hero_id": hero_id, "learned_skills": [11]}
            for position, hero_id in (("大营", 1), ("中军", 2), ("前锋", 3))
        ]
        plan = {"season": "S1", "teams": [{"name": "重组", "members": members}]}
        self.assertTrue(validate(p, plan, catalog={})["passed"])
        plan["existing_occupancy"] = {"skills": [{"skill_id": 11, "copies": 1, "team": "保留旧队"}]}
        self.assertIn("SKILL_COUNT", {x["code"] for x in validate(p, plan, catalog={})["errors"]})

    def test_ratio_1_2_preserved_occupancy(self):
        p = profile()
        p["skills"][0].update({"total_copies": 2, "available_copies": 1})
        plan = {"season": "S1", "existing_occupancy": {"skills": [{"skill_id": 11, "copies": 1, "team": "保留旧队"}]}, "teams": [{"name": "新队", "members": [
            {"position": "大营", "hero_id": 1, "learned_skills": [11]},
            {"position": "中军", "hero_id": 2, "learned_skills": []},
            {"position": "前锋", "hero_id": 3, "learned_skills": []},
        ]}]}
        self.assertTrue(validate(p, plan, catalog={})["passed"])
        plan["existing_occupancy"]["skills"][0]["copies"] = 2
        self.assertIn("SKILL_PRESERVED_COUNT", {x["code"] for x in validate(p, plan, catalog={})["errors"]})

    def test_export_free_count_above_database_total_is_not_silently_accepted(self):
        rows, unknown = parse_skills([[99, 2]], {99: {"id": 99, "name": "待核战法", "skillCount": 1}}, {})
        self.assertFalse(unknown)
        self.assertIsNone(rows[0]["assigned_copies"])
        p = profile()
        p["skills"][0].update({"available_copies": 2, "total_copies": 1})
        plan = {"season": "S1", "teams": [{"name": "测试", "members": [
            {"position": "大营", "hero_id": 1, "learned_skills": [11]},
            {"position": "中军", "hero_id": 2, "learned_skills": []},
            {"position": "前锋", "hero_id": 3, "learned_skills": []},
        ]}]}
        self.assertIn("SKILL_COUNT_INCONSISTENT", {x["code"] for x in validate(p, plan, catalog={})["errors"]})

    def test_owned_later_stage_is_warning_not_ban(self):
        p = profile()
        p["skills"][0]["acquisition_stage"] = "S3"
        p["skills"][0]["acquisition_stage_status"] = "confirmed"
        plan = {"season": "S1", "cost_limit": 10, "teams": [{"name": "跨季已持有", "members": [
            {"position": "大营", "hero_id": 1, "learned_skills": [11]},
            {"position": "中军", "hero_id": 2, "learned_skills": []},
            {"position": "前锋", "hero_id": 3, "learned_skills": []},
        ]}]}
        result = validate(p, plan, catalog={})
        self.assertTrue(result["passed"])
        self.assertIn("OWNED_LATER_STAGE", {x["code"] for x in result["warnings"]})

    def test_existing_occupancy_does_not_need_free_copy(self):
        p = profile()
        p["skills"][0]["available_copies"] = 0
        plan = {"season": "S1", "cost_limit": 10, "existing_occupancy": {"skills": [{"skill_id": 11, "copies": 1, "team": "保留旧队"}]}, "teams": []}
        result = validate(p, plan, catalog={})
        self.assertTrue(result["passed"])

    def test_preserved_old_team_resources_must_exist_and_have_valid_counts(self):
        plan = {"season": "S1", "existing_occupancy": {
            "heroes": [{"hero_id": 999, "team": "保留旧队"}],
            "skills": [
                {"skill_id": 999, "copies": 1, "team": "保留旧队"},
                {"skill_id": 11, "copies": 1.5, "team": "保留旧队"},
            ],
        }, "teams": []}
        codes = {x["code"] for x in validate(profile(), plan, catalog={})["errors"]}
        self.assertTrue({"HERO_OCCUPANCY_NOT_OWNED", "SKILL_OCCUPANCY_NOT_OWNED", "OCCUPANCY_COPIES_INVALID"} <= codes)

    def test_report_audit_requires_reason_for_unused_five_star(self):
        plan = {"season": "S1", "cost_limit": 10, "teams": []}
        result = audit(profile(), plan)
        self.assertIn("UNUSED_FIVE_STAR_UNEXPLAINED", {x["code"] for x in result["report_audit"]["errors"]})

    def test_full_account_consultation_requires_explicit_constraints(self):
        result = audit(profile(), {"season": "S1", "consultation_type": "full_account", "teams": []})
        fields = {x.get("field") for x in result["report_audit"]["errors"] if x["code"] == "ACCOUNT_CONSTRAINT_MISSING"}
        self.assertEqual(fields, {"requested_main_teams", "cost_limit", "team_limit", "awakening_resources.five_star_slots"})

    def test_full_consultation_renders_after_audit(self):
        p, plan = full_consultation()
        result = audit(p, plan)
        self.assertTrue(result["lineup_ready"], result)
        self.assertTrue(result["delivery_ready"], result)
        text = render_report(p, plan, result)
        self.assertIn("第一主力", text)
        self.assertIn("金币获取", text)
        self.assertIn("战法16", text)
        self.assertIn("资料库推定", text)
        battle_report = {
            "reports": [{
                "id": "R-render", "team": "第一主力", "opponent_archetype": "常规队", "result": "负",
                "rounds": 4, "action_order": ["我方", "敌方"], "main_damage_source": "敌方主输出",
                "diagnosis_tags": ["冲突"], "representative": True, "evidence_status": "complete",
                "first_abnormal_event": "准备回合后释放的同类效果失效",
                "mechanism_observations": [{
                    "category": "战法冲突", "round": 0,
                    "evidence": "准备回合日志明确显示后释放效果未生效",
                    "confidence": "confirmed", "current_text_checked": True,
                }],
            }],
        }
        feedback_text = render_report(p, plan, audit(p, plan, battle_report))
        self.assertIn("证据完整/部分/摘要=1/0/0", feedback_text)
        self.assertIn("首个异常事件", feedback_text)
        self.assertIn("已确认硬错误：战法冲突", feedback_text)
        del plan["governance_plans"]
        pending = audit(p, plan)
        self.assertTrue(pending["lineup_ready"])
        self.assertFalse(pending["delivery_ready"])
        self.assertEqual(pending["next_stage"], "阵容已验收，下一步补施政两案")

    def test_governance_empty_content_blocks_delivery_but_keeps_lineup_ready(self):
        empty_values = [None, "", " \n\t", [], {}, [" ", {}], {"内容": [None, " "]}, True, 42,
                        [42], {"占位": 0}, [{"占位": 0}]]
        for value in empty_values:
            with self.subTest(value=value):
                p, plan = full_consultation()
                plan["governance_plans"] = [{"direction": direction, "plan": value} for direction in ("金币获取", "自由建议")]
                result = audit(p, plan)
                self.assertTrue(result["lineup_ready"])
                self.assertFalse(result["delivery_ready"])
                self.assertIn("GOVERNANCE_CONTENT_MISSING", {x["code"] for x in result["report_audit"]["errors"]})
                with self.assertRaises(ValueError):
                    render_report(p, plan, result)

    def test_governance_invalid_types_return_structured_errors(self):
        invalid_values = [{"direction": "金币获取"}, "施政文本", True, 42,
                          [None, {"direction": "自由建议", "plan": "方案乙"}],
                          [{"direction": [], "plan": "方案甲"}, {"direction": "自由建议", "plan": "方案乙"}]]
        for value in invalid_values:
            with self.subTest(value=value):
                p, plan = full_consultation()
                plan["governance_plans"] = value
                result = audit(p, plan)
                self.assertTrue(result["lineup_ready"])
                self.assertFalse(result["delivery_ready"])
                self.assertIn("GOVERNANCE_FORMAT", {x["code"] for x in result["report_audit"]["errors"]})

    def test_governance_details_support_structured_content_and_blank_plan_fallback(self):
        p, plan = full_consultation()
        plan["governance_plans"] = [
            {"direction": "金币获取", "plan": " ", "details": [42, {"政策": "增加金币", "数量": 0}]},
            {"direction": "自由建议", "details": {"参数": [0, 42], "建议": "按账号目标配置"}},
        ]
        result = audit(p, plan)
        self.assertTrue(result["delivery_ready"], result)
        text = render_report(p, plan, result)
        self.assertIn("增加金币", text)
        self.assertIn("按账号目标配置", text)

    def test_battle_feedback_requires_five_and_finds_repetition(self):
        reports = []
        for i in range(5):
            reports.append({
                "id": f"R{i+1}", "team": "第一主力", "opponent_archetype": "爆头队" if i < 3 else "控制队",
                "result": "负" if i < 3 else "平", "rounds": 5, "action_order": ["敌方", "我方"],
                "expected_action_order": ["我方", "敌方"], "first_control": "敌方混乱", "first_buff": "敌方先手",
                "main_damage_source": "主输出", "headshot_round": 2 if i < 3 else None,
                "diagnosis_tags": ["速度", "生存"] if i < 3 else ["输出"], "representative": True,
                "evidence_status": "partial",
            })
        result = analyze({"reports": reports})
        self.assertTrue(result["actionable"])
        team = result["teams"]["第一主力"]
        self.assertEqual(len(team["early_headshots_round_1_to_3"]), 3)
        self.assertIn("速度", team["repeated_issue_tags"])
        self.assertTrue(team["recommendations"])
        reports[3]["team"] = "第二主力"
        reports[4]["team"] = "第二主力"
        split = analyze({"reports": reports})
        self.assertFalse(split["actionable"])
        self.assertFalse(split["teams"]["第一主力"]["actionable"])
        self.assertFalse(split["teams"]["第一主力"]["recommendations"])

    def test_five_summary_reports_only_count_results(self):
        rows = battle_reports(5, "summary_only")
        for row in rows:
            row.update({"headshot_round": 2, "first_control": "摘要推测控制", "first_buff": "摘要推测增益",
                        "first_abnormal_event": "摘要推测异常", "mechanism_observations": [{
                            "category": "战法冲突", "evidence": "摘要推测冲突", "confidence": "confirmed",
                            "current_text_checked": True,
                        }]})
        result = analyze({"reports": rows})
        self.assertFalse(result["actionable"])
        team = result["teams"]["第一主力"]
        self.assertEqual(team["sample_count"], 5)
        self.assertEqual(team["diagnostic_sample_count"], 0)
        self.assertEqual(team["results"], {"负": 5})
        for field in ("recommendations", "repeated_issue_tags", "actual_action_orders", "action_order_mismatch_reports",
                      "first_controls", "first_buffs", "first_abnormal_events", "main_damage_sources",
                      "early_headshots_round_1_to_3", "mechanism_observation_reports", "confirmed_hard_faults"):
            self.assertFalse(team[field], field)

    def test_four_diagnostic_reports_and_summary_do_not_reach_threshold(self):
        rows = battle_reports(4, "partial")
        rows.append({**battle_reports(1, "summary_only")[0], "id": "R-summary"})
        result = analyze({"reports": rows})
        self.assertFalse(result["actionable"])
        team = result["teams"]["第一主力"]
        self.assertEqual(team["sample_count"], 5)
        self.assertEqual(team["diagnostic_sample_count"], 4)
        self.assertFalse(team["action_basis"]["representative_sample"])
        self.assertFalse(team["recommendations"])

    def test_summary_diagnoses_do_not_pollute_five_diagnostic_reports(self):
        rows = battle_reports(5, "partial")
        for row in rows:
            row["action_order"] = row["expected_action_order"]
        baseline = analyze({"reports": rows})["teams"]["第一主力"]
        for i in range(2):
            rows.append({**battle_reports(1, "summary_only")[0], "id": f"S{i}",
                         "diagnosis_tags": ["速度", "生存"], "headshot_round": 2})
        result = analyze({"reports": rows})
        team = result["teams"]["第一主力"]
        self.assertTrue(result["actionable"])
        self.assertEqual(team["sample_count"], 7)
        self.assertEqual(team["diagnostic_sample_count"], 5)
        self.assertEqual(team["recommendations"], baseline["recommendations"])
        self.assertEqual(team["repeated_issue_tags"], {"输出": 5})
        self.assertFalse(team["action_order_mismatch_reports"])
        self.assertFalse(team["early_headshots_round_1_to_3"])

    def test_battle_feedback_rejects_duplicate_or_malformed_samples(self):
        row = {"id": "R1", "team": "主力", "opponent_archetype": "爆头队", "result": "负", "rounds": 3,
               "action_order": ["敌方", "我方"], "main_damage_source": "敌方", "diagnosis_tags": ["生存"]}
        reports = [{**row, "id": f"R{i}"} for i in range(1, 6)]
        reports[4]["id"] = "R1"
        result = analyze({"reports": reports})
        self.assertFalse(result["actionable"])
        self.assertIn("DUPLICATE_REPORT_ID", {x["code"] for x in result["errors"]})
        reports[4]["id"] = "R5"
        reports[4]["diagnosis_tags"] = "生存"
        result = analyze({"reports": reports})
        self.assertIn("REPORT_FIELD_INVALID", {x["code"] for x in result["errors"]})

    def test_battle_feedback_allows_confirmed_hard_fault_before_five_samples(self):
        report = {
            "id": "R-hard", "team": "第一主力", "opponent_archetype": "常规队", "result": "负",
            "rounds": 4, "action_order": ["我方", "敌方"], "main_damage_source": "敌方主输出",
            "diagnosis_tags": ["冲突"], "representative": True, "evidence_status": "complete",
            "first_abnormal_event": "准备回合后释放的同类效果失效",
            "mechanism_observations": [{
                "category": "战法冲突", "round": 0,
                "evidence": "准备回合日志明确显示后释放效果未生效",
                "confidence": "confirmed", "current_text_checked": True,
            }],
        }
        result = analyze({"reports": [report]})
        self.assertTrue(result["actionable"], result)
        team = result["teams"]["第一主力"]
        self.assertEqual(team["diagnostic_sample_count"], 1)
        self.assertTrue(team["action_basis"]["confirmed_hard_fault"])
        self.assertFalse(team["action_basis"]["representative_sample"])
        self.assertEqual(team["confirmed_hard_faults"][0]["category"], "战法冲突")

    def test_battle_feedback_does_not_promote_weak_or_invalid_mechanism_evidence(self):
        report = {
            "id": "R-weak", "team": "第一主力", "opponent_archetype": "常规队", "result": "负",
            "rounds": 4, "action_order": ["我方", "敌方"], "main_damage_source": "敌方主输出",
            "diagnosis_tags": ["冲突"], "representative": True, "evidence_status": "summary_only",
            "mechanism_observations": [{
                "category": "战法冲突", "round": 0, "evidence": "仅结果页推测",
                "confidence": "confirmed", "current_text_checked": True,
            }],
        }
        result = analyze({"reports": [report]})
        self.assertFalse(result["actionable"], result)
        self.assertFalse(result["teams"]["第一主力"]["confirmed_hard_faults"])
        report["mechanism_observations"][0]["round"] = 5
        invalid = analyze({"reports": [report]})
        self.assertIn("REPORT_FIELD_INVALID", {x["code"] for x in invalid["errors"]})


if __name__ == "__main__":
    unittest.main()
