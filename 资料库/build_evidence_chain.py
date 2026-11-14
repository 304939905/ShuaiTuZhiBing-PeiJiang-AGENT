# -*- coding: utf-8 -*-
"""
构建「证据链目录」：在现有索引基础上，把每份报告 ↔ 静帧图包 ↔ 源视频 ↔ 转写 json 串起来。
不移动任何文件，纯扫描+匹配+生成索引。覆盖全部子项目。
输出：
  D:/Desktop/shandou/资料库/evidence_chain.json   (机器可读，供 AI 溯源)
  D:/Desktop/shandou/资料库/evidence_chain.md     (人可读，按子项目分组)
"""
import os, re, json

ROOT = "D:/Desktop/shandou"
OUT_JSON = os.path.join(ROOT, "资料库", "evidence_chain.json")
OUT_MD   = os.path.join(ROOT, "资料库", "evidence_chain.md")

# 子项目定义：report_dir 是锚点（精编报告所在）；其余是待匹配资产根
# 归置后（2026-08-19）：精编报告在 报告库/<子项目>/精编/，旧版在 报告库/<子项目>/{完整版,逐帧1秒版}/
# 视频/静帧/转写 保持原位（按视频分组的干净输入源，不移动）
SUBPROJECTS = {
    "抖音旧56": {
        "report_dir":   os.path.join(ROOT, "报告库", "旧56项目", "精编"),
        "video_dirs":  [os.path.join(ROOT, "抖音")],
        "frames_dir":   os.path.join(ROOT, "抖音_frames_dense_1s"),
        "transcript_dir": os.path.join(ROOT, "抖音_transcripts"),
    },
    "开荒": {
        "report_dir":   os.path.join(ROOT, "报告库", "开荒", "精编"),
        "video_dirs":  [os.path.join(ROOT, "抖音", "开荒")],
        "frames_dir":   os.path.join(ROOT, "抖音_frames_dense_1s", "开荒"),
        "transcript_dir": os.path.join(ROOT, "抖音_transcripts", "开荒"),
    },
    "赛季": {
        "report_dir":   os.path.join(ROOT, "报告库", "赛季", "精编"),
        "video_dirs":  [os.path.join(ROOT, "抖音", "赛季")],
        "frames_dir":   os.path.join(ROOT, "赛季_frames_dense_1s"),
        "transcript_dir": os.path.join(ROOT, "赛季_transcripts"),
    },
    "阵容新批": {
        "report_dir":   os.path.join(ROOT, "报告库", "阵容新批", "精编"),
        "video_dirs":  [os.path.join(ROOT, "抖音", "阵容")],
        "frames_dir":   os.path.join(ROOT, "抖音_frames_dense_1s"),
        "transcript_dir": os.path.join(ROOT, "抖音_transcripts"),
    },
}

# 旧版报告（完整学习报告 / 逐帧1秒版）所在目录，作为 alt 版本引用
ALT_DIRS = []
for _sub in ["旧56项目", "开荒", "赛季", "阵容新批"]:
    for _ver in ["完整版", "逐帧1秒版"]:
        ALT_DIRS.append(os.path.join(ROOT, "报告库", _sub, _ver))
ALT_SKIP_PREFIXES = ("_backup", "_pre", "_render", "_delivery")

SUFFIXES_REPORT = ["_精编学习报告.docx", "_精修学习报告.docx"]
RE_PORT = re.compile(r"_(?:精编|精修)学习报告\.docx$")
RE_TOP = re.compile(r"_top_0_\d+")
RE_VIDEO_PREFIX = re.compile(r"^video_")

def core_key(name: str) -> str:
    """归一化：去后缀、去 video_ 前缀、去 _top_0_N，保留 ... 截断标记。"""
    n = name
    for suf in (".docx", ".mp4", ".json", ".json.wav", ".wav"):
        if n.endswith(suf):
            n = n[: -len(suf)]
    n = RE_VIDEO_PREFIX.sub("", n)
    n = RE_TOP.sub("", n)
    n = n.strip()
    return n

def list_subdirs(base):
    """递归返回 base 下所有目录的相对(于ROOT)路径列表。"""
    out = []
    if not os.path.isdir(base):
        return out
    for dp, dn, fn in os.walk(base):
        for d in dn:
            out.append(os.path.join(dp, d))
    return out

