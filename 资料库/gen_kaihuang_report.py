# -*- coding: utf-8 -*-
"""把 6 份开荒逐帧 JSON 合并渲染成 1 份《开荒专题》深度学习报告。"""
import os, io, json, sys, traceback
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

BASE = r"D:\Desktop\shandou"
JSON_DIR = os.path.join(BASE, "资料库", "frame_json_kaihuang")
FRAMES_ROOT = os.path.join(BASE, "抖音_frames_dense_1s")
OUT_DIR = os.path.join(BASE, "学习汇报")
FONT = "Microsoft YaHei"

# 按「理论 → 选将 → 实操 → 答疑 → 反面教材 → 修车」排序
ORDER = [
    ("video_率土开荒焚诀，【开荒的基本原理】..._top_0_2",
     "理论总纲", "开荒的基本原理"),
    ("video_萌新第一课：哪些武将是核心，哪些..._top_0_2",
     "选将速查", "萌新第一课：武将优先级"),
    ("开荒焚决来了,上线三次，开荒完事! 10分钟超详细实录开荒教学，三部上线开荒法，震撼来袭!",
     "实操主篇", "三次上线开荒法（大黄乐顺风局）"),
    ("开荒期常见问题汇总 ，一篇全看懂，兄弟们速速来看！",
     "答疑篇", "开荒期常见问题汇总"),
    ("史上最大开荒滑铁卢 这里是地狱吗？",
     "失败复盘", "史上最大开荒滑铁卢（关妹甄洛严颜·上）"),
    ("关妹甄洛严颜开荒实录！ 翻车翻炸了咋补救？接着看！",
     "翻车补救", "关妹甄洛严颜开荒实录（下）：翻车后怎么修车"),
]
CN = "一二三四五六七八九十"


def _set_font(run, size=10.5, bold=False, italic=False, color=None):
    run.font.name = FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = color


def add_heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for r in p.runs:
        r.font.name = FONT
        r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        r.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    return p


def add_para(doc, text, bold=False, italic=False, size=10.5, color=None, align=None):
    p = doc.add_paragraph()
    _set_font(p.add_run(text), size, bold, italic, color)
    p.paragraph_format.space_after = Pt(6)
    if align is not None:
        p.alignment = align
    return p


def add_bullet(doc, text, indent=0):
    p = doc.add_paragraph(style="List Bullet")
    _set_font(p.add_run(text))
    p.paragraph_format.space_after = Pt(4)
    if indent:
        p.paragraph_format.left_indent = Inches(0.25 * (indent + 1))
    return p


