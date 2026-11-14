# -*- coding: utf-8 -*-
"""把 frame_json_kaihuang/ 下 6 份逐帧判读 JSON 合并渲染成一份《开荒专题》Word 报告。

图片会先用 Pillow 压到宽 1280 / JPEG q80 再嵌入，避免合并后文件体积失控。
"""
import os, json, io

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from PIL import Image

import kaihuang_meta as M

BASE = r"D:\Desktop\shandou"
JD = os.path.join(BASE, "资料库", "frame_json_kaihuang")
FRAMES_ROOT = os.path.join(BASE, "抖音_frames_dense_1s")
OUT = os.path.join(BASE, "学习汇报", "开荒专题（6 视频合并）_逐帧深度学习报告_1秒版.docx")
CACHE = os.path.join(BASE, "资料库", "_kg_imgcache")
FONT = "Microsoft YaHei"
C = WD_ALIGN_PARAGRAPH.CENTER

os.makedirs(CACHE, exist_ok=True)


def _f(run, size=10.5, bold=False, italic=False, color=None):
    run.font.name = FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = color


def H(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for r in p.runs:
        r.font.name = FONT
        r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    return p


def P(doc, text, bold=False, italic=False, size=10.5, color=None, align=None):
    p = doc.add_paragraph()
    _f(p.add_run(text), size, bold, italic, color)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    p.paragraph_format.space_after = Pt(6)
    if align:
        p.alignment = align
    return p


def B(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    _f(p.add_run(text))
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    p.paragraph_format.space_after = Pt(4)
    return p


def shrink(src, key):
    """压缩图片到缓存目录，返回缓存路径。"""
    dst = os.path.join(CACHE, key)
    if os.path.exists(dst):
        return dst
    try:
        im = Image.open(src)
        if im.mode != "RGB":
            im = im.convert("RGB")
        w, h = im.size
        if w > 1280:
            im = im.resize((1280, int(h * 1280 / w)), Image.LANCZOS)
        im.save(dst, "JPEG", quality=80, optimize=True)
        return dst
    except Exception:
        return src


def img(doc, path, caption, key, width=5.0):
    if not os.path.exists(path):
        P(doc, "[图缺失: %s]" % os.path.basename(path), italic=True,
          color=RGBColor(255, 0, 0))
        return False
    small = shrink(path, key)
    p = doc.add_paragraph()
    p.alignment = C
    p.add_run().add_picture(small, width=Inches(width))
    cap = doc.add_paragraph()
    cap.alignment = C
    _f(cap.add_run(caption), 9, color=RGBColor(80, 80, 80))
    cap.paragraph_format.space_after = Pt(10)
    return True


def table(doc, headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        _f(c.paragraphs[0].add_run(h), 9.5, bold=True)
    for r in rows:
        cells = t.add_row().cells
        for i, v in enumerate(r):
            cells[i].text = ""
            _f(cells[i].paragraphs[0].add_run(str(v)), 9)
    return t


def dur(s):
    s = int(round(float(s)))
    return "%02d:%02d" % (s // 60, s % 60)


def pick(tl, quota):
    """按段均匀配额挑帧，保证每段至少 1 帧，总数不超过 quota。"""
    segs = [s for s in tl if s.get("frames")]
    if not segs:
        return []
    n = len(segs)
    per = max(1, quota // n)
    out = []
    for s in segs:
        fr = s["frames"]
        if len(fr) <= per:
            sel = fr
        else:
            step = len(fr) / float(per)
            sel = [fr[int(i * step)] for i in range(per)]
        out.append((s, sel))
    # 若还有余额，按段帧数多的补
    used = sum(len(x[1]) for x in out)
    idx = 0
    order = sorted(range(n), key=lambda i: -len(segs[i]["frames"]))
    while used < quota and idx < len(order):
        i = order[idx]
        seg, sel = out[i]
        rest = [f for f in seg["frames"] if f not in sel]
        if rest:
            sel.append(rest[len(rest) // 2])
            sel.sort(key=lambda f: f.get("ts", ""))
            used += 1
        else:
            idx += 1
    return out


def main():
    data = []
    for item in M.ORDER:
        p = os.path.join(JD, item["file"])
        d = json.load(io.open(p, "r", encoding="utf-8"))
        data.append((item, d))

    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = FONT
    st._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    st.font.size = Pt(10.5)

    tot_dur = sum(d["duration_s"] for _, d in data)
    tot_frm = sum(d["frame_count"] for _, d in data)
    tot_shot = 0

    # ---------- 封面 ----------
    P(doc, "率土之滨 开荒专题", bold=True, size=22, align=C)
    P(doc, "6 期视频合并 · 逐帧深度学习报告", bold=True, size=14, align=C)
    P(doc, "", size=8, align=C)
    P(doc, "覆盖视频：6 期　|　总时长：%s　|　抽帧：%d 帧（1 秒/帧）"
      % (dur(tot_dur), tot_frm), size=11, align=C)
    P(doc, "报告类型：合并专题版（理论 + 选将 + 实操 + 答疑 + 正反案例）",
      size=11, align=C)
    P(doc, "生成日期：%s" % data[0][1].get("report_date", ""), size=10.5, align=C)
    P(doc, "", size=8, align=C)
    P(doc, "方法：faster-whisper 音频转写 + 每 1 秒抽 1 帧 + 逐帧画面判读 + 黑话查证",
      size=10, align=C)
    P(doc, "说明：开荒 6 期内容高度连贯，按用户要求不单独成篇，"
           "全部看完后合并为本份专题报告。", size=10, italic=True, align=C)
    doc.add_page_break()

    # ---------- 一、专题总览 ----------
    H(doc, "一、专题总览与阅读路径", level=1)
    P(doc, "开荒是率土之滨新赛季前 24 小时的核心操作，直接决定整个赛季的发育起点。"
           "本专题的 6 期视频并非平行关系，而是构成一条完整的学习链："
           "先建立配队原理，再解决选将取舍，然后看一遍完整实操，"
           "补齐高频疑问，最后用一正一反两个案例做压力测试。")
    rows = []
    for i, (item, d) in enumerate(data, 1):
        rows.append([i, item["role"], d["video_title"][:26],
                     dur(d["duration_s"]),
                     "%d 帧" % d["frame_count"]])
    table(doc, ["序", "定位", "视频（截断显示）", "时长", "抽帧"], rows)
    P(doc, "")
    P(doc, "建议阅读顺序即本报告章节顺序。若只想解决具体问题，可直接跳读：",
      bold=True)
    B(doc, "不知道用谁开荒 → 第二章「选将速查」+ 第三章「三次上线开荒法」")
    B(doc, "队伍已定、不知道怎么打 → 第三章「三次上线开荒法」")
    B(doc, "卡在某个具体问题 → 第四章「常见问题答疑」")
    B(doc, "已经翻车了 → 第七章「翻车之后怎么补救」")
    B(doc, "想避免翻车 → 第六章「史上最大开荒滑铁卢」的 7 条错误复盘")

    P(doc, "")
    H(doc, "1.1　逐帧学习方法说明", level=2)
    P(doc, "1. 以 1 秒为步长对 6 期视频均匀抽帧，共 %d 帧，覆盖 %s 全部素材，无遗漏。"
      % (tot_frm, dur(tot_dur)))
    P(doc, "2. 全部帧制成 contact sheet（每张 40 帧，5×8 排列，带秒级时间戳），"
           "逐格判读定位画面变化点。")
    P(doc, "3. 凡需写入报告的具体武将名、战法名、等级与数值，一律回看单帧原图确认，"
           "不以缩略图或音频转写为准。")
    P(doc, "4. 与 faster-whisper 音频转写逐句对齐，识别并标注转写错误"
           "（开荒实录类视频的转写错误率明显偏高，武将名多为音译近似词）。")
    P(doc, "5. 画面中出现的率土黑话与术语，已查证后补入 资料库\\名词概念.md。")
    P(doc, "6. 本报告插图为各期精选帧（按时间段均匀采样），"
           "全部原始帧作为备查证据保留在 抖音_frames_dense_1s\\开荒\\ 下。")

    # ---------- 二~七、各期正文 ----------
    for i, (item, d) in enumerate(data):
        doc.add_page_break()
        H(doc, "%s、%s" % ("二三四五六七"[i], item["ch"]), level=1)
        P(doc, "源视频：%s" % d["video_title"], size=9.5,
          color=RGBColor(90, 90, 90))
        P(doc, "时长 %s　|　抽帧 %d 帧　|　分辨率 %s　|　本章定位：%s"
          % (dur(d["duration_s"]), d["frame_count"],
             d.get("resolution", "-"), item["role"]),
          size=9.5, color=RGBColor(90, 90, 90))
        P(doc, "")
        P(doc, item["lead"])

        s = d["summary"]
        P(doc, "本期一句话结论：", bold=True)
        P(doc, s.get("one_line", ""), bold=True)

        vo = s.get("visual_only") or []
        if vo:
            H(doc, "%s.1 画面独有的关键信息" % "二三四五六七"[i], level=2)
            P(doc, "以下信息只存在于画面，音频转写无法确认：", italic=True)
            for v in vo:
                B(doc, v)

        fov = d.get("frame_only_value") or []
        if fov:
            H(doc, "%s.2 逐帧判读的增量结论" % "二三四五六七"[i], level=2)
            for v in fov:
                if isinstance(v, dict):
                    q = v.get("question") or v.get("title") or ""
                    P(doc, "问：%s" % q, bold=True)
                    for a in (v.get("answer_points") or []):
                        B(doc, a)
                    ts = v.get("timestamps") or []
                    if ts:
                        P(doc, "（对应时间：%s）" % "、".join(map(str, ts)),
                          size=9, italic=True, color=RGBColor(120, 120, 120))
                else:
                    B(doc, str(v))

        corr = s.get("corrections") or []
        if corr:
            H(doc, "%s.3 对既有音频版理解的修正" % "二三四五六七"[i], level=2)
            for c in corr:
                P(doc, str(c), color=RGBColor(192, 0, 0))

        # 时间轴插图
        H(doc, "%s.4 时间轴与画面证据" % "二三四五六七"[i], level=2)
        fdir = os.path.join(FRAMES_ROOT, d["frames_dir"])
        picked = pick(d.get("timeline") or [], item["quota"])
        for seg, frames in picked:
            H(doc, "%s　%s" % (seg.get("range", ""), seg.get("title", "")),
              level=3)
            for fr in frames:
                fp = os.path.join(fdir, fr["file"])
                key = "%02d_%s" % (i, fr["file"])
                if img(doc, fp, "%s | %s" % (fr.get("ts", ""), fr.get("desc", "")), key):
                    tot_shot += 1

        lim = d.get("limitations") or []
        if lim:
            H(doc, "%s.5 本期局限与无法确认之处" % "二三四五六七"[i], level=2)
            for l in lim:
                B(doc, str(l))

    # ---------- 八、跨期综合 ----------
    doc.add_page_break()
    H(doc, "八、%s" % M.CROSS["title"], level=1)
    P(doc, "以下结论无法从任何单独一期得出，是把 6 期逐帧判读结果放在一起"
           "交叉比对后才浮现的。", italic=True)
    for k, (t, body) in enumerate(M.CROSS["blocks"], 1):
        H(doc, "8.%d　%s" % (k, t), level=2)
        P(doc, body)

    # ---------- 九、术语与证据 ----------
    doc.add_page_break()
    H(doc, "九、术语与证据索引", level=1)
    gl = []
    for _, d in data:
        for g in (d.get("glossary") or []):
            g = g if isinstance(g, str) else str(g.get("term", g))
            if g not in gl:
                gl.append(g)
    P(doc, "本专题涉及术语共 %d 条（释义见 资料库\\名词概念.md）：" % len(gl),
      bold=True)
    P(doc, "、".join(gl))
    P(doc, "")
    P(doc, "证据来源：", bold=True)
    seen = set()
    for _, d in data:
        for s0 in (d.get("sources") or []):
            s0 = str(s0)
            if s0 not in seen:
                seen.add(s0)
                B(doc, s0)
    P(doc, "")
    P(doc, M.FOOT, italic=True, size=9.5, color=RGBColor(90, 90, 90))

    doc.save(OUT)
    return OUT, tot_shot, len(gl)


if __name__ == "__main__":
    out, n, g = main()
    size = os.path.getsize(out) // 1024
    print("OK  %s" % os.path.basename(out))
    print("插图 %d 张  术语 %d 条  体积 %d KB" % (n, g, size))
