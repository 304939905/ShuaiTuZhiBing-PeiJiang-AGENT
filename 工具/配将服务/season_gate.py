#!/usr/bin/env python3
"""赛季门禁：区分“账号已拥有可继续使用”与“当前赛季能否新获取”。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "资料库" / "official_skill_db.json"
STAGE_ORDER = {"S1": 1, "S2": 2, "S3": 3, "征服赛季": 4}


def load_catalog(path: Path = DB_PATH):
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    return {
        int(row["id"]): {"name": name, **row}
        for name, row in raw.get("skills", {}).items()
        if row.get("id") is not None
    }


def evaluate_skill(skill, current_season, *, owned=False, material=False, purpose="acquire"):
    """返回单个战法的赛季结论。

    owned=True 只回答“能否继续使用”；否则回答“当前能否新获取”。
    material=True 表示该项会改变正式配将结论，此时不确定项进入人工核验清单。
    """
    name = skill.get("name") or f"战法ID {skill.get('id')}"
    stage = skill.get("acquisition_stage")
    status = skill.get("acquisition_stage_status")
    result = {
        "skill_id": skill.get("id"),
        "name": name,
        "purpose": purpose,
        "owned": bool(owned),
        "current_season": current_season,
        "acquisition_stage": stage,
        "acquisition_stage_status": status,
        "allowed": None,
        "needs_manual_check": False,
        "reason": "",
    }
    if owned:
        result["allowed"] = True
        result["reason"] = (
            "当前赛季战报已实际观察到；按实战事实纳入克制分析"
            if purpose == "counter"
            else "账号已拥有；获取阶段不限制跨赛季继续使用"
        )
        return result
    if current_season not in STAGE_ORDER:
        result["reason"] = "当前赛季未确定，不能判断新获取资格"
        result["needs_manual_check"] = bool(material)
        return result
    if not stage:
        result["reason"] = "本地资料缺少获取阶段，暂不作为可获取战法推荐"
        result["needs_manual_check"] = bool(material)
        return result
    if stage not in STAGE_ORDER:
        result["reason"] = f"本地获取阶段“{stage}”无法映射，暂不推荐新获取"
        result["needs_manual_check"] = bool(material)
        return result
    if status == "provisional_default":
        if current_season != "征服赛季":
            result["allowed"] = False
            result["reason"] = "获取阶段为保守暂定的征服赛季；当前按不可获取过滤"
        else:
            result["reason"] = "处于征服赛季，但该战法的具体获取阶段仍是暂定值"
        result["needs_manual_check"] = bool(material)
        return result
    if status != "confirmed":
        result["reason"] = f"本地写有获取阶段{stage}，但缺少已确认状态，暂不作为可获取结论"
        result["needs_manual_check"] = bool(material)
        return result
    result["allowed"] = STAGE_ORDER[stage] <= STAGE_ORDER[current_season]
    result["reason"] = (
        f"已确认可在{stage}起获取"
        if result["allowed"]
        else f"已确认需到{stage}，当前{current_season}不可新获取"
    )
    return result


def evaluate_requests(requests, current_season, owned_ids, catalog=None):
    catalog = load_catalog() if catalog is None else catalog
    results, manual_checks = [], []
    for request in requests or []:
        purpose = request.get("purpose") or "acquire"
        skill_id = request.get("skill_id")
        try:
            skill_id = int(skill_id)
        except (TypeError, ValueError):
            row = {
                "skill_id": request.get("skill_id"),
                "name": request.get("name") or "未识别战法",
                "allowed": None,
                "needs_manual_check": bool(request.get("material")),
                "reason": "战法ID无效，不能执行赛季门禁",
            }
            results.append(row)
            if row["needs_manual_check"]:
                manual_checks.append(row)
            continue
        skill = catalog.get(skill_id) or {"id": skill_id, "name": request.get("name")}
        row = evaluate_skill(
            skill,
            current_season,
            # “新获取”即使账号已有一份，也须重新过赛季门禁；
            # “克制分析”不能把我方持有当成对手持有的证据。
            owned=(skill_id in owned_ids) if purpose == "use" else bool(request.get("observed_in_current_season")) if purpose == "counter" else False,
            material=bool(request.get("material")),
            purpose=purpose,
        )
        results.append(row)
        if row["needs_manual_check"]:
            manual_checks.append(row)
    return {"results": results, "manual_checks": manual_checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("requests", type=Path, help="包含season、owned_skill_ids、requests的JSON")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.requests.read_text(encoding="utf-8-sig"))
    result = evaluate_requests(
        payload.get("requests"),
        payload.get("season"),
        {int(x) for x in payload.get("owned_skill_ids", [])},
    )
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
