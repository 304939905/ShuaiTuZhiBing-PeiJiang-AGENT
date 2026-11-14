#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量视觉核验: 每份精修取溯源索引首行落地帧, 调 vision_glm 识别画面。
输出 JSON 到 资料库/_vision_verify.json: [{sub, report, frame, vision_text}]
用法: batch_vision_verify.py [子项目] [份数上限]
"""
import sys, io, json, re, os
from pathlib import Path
import contextlib, importlib.util
import docx

ROOT = Path("D:/Desktop/shandou/报告库")
SUB = ["旧56项目", "开荒", "海之呼唤", "赛季"]
BENCH_K = ["攻其篇—粉丝投稿解析", "神赏篇 来了! 评论投稿", "从零开始，宝物养成焚决"]
fpat = re.compile(r"frame_(\d{4})_(\d{2})-(\d{2})\.jpg")
PROMPT = "识别这张游戏截图：1画面主体 2可见UI/文字 3武将或卡牌名。简洁列出。"
JSON_PATH = Path("D:/Desktop/shandou/资料库/_vision_verify.json")


def save_json(out):
    tmp = JSON_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(str(tmp), str(JSON_PATH))

spec = importlib.util.spec_from_file_location("vg", "D:/Desktop/shandou/资料库/vision_glm.py")
vg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vg)

sub_filter = sys.argv[1] if len(sys.argv) > 1 else None
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 0

out = []
done = set()
# merge 模式: 加载已有 JSON, 跳过已有有效结果, 只处理缺失/FRAME_MISSING
if JSON_PATH.exists():
    try:
        prev = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        out = [x for x in prev if x.get("vision_text") not in ("FRAME_MISSING", "NO_ANCHOR")]
        done = {x["report"] for x in out}
        print(f"[merge] 已加载 {len(prev)} 条, 有效 {len(out)}, 需重处理 {len(prev)-len(out)}", flush=True)
    except Exception:
        out = []
        done = set()
for sub in SUB:
    if sub_filter and sub != sub_filter:
        continue
    jd = ROOT / sub / "精编"
    count = 0
    for f in sorted(jd.glob("*.docx")):
        if any(k in f.name for k in BENCH_K):
            continue
        if limit and count >= limit:
            break
        if f.name in done:
            continue
        full = "\n".join(p.text for p in docx.Document(str(f)).paragraphs)
        # 目录: 取"源静帧目录"行
        dm = re.search(r"源静帧目录[:：]\s*(.+)", full)
        dp = Path(dm.group(1).strip().rstrip("/")) if dm else None
        # 时间锚: 正文第一条 [MM:SS] 分析点
        m = re.search(r"^\[(\d\d):(\d\d)\]\s+", full, flags=re.M)
        if not (dp and m):
            out.append({"sub": sub, "report": f.name, "frame": None, "vision_text": "NO_ANCHOR"})
            continue
        mm, ss = m.group(1), m.group(2)
        sec = int(mm) * 60 + int(ss)
        # 统一新格式: frame_{sec+1:06d}_{hms}
        h, rem = divmod(sec, 3600)
        fm2, fss = divmod(rem, 60)
        cand = dp / f"frame_{sec+1:06d}_{h:02d}h{fm2:02d}m{fss:02d}s000ms.jpg"
        if not (cand and cand.exists()) and dp and dp.exists():
            # 开荒合并: 帧在子目录内, 找含该秒的子目录帧(排除 contact_sheets/_ 前缀)
            found = None
            for sd in sorted([x for x in dp.iterdir() if x.is_dir()]):
                if "contact_sheets" in sd.name or sd.name.startswith("_"):
                    continue
                f2 = sd / f"frame_{sec+1:06d}_{h:02d}h{fm2:02d}m{fss:02d}s000ms.jpg"
                if f2.exists():
                    found = f2
                    break
            if found is None:
                subs = [x for x in dp.iterdir() if x.is_dir() and "contact_sheets" not in x.name and not x.name.startswith("_")]
                ff = sorted(subs[0].glob("*.jpg")) if subs else []
                found = ff[0] if ff else None
            cand = found
        if not (cand and cand.exists()):
            out.append({"sub": sub, "report": f.name, "frame": str(cand), "vision_text": "FRAME_MISSING"})
            continue
        # 调视觉模型
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                sys.argv = ["vision_glm.py", str(cand), PROMPT]
                vg.main()
            text = buf.getvalue().strip()
        except SystemExit:
            text = buf.getvalue().strip() or "EXIT"
        except Exception as e:
            text = f"ERR {e!r}"
        out.append({"sub": sub, "report": f.name, "frame": str(cand), "vision_text": text[:500]})
        count += 1
        print(f"[{sub}] {f.name[:36]} -> {len(text)}字", flush=True)
        save_json(out)  # 增量落盘, 崩溃不丢已处理结果

save_json(out)
print(f"\nDONE {len(out)} 份 -> {JSON_PATH}")
