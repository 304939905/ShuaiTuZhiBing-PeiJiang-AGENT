"""阵容新批「核心结论」完整性守卫。

这是渲染前的内容完整性检查，不判断游戏事实是否正确；它只阻止没有结构化
核心结论、或以明显残句结束的母本被渲染成“精编学习报告”。

优先检查人工复核的 refined_key_points；没有该字段时才检查旧 key_points。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


TERMINALS = "。！？"


def selected_core_points(data: dict[str, Any]) -> list[str]:
    summary = data.get("summary") or {}
    if not isinstance(summary, dict):
        return []
    points = summary.get("refined_key_points") or summary.get("key_points") or []
    if not isinstance(points, list):
        return []
    return [str(point).strip() for point in points if str(point).strip()]


def _points_issues(points: list[str]) -> list[str]:
    if not points:
        return ["缺少结构化核心结论"]

    last = points[-1]
    if last[-1:] not in TERMINALS:
        return [f"末条核心结论未以完整句末标点结束：{last[-24:]}"]
    return []


def core_issues(data: dict[str, Any]) -> list[str]:
    return _points_issues(selected_core_points(data))


def raw_core_issues(data: dict[str, Any]) -> list[str]:
    """检查原始 key_points，防止 refined_key_points 掩盖截断母本。"""
    summary = data.get("summary") or {}
    raw = summary.get("key_points") if isinstance(summary, dict) else []
    if not isinstance(raw, list):
        raw = []
    points = [str(point).strip() for point in raw if isinstance(point, str) and point.strip()]
    return _points_issues(points)


def assert_complete_core(data: dict[str, Any], source: str = "母本") -> None:
    issues = core_issues(data)
    if issues:
        raise ValueError(f"{source}核心结论不完整，拒绝渲染：{'；'.join(issues)}")


def scan(directory: Path, raw: bool = False) -> int:
    bad = 0
    for path in sorted(directory.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        issues = raw_core_issues(data) if raw else core_issues(data)
        if issues:
            bad += 1
            print(f"NEEDS_REPAIR\t{path.name}\t{'；'.join(issues)}")
        else:
            print(f"PASS\t{path.name}")
    return bad


if __name__ == "__main__":
    args = [arg for arg in sys.argv[1:] if arg != "--raw"]
    root = Path(args[0]) if args else Path(__file__).with_name("zhenrong_frame_json")
    count = scan(root, raw="--raw" in sys.argv[1:])
    print(f"ISSUE={count}")
    raise SystemExit(1 if count else 0)
