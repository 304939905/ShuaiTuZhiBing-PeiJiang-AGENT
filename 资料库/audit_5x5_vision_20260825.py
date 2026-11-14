# -*- coding: utf-8 -*-
"""5×5抽检中的代表性源帧视觉复核（增量写入）。"""
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
OUT = ROOT / "资料库" / "5X5_RANDOM_AUDIT_VISION_20260825.json"

PROMPT = (
    "这是《率土之滨》视频的1秒源帧，用于报告溯源抽检。"
    "只根据画面回答，禁止猜测：1.画面类型；2.可辨认的武将/战法/宝物/数字；"
    "3.硬字幕或UI关键文字；4.无法辨认的部分。简洁分点。"
)


def load_vision_module():
    p = ROOT / "资料库" / "vision_glm.py"
    spec = importlib.util.spec_from_file_location("vision_glm_audit", p)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def first_timestamp(text: str) -> int:
    for line in text.splitlines():
        if line.startswith("["):
            m = re.search(r"\[(\d{2}):(\d{2})\]", line)
            if m:
                return int(m.group(1)) * 60 + int(m.group(2))
    m = re.search(r"\[(\d{2}):(\d{2})\]", text)
    return int(m.group(1)) * 60 + int(m.group(2)) if m else 0


def frame_name(sec: int) -> str:
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"frame_{sec + 1:06d}_{h:02d}h{m:02d}m{s:02d}s000ms.jpg"


def locate_frame(record: dict) -> tuple[Path | None, str]:
    text = record["full_text"]
    report = Path(record["report"])

    # 阵容新批：取 JSON 时间轴首帧，该帧有人工结构化描述。
    if "阵容新批" in str(report) and record["json_candidates"]:
        jp = Path(record["json_candidates"][0])
        d = json.loads(jp.read_text(encoding="utf-8"))
        timeline = d.get("timeline") or []
        for block in timeline:
            for f in block.get("frames") or []:
                name = f.get("file")
                if name:
                    p = ROOT / "抖音_frames_dense_1s" / "阵容" / d["frames_dir"] / name
                    if p.exists():
                        return p, f"json:{jp.name} ts={f.get('ts', '')}"

    # 旧批次中有少数精编报告未写「源静帧目录」，
    # 从 frame_json.frames_dir + 首条结构化时间锚恢复实际 1s 帧。
    if record["json_candidates"]:
        jp = Path(record["json_candidates"][0])
        d = json.loads(jp.read_text(encoding="utf-8"))
        roots = []
        if "海之呼唤" in str(report):
            roots.append(ROOT / "海之呼唤_frames_dense_1s")
        elif "赛季" in str(report):
            roots.append(ROOT / "赛季_frames_dense_1s")
        else:
            roots.append(ROOT / "抖音_frames_dense_1s")
        for block in d.get("timeline") or []:
            for f in block.get("frames") or []:
                ts = f.get("ts") or ""
                m = re.fullmatch(r"(\d{2}):(\d{2})", ts)
                if not m:
                    continue
                sec = int(m.group(1)) * 60 + int(m.group(2))
                for root in roots:
                    p = root / d["frames_dir"] / frame_name(sec)
                    if p.exists():
                        return p, f"json-restored:{jp.name} ts={ts}"

    # 其他精修：取正文第一个单点时间锚，与源静帧目录组合。
    dm = re.search(r"源静帧目录：([^\r\n]+)", text)
    if dm:
        src_dir = ROOT / dm.group(1).strip()
        sec = first_timestamp(text)
        p = src_dir / frame_name(sec)
        if p.exists():
            return p, f"docx:first-anchor={sec}s"
        # 容错：返回目录内第一张非 contact sheet。
        files = sorted(x for x in src_dir.glob("*.jpg") if "contact" not in x.name.lower())
        if files:
            return files[0], f"fallback:first-frame expected={p.name}"

    return None, "NO_FRAME"


def save(rows: list[dict]) -> None:
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, OUT)


def main() -> None:
    records = json.loads(LOCAL.read_text(encoding="utf-8"))["records"]
    previous = []
    if OUT.exists():
        previous = json.loads(OUT.read_text(encoding="utf-8"))
    by_id = {x["sample_id"]: x for x in previous if x.get("vision_text") and not x["vision_text"].startswith("ERR")}
    vg = load_vision_module()

    for record in records:
        sid = record["sample_id"]
        if sid in by_id:
            print(f"SKIP {sid}", flush=True)
            continue
        frame, locator = locate_frame(record)
        if not frame:
            by_id[sid] = {
                "sample_id": sid,
                "report": record["report"],
                "frame": None,
                "locator": locator,
                "vision_text": "ERR NO_FRAME",
            }
            save([by_id[k] for k in sorted(by_id)])
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
        by_id[sid] = {
            "sample_id": sid,
            "report": record["report"],
            "frame": str(frame),
            "locator": locator,
            "vision_text": result,
        }
        save([by_id[k] for k in sorted(by_id)])
        print(f"DONE {sid} frame={frame.name} chars={len(result)}", flush=True)

    rows = [by_id[k] for k in sorted(by_id)]
    save(rows)
    ok = sum(1 for x in rows if not x["vision_text"].startswith("ERR"))
    print(f"COMPLETE total={len(rows)} ok={ok} out={OUT}")


if __name__ == "__main__":
    main()
