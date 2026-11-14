# -*- coding: utf-8 -*-
"""5×5抽检中对「中心论据帧」的补充视觉复核。"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Desktop\shandou")
LOCAL = ROOT / "资料库" / "5X5_RANDOM_AUDIT_LOCAL_EVIDENCE_20260825.json"
OUT = ROOT / "资料库" / "5X5_RANDOM_AUDIT_VISION_TARGETS_20260825.json"

# 为首帧是片头/地图/聊天，不能直接支撑中心论据的报告手工选择关键帧。
TARGET_SECONDS = {
    "R1-1": 27,
    "R1-3": 150,
    "R1-4": 50,
    "R1-5": 24,
    "R2-1": 13,
    "R2-2": 24,
    "R2-3": 53,
    "R2-4": 35,
    "R2-5": 9,
    "R3-1": 36,
    "R3-3": 43,
    "R3-4": 20,
    "R4-1": 43,
    "R4-4": 43,
    "R4-5": 18,
    "R5-2": 37,
    "R5-5": 15,
}

PROMPT = (
    "这是《率土之滨》成果报告的中心论据帧。"
    "只根据画面，禁止补全或猜测。请尽量精确读取："
    "1.武将名与阵营/兵种/星级；2.每个战法名及数字；3.宝物/特性；"
    "4.战报数值或硬字幕；5.无法辨认项。"
)


def frame_name(sec: int) -> str:
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"frame_{sec + 1:06d}_{h:02d}h{m:02d}m{s:02d}s000ms.jpg"


def source_dir(record: dict) -> Path:
    text = record["full_text"]
    dm = re.search(r"源静帧目录：([^\r\n]+)", text)
    if dm:
        return ROOT / dm.group(1).strip()
    report = record["report"]
    jp = Path(record["json_candidates"][0])
    d = json.loads(jp.read_text(encoding="utf-8"))
    if "阵容新批" in report:
        return ROOT / "抖音_frames_dense_1s" / "阵容" / d["frames_dir"]
    if "海之呼唤" in report:
        return ROOT / "海之呼唤_frames_dense_1s" / d["frames_dir"]
    if "赛季" in report:
        return ROOT / "赛季_frames_dense_1s" / d["frames_dir"]
    return ROOT / "抖音_frames_dense_1s" / d["frames_dir"]


def save(rows: list[dict]) -> None:
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, OUT)


def main() -> None:
    records = {x["sample_id"]: x for x in json.loads(LOCAL.read_text(encoding="utf-8"))["records"]}
    existing = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    done = {x["sample_id"]: x for x in existing if not x.get("vision_text", "").startswith("ERR")}
    p = ROOT / "资料库" / "vision_glm.py"
    spec = importlib.util.spec_from_file_location("vision_glm_targets", p)
    vg = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(vg)

    for sid, sec in TARGET_SECONDS.items():
        if sid in done:
            print(f"SKIP {sid}", flush=True)
            continue
        record = records[sid]
        frame = source_dir(record) / frame_name(sec)
        if not frame.exists():
            done[sid] = {"sample_id": sid, "second": sec, "frame": str(frame), "vision_text": "ERR NO_FRAME"}
            save([done[x] for x in sorted(done)])
            print(f"ERR {sid} NO_FRAME", flush=True)
            continue
        buf = io.StringIO()
        try:
            old_argv = sys.argv
            with contextlib.redirect_stdout(buf):
                sys.argv = ["vision_glm.py", str(frame), PROMPT]
                vg.main()
            sys.argv = old_argv
            result = buf.getvalue().strip()
        except SystemExit:
            result = buf.getvalue().strip() or "ERR SYSTEM_EXIT"
        except Exception as exc:
            result = f"ERR {exc!r}"
        done[sid] = {
            "sample_id": sid,
            "second": sec,
            "report": record["report"],
            "frame": str(frame),
            "vision_text": result,
        }
        save([done[x] for x in sorted(done)])
        print(f"DONE {sid} sec={sec} chars={len(result)}", flush=True)
    rows = [done[x] for x in sorted(done)]
    save(rows)
    print(f"COMPLETE total={len(rows)} ok={sum(not x['vision_text'].startswith('ERR') for x in rows)}")


if __name__ == "__main__":
    main()
