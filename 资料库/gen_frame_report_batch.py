#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据驱动的「1 秒/帧逐帧深度学习报告」批量渲染器。

用法：
    python gen_frame_report_batch.py                # 渲染 frame_json/ 下全部
    python gen_frame_report_batch.py a.json b.json  # 只渲染指定 JSON
"""
import os
import sys
import glob
import json
import io
import traceback

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn

BASE = r"D:\Desktop\shandou"
JSON_DIR = os.path.join(BASE, "资料库", "frame_json")
FRAMES_ROOT = os.path.join(BASE, "抖音_frames_dense_1s")
OUT_DIR = os.path.join(BASE, "学习汇报")
FONT = "Microsoft YaHei"


# ---------------- docx helpers ----------------
def _set_font(run, size=10.5, bold=False, italic=False, color=None):
    run.font.name = FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = color


def add_heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        run.font.name = FONT
        run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    return p


def add_para(doc, text, bold=False, italic=False, size=10.5, color=None, align=None):
    p = doc.add_paragraph()
    _set_font(p.add_run(text), size, bold, italic, color)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    p.paragraph_format.space_after = Pt(6)
    if align:
        p.alignment = align
    return p


def add_bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    _set_font(p.add_run(text))
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    p.paragraph_format.space_after = Pt(4)
    return p


def embed_image(doc, path, caption, width=5.2):
    if not os.path.exists(path):
        add_para(doc, f"[图缺失: {os.path.basename(path)} | {caption}]",
                 italic=True, color=RGBColor(255, 0, 0))
        return False
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(path, width=Inches(width))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_font(cap.add_run(caption), 9, color=RGBColor(80, 80, 80))
    cap.paragraph_format.space_after = Pt(10)
    return True


def add_table(doc, headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        _set_font(c.paragraphs[0].add_run(h), 9.5, bold=True)
    for r in rows:
        cells = t.add_row().cells
        for i, v in enumerate(r):
            cells[i].text = ""
            _set_font(cells[i].paragraphs[0].add_run(str(v)), 9)
    return t


def fmt_dur(sec):
    sec = int(round(float(sec)))
    return f"{sec // 60:02d}:{sec % 60:02d}"


# ---------------- renderer ----------------
def build(data):
    title = data["video_title"]
    frames_dir = os.path.join(FRAMES_ROOT, data["frames_dir"])

    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = FONT
    st._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    st.font.size = Pt(10.5)

    missing = []

    # -------- Cover --------
    C = WD_ALIGN_PARAGRAPH.CENTER
    add_para(doc, "率土之滨抖音视频 逐帧深度学习报告", bold=True, size=18, align=C)
    add_para(doc, f"视频标题：{title}", bold=True, size=13, align=C)
    add_para(doc, "报告类型：1 秒/帧逐帧版 + 与既有音频版报告对照", size=11, align=C)
    add_para(doc, f"视频编号：{data.get('video_id','-')}　|　时长：{fmt_dur(data['duration_s'])}"
                  f"　|　抽帧：{data['frame_count']} 帧（1 秒/帧）", size=10.5, align=C)
    add_para(doc, f"分辨率：{data.get('resolution','-')}　|　生成日期：{data.get('report_date','')}",
             size=10.5, align=C)
    add_para(doc, "方法：faster-whisper 音频转写 + 每 1 秒抽 1 帧 + 逐帧画面判读 + 黑话查证",
             size=10, align=C)
    doc.add_page_break()

    # -------- 1. Core conclusions --------
    add_heading(doc, "一、逐帧学习的核心结论", level=1)
    add_para(doc, data["summary"]["one_line"], bold=True)
    add_para(doc, f"本次对该视频进行 1 秒/帧密集抽帧（{data['frame_count']} 帧，覆盖全片 "
                  f"{fmt_dur(data['duration_s'])}），逐帧判读画面中的 UI、武将卡、战法图标、"
                  f"战报、字幕与文字提示，并与音频转写逐句对齐。")

    vo = data["summary"].get("visual_only") or []
    if vo:
        add_heading(doc, "1.1 音频无法确认、画面可核实的关键信息", level=2)
        for b in vo:
            add_bullet(doc, b)

    corr = data["summary"].get("corrections") or []
    if corr:
        add_heading(doc, "1.2 对既有报告的修正", level=2)
        for c in corr:
            add_para(doc, c, color=RGBColor(192, 0, 0))

    # -------- 2. Method --------
    doc.add_page_break()
    add_heading(doc, "二、逐帧分析方法", level=1)
    n_shots = sum(len(s.get("frames") or []) for s in data["timeline"])
    add_para(doc, f"1. 以 1 秒为步长对 {fmt_dur(data['duration_s'])} 的视频均匀抽帧，"
                  f"共 {data['frame_count']} 帧，覆盖全片无遗漏。")
    add_para(doc, f"2. 将全部帧制作成 {data.get('sheet_count','若干')} 张 contact sheet"
                  f"（每张 40 帧，5×8 排列，带秒级时间戳），逐格判读画面信息。")
    add_para(doc, "3. 将画面信息与 faster-whisper 音频转写逐句对齐，识别转写错误并补充视觉证据。")
    add_para(doc, f"4. 选取 {n_shots} 张最具信息量的单帧嵌入本报告；"
                  f"其余帧作为备查证据保留在 抖音_frames_dense_1s\\{data['frames_dir']}\\ 下。")
    add_para(doc, "5. 对画面中出现的率土黑话/术语，已在资料库「名词概念.md」中查证补齐。")

    # -------- 3. Timeline --------
    doc.add_page_break()
    add_heading(doc, "三、逐帧时间轴与画面解读", level=1)
    for sec in data["timeline"]:
        add_heading(doc, f"{sec['range']}　{sec['title']}", level=2)
        for fr in sec.get("frames") or []:
            p = os.path.join(frames_dir, fr["file"])
            ok = embed_image(doc, p, f"{fr['ts']} | {fr['desc']}")
            if not ok:
                missing.append(fr["file"])

    # -------- 4. Comparison --------
    cmp_rows = data.get("comparison") or []
    if cmp_rows:
        doc.add_page_break()
        add_heading(doc, "四、逐帧版 vs 既有音频版报告对照", level=1)
        add_para(doc, "既有报告基于稀疏取帧 + 音频转写；本版基于全片 1 秒/帧密集画面 + "
                      "音频转写 + 逐帧判读 + 术语查证。下表列出关键差异。")
        add_table(doc, ["信息点", "既有音频版报告", "1 秒/帧逐帧版（本版）", "差异说明"],
                  [[r["item"], r["old"], r["new"], r["diff"]] for r in cmp_rows])

    # -------- 5. Frame-only value --------
    fov = data.get("frame_only_value") or []
    if fov:
        doc.add_page_break()
        add_heading(doc, "五、逐帧版独有的新增价值", level=1)
        add_para(doc, "以下结论在仅听音频时难以得出，必须通过画面判读：")
        for v in fov:
            add_bullet(doc, v)

    # -------- 6. Limitations --------
    lim = data.get("limitations") or []
    add_heading(doc, "六、局限与查不到 / 无法确认", level=1)
    if lim:
        for l in lim:
            add_bullet(doc, l)
    else:
        add_para(doc, "本次逐帧判读未发现无法确认的内容。", italic=True)

    # -------- 7. Glossary & sources --------
    add_heading(doc, "七、术语与证据索引", level=1)
    gl = data.get("glossary") or []
    if gl:
        add_para(doc, "本视频涉及术语（释义见资料库「名词概念.md」）：", bold=True)
        add_para(doc, "、".join(gl))
    add_para(doc, "证据来源：", bold=True)
    for s in data.get("sources") or []:
        add_bullet(doc, s)

    return doc, missing


def render(json_path):
    with io.open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    doc, missing = build(data)
    out = os.path.join(OUT_DIR, data["video_title"] + "_逐帧深度学习报告_1秒版.docx")
    doc.save(out)
    return out, missing, sum(len(s.get("frames") or []) for s in data["timeline"])


def main():
    args = sys.argv[1:]
    files = args if args else sorted(glob.glob(os.path.join(JSON_DIR, "*.json")))
    if not files:
        print("NO JSON FOUND in", JSON_DIR)
        return
    ok = fail = 0
    for jf in files:
        try:
            out, missing, n = render(jf)
            size = os.path.getsize(out) // 1024
            flag = f"  [缺图 {len(missing)}: {missing[:3]}]" if missing else ""
            print(f"OK   {os.path.basename(out)[:52]:<54} {n:>3}图 {size:>5}KB{flag}")
            ok += 1
        except Exception as e:
            print(f"FAIL {os.path.basename(jf)[:52]:<54} {type(e).__name__}: {e}")
            traceback.print_exc()
            fail += 1
    print(f"\n合计 成功={ok} 失败={fail}")


if __name__ == "__main__":
    main()