def list_files(base, ext):
    out = []
    if not os.path.isdir(base):
        return out
    for dp, dn, fn in os.walk(base):
        # 跳过备份/遗留目录
        if any(part.startswith(("_backup", "_pre", "_render", "_delivery")) for part in dp.split(os.sep)):
            continue
        for f in fn:
            if f.lower().endswith(ext):
                out.append(os.path.join(dp, f))
    return out

def count_jpg(d):
    if not os.path.isdir(d):
        return 0
    return sum(1 for f in os.listdir(d) if f.lower().endswith(".jpg"))

def find_frames(frames_dir, report_base):
    """在 frames_dir 下找与报告同 core-key 的帧目录。"""
    ck = core_key(report_base)
    cands = []
    for d in list_subdirs(frames_dir):
        if core_key(os.path.basename(d)) == ck:
            cands.append(d)
    if not cands:
        return None
    if len(cands) == 1:
        return cands[0]
    # 多候选：优先与报告全名（含 _top_0_N）完全一致的
    for d in cands:
        if os.path.basename(d) == report_base:
            return d
    return cands[0]

def find_video(video_dirs, report_base):
    ck = core_key(report_base)
    for vd in video_dirs:
        for f in list_files(vd, ".mp4"):
            if core_key(os.path.basename(f)) == ck:
                return f
    return None

def find_transcript(transcript_dir, report_base):
    ck = core_key(report_base)
    for f in list_files(transcript_dir, ".json"):
        if f.lower().endswith(".json.wav"):
            continue
        if core_key(os.path.basename(f)) == ck:
            return f
    return None

ALT_SUFFIXES = ["_完整学习报告", "_逐帧深度学习报告_1秒版", "_逐帧深度学习报告", "_完整学习报告_1秒版"]

def alt_core(name: str) -> str:
    """旧版报告名归一：先去报告类型后缀，再走通用 core_key。"""
    n = name
    if n.lower().endswith(".docx"):
        n = n[:-5]
    for s in ALT_SUFFIXES:
        if n.endswith(s):
            n = n[: -len(s)]
    return core_key(n)

def find_alt_reports(alt_dirs, report_base):
    """搜索旧版报告（完整学习报告 / 逐帧1秒版），作为同标题的 alt 版本。"""
    ck = core_key(report_base)
    alts = []
    for ad in alt_dirs:
        for f in list_files(ad, ".docx"):
            bn = os.path.basename(f)
            if RE_PORT.search(bn):
                continue  # 跳过精编本身
            if alt_core(bn) == ck:
                alts.append(f)
    return alts

def contact_sheet_dir(frames_dir):
    d = os.path.join(frames_dir, "contact_sheets")
    return d if os.path.isdir(d) else None

