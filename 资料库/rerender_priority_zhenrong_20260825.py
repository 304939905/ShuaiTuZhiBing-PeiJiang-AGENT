#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""重渲 5×5 抽检中核心结论截断的 7 份阵容新批精编报告。

仅处理明确列出的样本（含用户已解除挂起的第十三期），并在首次覆盖前
将原 DOCX 复制到审计备份目录。不会批量渲染其余阵容新批成果。
"""
from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

ROOT = Path(r"D:/Desktop/shandou")
LIB = ROOT / "资料库"
SRC = LIB / "zhenrong_frame_json"
OUT = ROOT / "报告库" / "阵容新批" / "精编"
BACKUP = LIB / "audit_backups" / "20260825_priority_zhenrong_reports"

TARGETS = [
    "video_来来来，上人配将，免费粉丝配将第..._top_0_1.json",
    "video_对自己队伍不确定的，发评论区大家..._top_0_3.json",
    "配将点评.json",
    "率土之滨队伍推荐第16队——宁元刀（黑科技）（碰瓷）.json",
    "video_来人配将，免费粉丝配将第十三期 ..._top_0_3.json",
    "四星称号神队晋步，竹林七贤.json",
    "video_免费粉丝配将第九期，平民专业配将..._top_0_2.json",
]


def main() -> None:
    spec = importlib.util.spec_from_file_location(
        "gen_refined_report_zhenrong", LIB / "gen_refined_report_zhenrong.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    BACKUP.mkdir(parents=True, exist_ok=True)
    for filename in TARGETS:
        src = SRC / filename
        if not src.exists():
            raise FileNotFoundError(src)
        title = module.load_json(src).get("video_title") or src.stem
        output = OUT / f"{title}_精编学习报告.docx"
        if not output.exists():
            raise FileNotFoundError(output)
        backup = BACKUP / output.name
        if not backup.exists():
            shutil.copy2(output, backup)
        rendered, _ = module.render(str(src))
        if Path(rendered) != output or not output.exists():
            raise RuntimeError(f"render output mismatch: {rendered}")
        print(f"OK {output.name}")


if __name__ == "__main__":
    main()
