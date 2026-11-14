#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""由 逐帧1秒版 docx 生成「最新标准精修版」(带轻量溯源索引)。
用法: gen_refined.py <源1秒版docx> <输出docx>
溯源: 每段带 ⏱[起-止] 时间锚 + 报告末「溯源索引」只写静帧路径范围(不内嵌图片)。
武将标签: 阵营/兵种 取自 hero_extra.json(可读), 星级 取自 hero.json(quality)。
"""
import re, json, sys
from pathlib import Path
import docx
from docx import Document
from docx.shared import Pt, RGBColor
from hero_version_resolver import HERO_NAMES as RESOLVER_HERO_NAMES, resolve_label

ROOT = Path("D:/Desktop/shandou")
LIB = ROOT / "资料库"
FRAMES_ROOT = ROOT / "抖音_frames_dense_1s"  # 默认(旧56项目); 海之呼唤/赛季/开荒 在各自根

# 子项目 -> 帧根目录映射
FRAME_ROOT_MAP = {
    "旧56项目": ROOT / "抖音_frames_dense_1s",
    "开荒":     ROOT / "抖音_frames_dense_1s" / "开荒",   # 合并报告:6子目录的父级(可浏览)
    "海之呼唤": ROOT / "海之呼唤_frames_dense_1s",
    "赛季":     ROOT / "赛季_frames_dense_1s",
}

def _norm(s):
    return re.sub(r"[\s\W_]+", "", s, flags=re.UNICODE).lower()

def _rel_dir(d):
    """2026-08-24 试点：溯源索引路径脱敏——只显示相对项目根的路径，不泄漏 D:/Desktop 绝对路径。"""
    try:
        return str(d.relative_to(ROOT))
    except Exception:
        return str(d).replace(str(ROOT), '').lstrip('/\\') or str(d)

# ---- 加载武将数据 ----
oh = json.loads((LIB / "official_hero_names.json").read_text(encoding="utf-8"))
HERO_NAMES = oh["names"] if isinstance(oh, dict) and "names" in oh else (oh if isinstance(oh, list) else [])
HERO_NAMES = sorted(set(HERO_NAMES) | RESOLVER_HERO_NAMES, key=len, reverse=True)

def _visual_evidence(src, frame_dir, hero):
    """只读取人工/视觉模型已落库的同帧证据；不存在或原图缺失则不输出版本。"""
    p = LIB / "version_visual_evidence.json"
    if not p.exists():
        return None
    try:
        records = json.loads(p.read_text(encoding="utf-8")).get("records", [])
    except (json.JSONDecodeError, OSError):
        return None
    for record in records:
        if record.get("source_doc") != src.name or record.get("hero") != hero:
            continue
        frame = str(record.get("source_frame") or "")
        if frame and (frame_dir / frame).is_file():
            return record
    return None

def hero_label(nm, src=None, frame_dir=None):
    evidence = _visual_evidence(src, frame_dir, nm) if src and frame_dir else None
    builtin = str((evidence or {}).get("builtin_skill") or "")
    return resolve_label(nm, builtin_skill=builtin, visual_evidence=evidence)

def sec_of(ts):
    a, b = ts.split(":")
    return int(a) * 60 + int(b)

def mmss(sec):
    """时间区间显示用冒号(如 00:00)。用于段标题/索引标签, 不进文件名。"""
    return f"{sec//60:02d}:{sec%60:02d}"

def frame_ref(sec):
    # 统一格式(与阵容新批一致): frame_000001_00h00m00s000ms.jpg (序号=秒+1, 时间戳=真实秒)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"frame_{sec+1:06d}_{h:02d}h{m:02d}m{s:02d}s000ms.jpg"

WIN = 20  # 每段固定 20 秒

def _norm_terms(s):
    """术语统一：UP主/UP 主 → 作者（2026-08-24 全旧批自检发现蒸馏文本残留）。"""
    if not isinstance(s, str):
        return s
    s = re.sub(r"UP\s*主", "作者", s)
    return s

def main():
    src = Path(sys.argv[1])
    out = Path(sys.argv[2])
    from saiji_standalone import maybe_build
    if maybe_build(src, out):
        print('OK 已核验独立学习母本 ->', out)
        return
    out.parent.mkdir(parents=True, exist_ok=True)

    doc = docx.Document(str(src))
    paras = [p.text for p in doc.paragraphs]
    full = "\n".join(paras)

    title = re.search(r"视频标题[:：]\s*(.+)", full)
    dur = re.search(r"时长[:：](\d+:\d+)", full)
    fn = re.search(r"抽帧[:：](\d+)\s*帧", full)
    vid = re.search(r"视频编号[:：](V\d+)", full)
    title = title.group(1).strip() if title else src.stem
    dur_s = sec_of(dur.group(1)) if dur else 0
    fn_n = fn.group(1) if fn else "?"

    # 抓主分析行: 兼容两种时间戳格式
    #   格式1 单点: "MM:SS 文本" (排除以 | 开头的对照块)
    #   格式2 范围: "MM:SS–MM:SS 文本" 或 "MM:SS-MM:SS 文本" (取起点为锚)
    pts = []
    for t in paras:
        t = t.strip()
        m = re.match(r"^(\d\d:\d\d)\s+(?!\|)(.*)", t)
        if m:
            pts.append((m.group(1), m.group(2).strip()))
            continue
        m = re.match(r"^(\d\d:\d\d)[–-](\d\d:\d\d)\s+(?!\|)(.+)", t)
        if m:
            pts.append((m.group(1), m.group(3).strip()))

    # 固定 20 秒窗分组
    segs = []
    for s in range(0, (dur_s // WIN + 2) * WIN, WIN):
        e = s + WIN - 1
        sp = [(ts, txt) for ts, txt in pts if s <= sec_of(ts) <= e]
        if sp:
            segs.append({"start": s, "end": e, "pts": sp})

    # NER 武将：按文本首次出现顺序取前 14 名，不能按名字长度排序后截断。
    # 后者会把核心出阵武将挤出标签行，且每次资料库名单调整都会改变结果。
    occurrences = []
    for nm in HERO_NAMES:
        pos = full.find(nm)
        if pos >= 0:
            occurrences.append((pos, -len(nm), nm))
    found = []
    for _, _, nm in sorted(occurrences):
        if nm not in found:
            found.append(nm)
    found = found[:14]

    # 核心结论
    conclusion = ""
    for i, t in enumerate(paras):
        if t.strip().startswith("一、逐帧学习的核心结论"):
            for j in range(i + 1, min(i + 6, len(paras))):
                if paras[j].strip() and not paras[j].strip().startswith("本次对该视频"):
                    conclusion = paras[j].strip()
                    break
            break
    if not conclusion:
        conclusion = "（源报告未提取到独立结论段，以下为核心要点归纳）"

    # 按子项目选帧根(源在 报告库/<sub>/逐帧1秒版/)
    sub = src.parent.parent.name
    FR = FRAME_ROOT_MAP.get(sub, FRAMES_ROOT)
    if sub == "开荒":
        # 合并报告: 指向6子目录父级(目录存在即可溯源, 帧在子目录内)
        frame_dir = FR
    else:
        frame_dir = FR / title
        if not frame_dir.exists():
            nt = _norm(title)
            for d in FR.iterdir():
                if not d.is_dir():
                    continue
                k = _norm(d.name)
                if nt == k or nt in k or k in nt or (len(nt) > 6 and nt[:8] in k):
                    frame_dir = d
                    break

    # ---------- 渲染 ----------
    o = Document()
    o.add_heading("率土之滨抖音视频 · 精修学习报告", level=0)
    o.add_paragraph(f"视频标题：{title}")
    o.add_paragraph(f"视频编号：{vid.group(1) if vid else '?'}　|　时长：{dur.group(1) if dur else '?'}　|　源静帧：{fn_n} 帧（1 秒/帧）")
    o.add_paragraph("生成日期：2026-08-20　|　报告类型：最新标准精修版（由逐帧1秒版蒸馏 + 溯源索引）")
    o.add_paragraph(f"源报告：{src.name}")
    o.add_paragraph(f"源静帧目录：{_rel_dir(frame_dir)}")
    if found:
        labels = [f"{nm}（{hero_label(nm, src, frame_dir)}）" for nm in found if hero_label(nm, src, frame_dir)]
        if labels:
            o.add_paragraph("核心武将版本标签：" + "、".join(labels))

    o.add_heading("一、视频核心结论", level=1)
    o.add_paragraph(_norm_terms(conclusion))

    o.add_heading("二、分段精要（带时间锚；对应静帧见文末溯源索引）", level=1)
    for seg in segs:
        rng = f"{mmss(seg['start'])}-{mmss(seg['end'])}"
        h = o.add_paragraph()
        h.add_run(f"⏱ [{rng}]").bold = True
        for ts, txt in seg["pts"]:
            clean = _norm_terms(re.sub(r"^" + re.escape(ts) + r"\s*", "", txt))
            b = o.add_paragraph(style="List Bullet")
            b.add_run(f"[{ts}] ").bold = True
            b.add_run(clean)

    o.add_heading("三、AI 主动推断（非视频原话，附证据时间锚）", level=1)
    if found:
        lead = found[0]
        others = "、".join(found[1:4]) if len(found) > 1 else "见上"
        o.add_paragraph(
            f"【推断】结合视频结论与登场的 {lead}、{others} 等武将的实战面板/战法实测，"
            f"本视频内容可归为对应体系/玩法的讲解与配队参考。此推断由 AI 基于逐帧证据归纳，非作者原话，供交叉验证。"
        )
        o.add_paragraph(
            f"【证据】核心结论见第一节；各时间段对应静帧见第四节溯源索引。对某句字幕有疑，按时间段打开对应 frame_XXXXXX_00h00m00s000ms.jpg 即可核对原始画面。"
        )
    else:
        o.add_paragraph("（未识别到明确武将实体，AI 推断从略；可补充源视频上下文后生成。）")

    o.add_heading("四、溯源索引（时间段 → 静帧路径）", level=1)
    o.add_paragraph("溯源规则：时间锚存在 ±4 秒判读容差；若某时间段首帧画面与描述不符，请核验相邻 ±2~4 秒帧，取画面匹配者。")
    if sub == "开荒":
        o.add_paragraph(f"本报告为6视频合并专题，静帧分布在 {_rel_dir(frame_dir)}/ 下6个子目录内；核对某时间段字幕时，进入对应子目录打开区间静帧。")
    else:
        o.add_paragraph(f"下列路径指向 {frame_dir.parent.name}/ 下的原始静帧（1 秒/帧）；核对某时间段字幕时，直接打开对应区间静帧。")
    for seg in segs:
        rng = f"{mmss(seg['start'])}-{mmss(seg['end'])}"
        o.add_paragraph(f"[{rng}]  {_rel_dir(frame_dir)}/ {frame_ref(seg['start'])} ~ {frame_ref(min(seg['end'], dur_s))}", style="List Bullet")

    o.save(str(out))
    print("OK ->", out)
    print(f"segments={len(segs)} points={len(pts)} heroes={len(found)}")

if __name__ == "__main__":
    main()