def main():
    records = []
    for sp_name, sp in SUBPROJECTS.items():
        rd = sp["report_dir"]
        if not os.path.isdir(rd):
            continue
        report_files = sorted(list_files(rd, ".docx"))
        for rf in report_files:
            bn = os.path.basename(rf)
            m = RE_PORT.search(bn)
            if not m:
                continue  # 只锚定精编报告
            base = bn[: m.start()]  # 去 _精编学习报告
            frames = find_frames(sp["frames_dir"], base)
            video = find_video(sp["video_dirs"], base)
            trans = find_transcript(sp["transcript_dir"], base)
            alts = find_alt_reports(ALT_DIRS, base)
            rec = {
                "subproject": sp_name,
                "title": base,
                "report": rf,
                "frames_dir": frames,
                "frame_count": count_jpg(frames) if frames else 0,
                "video": video,
                "transcript": trans,
                "alt_reports": alts,
                "contact_sheet_dir": contact_sheet_dir(frames) if frames else None,
            }
            records.append(rec)

    # 覆盖率统计
    def cnt(pred):
        return sum(1 for r in records if pred(r))
    stats = {
        "total_reports": len(records),
        "with_frames": cnt(lambda r: r["frames_dir"]),
        "with_video": cnt(lambda r: r["video"]),
        "with_transcript": cnt(lambda r: r["transcript"]),
        "with_alt_version": cnt(lambda r: r["alt_reports"]),
    }

    # 写 JSON
    out = {"generated_by": "build_evidence_chain.py", "stats": stats, "records": records}
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # 写 MD
    lines = []
    lines.append("# 证据链目录（报告 ↔ 静帧图包 ↔ 源视频 ↔ 转写）\n")
    lines.append("> 本目录在现有 `reports_index.md` / `video_index.md` 基础上新增，专供 AI 或人工**快速溯源**：\n"
                 "> 拿到任一份报告 → 一键定位其静帧图包、源视频、音频转写，反向亦可。\n")
    lines.append("## 覆盖率概览\n")
    lines.append(f"- 精编报告总数：**{stats['total_reports']}**")
    lines.append(f"- 能定位静帧图包：{stats['with_frames']}")
    lines.append(f"- 能定位源视频：{stats['with_video']}")
    lines.append(f"- 能定位音频转写：{stats['with_transcript']}")
    lines.append(f"- 另有旧版报告（完整/逐帧1秒）可参照：{stats['with_alt_version']}\n")
    lines.append("> 说明：`null` 表示本脚本按当前目录和名称规则未匹配到资产；不能据此断定原文件不存在。报告收录不代表内容已通过审核。\n")

    # 按子项目分组
    by_sp = {}
    for r in records:
        by_sp.setdefault(r["subproject"], []).append(r)
    rel = lambda p: os.path.relpath(p, ROOT).replace("\\", "/") if p else None
    for sp_name in SUBPROJECTS:
        recs = by_sp.get(sp_name, [])
        if not recs:
            continue
        lines.append(f"## {sp_name}（{len(recs)} 份）\n")
        lines.append("| # | 报告标题 | 静帧图包(帧数) | 源视频 | 音频转写 | 旧版报告 |")
        lines.append("|---|---|---|---|---|---|")
        for i, r in enumerate(recs, 1):
            fdir = rel(r["frames_dir"])
            fcell = f"{fdir} ({r['frame_count']})" if fdir else "—"
            vcell = rel(r["video"]) or "—"
            tcell = rel(r["transcript"]) or "—"
            acell = str(len(r["alt_reports"])) if r["alt_reports"] else "—"
            title = r["title"]
            if len(title) > 28:
                title = title[:28] + "…"
            lines.append(f"| {i} | {title} | {fcell} | {vcell} | {tcell} | {acell} |")
        lines.append("")

    # 附录：每条完整路径（便于复制）
    lines.append("## 附录：完整路径明细\n")
    for sp_name in SUBPROJECTS:
        recs = by_sp.get(sp_name, [])
        if not recs:
            continue
        lines.append(f"### {sp_name}\n")
        for r in recs:
            lines.append(f"- **{r['title']}**")
            lines.append(f"  - 报告: `{rel(r['report'])}`")
            lines.append(f"  - 静帧: `{rel(r['frames_dir'])}` （{r['frame_count']} 帧）" if r["frames_dir"] else "  - 静帧: —")
            lines.append(f"  - 视频: `{rel(r['video'])}`" if r["video"] else "  - 视频: —")
            lines.append(f"  - 转写: `{rel(r['transcript'])}`" if r["transcript"] else "  - 转写: —")
            if r["alt_reports"]:
                for a in r["alt_reports"]:
                    lines.append(f"  - 旧版: `{rel(a)}`")
        lines.append("")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # 控制台覆盖率
    print("=== 证据链构建完成 ===")
    print(f"输出: {rel(OUT_JSON)} | {rel(OUT_MD)}")
    print(f"统计: {json.dumps(stats, ensure_ascii=False)}")
    # 打印缺失项，便于人工核对
    miss = [r for r in records if not (r["frames_dir"] and r["video"] and r["transcript"])]
    if miss:
        print(f"\n⚠ 存在缺口的报告 {len(miss)} 份：")
        for r in miss:
            lack = []
            if not r["frames_dir"]: lack.append("帧")
            if not r["video"]: lack.append("视频")
            if not r["transcript"]: lack.append("转写")
            print(f"  - [{r['subproject']}] {r['title'][:30]}  缺: {','.join(lack)}")

if __name__ == "__main__":
    main()
