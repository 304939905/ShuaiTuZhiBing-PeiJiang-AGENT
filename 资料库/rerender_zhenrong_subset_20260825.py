#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""仅重渲已完成母本重建的 7 份非抽样阵容精编，并同步替换对应索引行。"""
from __future__ import annotations

import json
from pathlib import Path

import gen_refined_report_zhenrong as renderer
from rebuild_zhenrong_raw_keypoints_20260825 import REBUILT


LIB = Path(__file__).resolve().parent
SRC = LIB / "zhenrong_frame_json"
INDEX = LIB / "zhenrong_index_rows.json"


def main() -> None:
    old_rows = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else []
    rendered = {}
    for filename in REBUILT:
        out_path, row = renderer.render(str(SRC / filename))
        rendered[row["rel"]] = row
        print(f"OK\t{Path(out_path).name}")

    merged = []
    seen = set()
    for row in old_rows:
        key = row.get("rel")
        if key in rendered:
            merged.append(rendered[key])
            seen.add(key)
        else:
            merged.append(row)
    for key, row in rendered.items():
        if key not in seen:
            merged.append(row)
    INDEX.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"INDEX_ROWS={len(merged)}")


if __name__ == "__main__":
    main()