def embed_image(doc, path, caption, width=5.2):
    if not os.path.exists(path):
        return False
    doc.add_picture(path, width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_font(cap.add_run(caption), 9, italic=True, color=RGBColor(0x60, 0x60, 0x60))
    cap.paragraph_format.space_after = Pt(10)
    return True


def add_table(doc, headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        _set_font(c.paragraphs[0].add_run(h), 10, bold=True)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            _set_font(cells[i].paragraphs[0].add_run(str(v)), 9.5)
    return t


def fmt_dur(sec):
    sec = int(round(float(sec)))
    return "%02d:%02d" % (sec // 60, sec % 60)


def fov_lines(fov):
    """frame_only_value 可能是 str 或 dict（Q&A / 错误条目），统一成文本行。"""
    out = []
    for v in fov:
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, dict):
            if "question" in v:
                head = "Q：" + str(v.get("question", ""))
                pts = v.get("answer_points") or []
                body = "；".join(str(x) for x in pts)
                ts = "、".join(v.get("timestamps") or [])
                out.append("%s　A：%s%s" % (head, body, ("（%s）" % ts) if ts else ""))
            else:
                parts = []
                for k, val in v.items():
                    if k in ("frames",):
                        continue
                    vs = val if isinstance(val, str) else "；".join(str(x) for x in val) \
                        if isinstance(val, list) else str(val)
                    parts.append("%s：%s" % (k, vs))
                out.append("　".join(parts))
        else:
            out.append(str(v))
    return out


def main():
    docs = []
    for stem, tag, disp in ORDER:
        p = os.path.join(JSON_DIR, stem + ".json")
        if not os.path.exists(p):
            print("MISS %s" % stem[:40]); continue
        with io.open(p, "r", encoding="utf-8") as f:
            docs.append((tag, disp, json.load(f)))
    if len(docs) != 6:
        print("WARN 只读到 %d 份 JSON" % len(docs))

    tot_dur = sum(float(d["duration_s"]) for _, _, d in docs)
    tot_frames = sum(int(d.get("frame_count") or round(float(d["duration_s"]))) for _, _, d in docs)
    tot_shots = sum(len(s.get("frames") or []) for _, _, d in docs for s in d["timeline"])

    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = FONT
    st._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    st.font.size = Pt(10.5)
    missing = []
    C = WD_ALIGN_PARAGRAPH.CENTER

    # ---------- 封面 ----------
    add_para(doc, "率土之滨 开荒专题", bold=True, size=22, align=C)
    add_para(doc, "6 个视频合并 · 逐帧深度学习报告", bold=True, size=15, align=C)
    add_para(doc, "报告类型：1 秒/帧逐帧版（合并专题）", size=11, align=C)
    add_para(doc, "覆盖视频：%d 个　|　总时长：%s　|　抽帧：%d 帧（1 秒/帧）"
             % (len(docs), fmt_dur(tot_dur), tot_frames), size=10.5, align=C)
    add_para(doc, "嵌入证据帧：%d 张　|　生成日期：%s"
             % (tot_shots, docs[0][2].get("report_date", "")), size=10.5, align=C)
    add_para(doc, "方法：faster-whisper 音频转写 + 每 1 秒抽 1 帧 + 逐帧画面判读 + 黑话查证",
             size=10, align=C)
    doc.add_page_break()

    # ---------- 一、专题总览 ----------
    add_heading(doc, "一、专题总览与阅读地图", level=1)
    add_para(doc, "本专题把 6 期开荒视频合并为一份报告，按「理论 → 选将 → 实操 → 答疑 → "
                  "反面教材 → 补救」的学习顺序重排，而非按发布时间。6 期内容互补，"
                  "单看任何一期都不完整。", bold=True)
    rows = []
    for i, (tag, disp, d) in enumerate(docs, 1):
        rows.append([str(i), tag, disp, fmt_dur(d["duration_s"]),
                     str(d.get("frame_count") or round(float(d["duration_s"])))])
    add_table(doc, ["序", "定位", "内容", "时长", "帧数"], rows)
    doc.add_paragraph()

    add_heading(doc, "1.1 六期各自解决什么问题", level=2)
    for i, (tag, disp, d) in enumerate(docs, 1):
        add_para(doc, "第 %d 期【%s】%s" % (i, tag, disp), bold=True)
        add_para(doc, d["summary"].get("one_line", ""))

    # ---------- 二、跨集核心结论 ----------
    doc.add_page_break()
    add_heading(doc, "二、开荒核心结论（跨集汇总）", level=1)
    add_para(doc, "以下按功能归类，把 6 期里画面可核实的关键信息汇总在一起，"
                  "标注来源期数，方便对照原片复核。")
    for i, (tag, disp, d) in enumerate(docs, 1):
        vo = d["summary"].get("visual_only") or []
        if not vo:
            continue
        add_heading(doc, "2.%d 来自【%s】%s" % (i, tag, disp), level=2)
        for b in vo:
            add_bullet(doc, b)

    # ---------- 三、对既有报告的修正 ----------
    doc.add_page_break()
    add_heading(doc, "三、逐帧判读对既有音频版报告的修正", level=1)
    add_para(doc, "既有《开荒专题》报告基于稀疏取帧 + 音频转写，存在音译错误与数值缺失。"
                  "下列修正均有单帧画面证据。")
    n_corr = 0
    for i, (tag, disp, d) in enumerate(docs, 1):
        corr = d["summary"].get("corrections") or []
        if not corr:
            continue
        add_heading(doc, "3.%d 【%s】%s" % (i, tag, disp), level=2)
        for c in corr:
            add_para(doc, c, color=RGBColor(192, 0, 0))
            n_corr += 1
    if n_corr == 0:
        add_para(doc, "本次未发现需要修正的内容。", italic=True)

    # ---------- 四、方法 ----------
    doc.add_page_break()
    add_heading(doc, "四、逐帧分析方法", level=1)
    add_para(doc, "1. 以 1 秒为步长对 6 个视频（合计 %s）均匀抽帧，共 %d 帧，覆盖全片无遗漏。"
             % (fmt_dur(tot_dur), tot_frames))
    add_para(doc, "2. 全部帧制作成 contact sheet（每张 40 帧，5×8 排列，带秒级时间戳），逐格判读。")
    add_para(doc, "3. 画面信息与 faster-whisper 音频转写逐句对齐，识别转写错误并补充视觉证据。")
    add_para(doc, "4. 选取 %d 张最具信息量的单帧嵌入本报告；其余帧作为备查证据保留在 "
                  "抖音_frames_dense_1s\\开荒\\ 下。" % tot_shots)
    add_para(doc, "5. 画面中出现的率土黑话/术语，已在资料库「名词概念.md」中查证补齐。")
    add_para(doc, "6. 6 期分别由独立判读产出结构化 JSON，再由本脚本合并渲染，"
                  "各期结论保持可溯源到具体帧文件。")

    # ---------- 五~十、各集时间轴 ----------
    for i, (tag, disp, d) in enumerate(docs, 1):
        doc.add_page_break()
        idx = CN[i + 3] if (i + 3) < len(CN) else str(i + 4)
        add_heading(doc, "%s、【%s】%s" % (idx, tag, disp), level=1)
        add_para(doc, "源视频：%s" % d["video_title"], size=9.5,
                 color=RGBColor(0x60, 0x60, 0x60))
        add_para(doc, "时长 %s　|　抽帧 %s 帧　|　分辨率 %s"
                 % (fmt_dur(d["duration_s"]),
                    d.get("frame_count") or round(float(d["duration_s"])),
                    d.get("resolution", "-")), size=9.5,
                 color=RGBColor(0x60, 0x60, 0x60))
        add_para(doc, d["summary"].get("one_line", ""), bold=True)

        add_heading(doc, "%s.1 逐帧时间轴与画面解读" % (i + 4), level=2)
        frames_dir = os.path.join(FRAMES_ROOT, d["frames_dir"])
        for sec in d["timeline"]:
            add_heading(doc, "%s　%s" % (sec["range"], sec["title"]), level=3)
            for fr in sec.get("frames") or []:
                p = os.path.join(frames_dir, fr["file"])
                if not embed_image(doc, p, "%s | %s" % (fr["ts"], fr["desc"])):
                    missing.append(fr["file"])

        fov = d.get("frame_only_value") or []
        if fov:
            add_heading(doc, "%s.2 本期画面独有价值（音频听不出）" % (i + 4), level=2)
            for line in fov_lines(fov):
                add_bullet(doc, line)

        cmp_rows = d.get("comparison") or []
        if cmp_rows:
            add_heading(doc, "%s.3 与既有音频版报告对照" % (i + 4), level=2)
            add_table(doc, ["信息点", "既有音频版", "1 秒/帧逐帧版", "差异说明"],
                      [[r.get("item", ""), r.get("old", ""), r.get("new", ""),
                        r.get("diff", "")] for r in cmp_rows])

    # ---------- 十一、局限 ----------
    doc.add_page_break()
    add_heading(doc, "十一、局限与查不到 / 无法确认", level=1)
    add_para(doc, "以下内容画面未给出或无法确认，如实列出，不做推测。")
    for i, (tag, disp, d) in enumerate(docs, 1):
        lim = d.get("limitations") or []
        if not lim:
            continue
        add_para(doc, "【%s】%s" % (tag, disp), bold=True)
        for l in lim:
            add_bullet(doc, l)

    # ---------- 十二、术语与来源 ----------
    add_heading(doc, "十二、术语与证据索引", level=1)
    gl = []
    for _, _, d in docs:
        for g in d.get("glossary") or []:
            name = g if isinstance(g, str) else (g.get("term") or g.get("name") or str(g))
            if name not in gl:
                gl.append(name)
    if gl:
        add_para(doc, "本专题涉及术语 %d 条（释义见资料库「名词概念.md」）：" % len(gl), bold=True)
        add_para(doc, "、".join(gl))
    add_para(doc, "证据来源：", bold=True)
    seen = set()
    for _, _, d in docs:
        for s in d.get("sources") or []:
            ss = s if isinstance(s, str) else str(s)
            if ss in seen:
                continue
            seen.add(ss)
            add_bullet(doc, ss)

    out = os.path.join(OUT_DIR, "开荒专题（6 视频合并）_逐帧深度学习报告_1秒版.docx")
    doc.save(out)
    size = os.path.getsize(out) // 1024
    print("OK   %s" % os.path.basename(out))
    print("     %d 集  %d 图  %dKB  修正 %d 条  术语 %d 条" % (len(docs), tot_shots, size, n_corr, len(gl)))
    if missing:
        print("     缺图 %d: %s" % (len(missing), missing[:5]))
    else:
        print("     缺图 0")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
