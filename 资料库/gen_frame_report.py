#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a frame-by-frame deep-learning report for a single video,
plus a comparison with the existing audio-only report.
"""
import os
import sys
import json
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn


def set_cell_border(cell, **kwargs):
    """Set cell border for comparison table."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        if edge in kwargs:
            edge_elm = tcPr.find(qn(f'w:{edge}'))
            if edge_elm is None:
                edge_elm = docx.oxml.OxmlElement(f'w:{edge}')
                tcPr.append(edge_elm)
            edge_elm.set(qn('w:val'), kwargs[edge].get('val', 'single'))
            edge_elm.set(qn('w:sz'), str(kwargs[edge].get('sz', 4)))
            edge_elm.set(qn('w:space'), '0')
            edge_elm.set(qn('w:color'), kwargs[edge].get('color', '000000'))


def add_heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        run.font.name = 'Microsoft YaHei'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    return p


def add_para(doc, text, bold=False, italic=False, size=10.5, color=None, align=None):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = 'Microsoft YaHei'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = color
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    p.paragraph_format.space_after = Pt(6)
    if align:
        p.alignment = align
    return p


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style='List Bullet' if level == 0 else 'List Bullet 2')
    run = p.add_run(text)
    run.font.name = 'Microsoft YaHei'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    run.font.size = Pt(10.5)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    p.paragraph_format.space_after = Pt(4)
    return p


def embed_image(doc, path, caption, width=5.5):
    if not os.path.exists(path):
        add_para(doc, f"[图缺失: {caption}]", italic=True, color=RGBColor(255, 0, 0))
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(path, width=Inches(width))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    crun = cap.add_run(caption)
    crun.font.name = 'Microsoft YaHei'
    crun._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    crun.font.size = Pt(9)
    crun.font.color.rgb = RGBColor(80, 80, 80)
    cap.paragraph_format.space_after = Pt(10)


def build_report(out_docx):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Microsoft YaHei'
    style._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    style.font.size = Pt(10.5)

    video_name = "配将焚决来了 全体系队伍搭建思路最后一期，真焚决—宏观配将法，来了! 跟合集内容全部融会贯通，你也能成配将大手子!"
    dense_dir = r"D:/Desktop/shandou/抖音_frames_dense/" + video_name

    # ---------- Cover ----------
    add_para(doc, "率土之滨抖音视频 逐帧深度学习报告", bold=True, size=18, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_para(doc, f"视频标题：{video_name}", bold=True, size=14, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_para(doc, "报告类型：逐帧版 + 与既有音频版报告对比", size=11, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_para(doc, "生成日期：2026-08-07", size=11, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_para(doc, "方法：音频转写 faster-whisper + 每 2 秒抽取 1 帧并人工判读画面", size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_page_break()

    # ---------- Executive summary ----------
    add_heading(doc, "一、逐帧学习的核心结论", level=1)
    add_para(doc, "本次对同一视频进行了更密集的逐帧分析（104 帧，2 秒/帧），相比既有音频版报告（8 帧，约 20 秒/帧），画面补充了大量音频转写无法确认甚至误判的信息。")
    add_heading(doc, "1.1 音频转写无法确认、但画面可核实的关键信息", level=2)
    bullets = [
        "作者最终选择的队伍：画面 01:42 明确显示为「神赏出木鹿斩龙」，而非音频转写的「身上出墓路战龙」。",
        "缺失卡/武将：画面 00:58 显示「没有合纵」；01:02 显示刘备 + S 级战法「百战无怯」且标注「根本组不出来」。",
        "螃蟹队的资源冲突：01:04–01:12 连续画面显示，出螃蟹需占用曹操、攻其不备、反计之策，并与法刀抢反计、与魏智抢荀彧。",
        "法刀体系缺口：01:14 画面明确「没有吕蒙」。",
        "作者其余三队全顶配：02:00–02:06 连续展示 3–4 个满战法队伍界面。",
        "大张鲁队技能：02:18 画面显示技能为「避锐治气」（音频转写为「闭锐质气」）。",
        "克制链实战佐证：02:24–02:38 出现多张战报界面，包含「胜」「平」结果，说明克制关系有战报支撑。",
        "补链方案：02:44–02:48 显示「斩龙」队伍，并配文「克制链就非常完整了」。",
        "反面案例：02:56 展示「降配的螃蟹」+「白白的核弹」两队，说明硬凑两队半成品的危险。"
    ]
    for b in bullets:
        add_bullet(doc, b)

    add_heading(doc, "1.2 对既有报告的重要修正", level=2)
    add_para(doc, "既有音频版报告在「not_concluded」中认为「视频未展示战报」。逐帧判读后确认：视频 02:24–02:38 及 02:50 附近展示了大量个人战报（含胜/平/败），用于支撑克制链论述。因此「无战报」的结论需要修正为「有战报但无具体胜率/样本量数据」。", color=RGBColor(192, 0, 0))
    add_para(doc, "另有若干武将/战法名称因音频转写失真而在既有报告中标记为「查不到」；逐帧画面可将其校正为较准确的写法（见第四部分对照表）。", color=RGBColor(192, 0, 0))

    # ---------- Methodology ----------
    doc.add_page_break()
    add_heading(doc, "二、逐帧分析方法", level=1)
    add_para(doc, "1. 以 2 秒为步长对 207 秒视频均匀抽帧，共 104 帧，覆盖全部 3 分 27 秒内容。")
    add_para(doc, "2. 将 104 帧制作成 13 张 contact sheet（每张 8 帧），人工判读画面中的 UI、武将卡、战法图标、战报、字幕与文字提示。")
    add_para(doc, "3. 将画面信息与 faster-whisper 音频转写逐句对齐，识别音频转写错误并补充视觉证据。")
    add_para(doc, "4. 选取 19 张最具代表性的单帧嵌入本报告，其余帧作为备查证据保留在 D:\\Desktop\\shandou\\抖音_frames_dense\\ 下。")

    # ---------- Timeline ----------
    doc.add_page_break()
    add_heading(doc, "三、逐帧时间轴与画面解读", level=1)

    sections = [
        ("00:00–00:30", "开篇：从微观操作到宏观配将法", [
            ("00:00", "frame_0000_00-00.jpg", "黑白色调武将动画开场，视频基调为策略/教学。"),
            ("00:04", "frame_0002_00-04.jpg", "登录界面出现金色大字「微观操作」，旁白将「按体系配将」定位为战术层面的微观操作。"),
            ("00:08", "frame_0004_00-08.jpg", "金色标题「宏观配将法」出现，点明本期主题：根据账号情况决定出几队、出哪几队。"),
            ("00:14", "frame_0007_00-14.jpg", "画面叠加作者抖音合集卡片：「全率土最全入门攻略合集！」，53.9 万播放、111 收藏、更新至第 11 集，说明本视频是系列收官。"),
            ("00:20", "frame_0010_00-20.jpg", "武将卡池界面，暗示本视频将以具体账号为例。"),
            ("00:24", "frame_0012_00-24.jpg", "大字「如何根据账号情况」；00:26「来搭建队伍」，引出核心问题。"),
            ("00:30", "frame_0015_00-30.jpg", "标题「一、质量大于数量」，正式进入原则一。")
        ]),
        ("00:30–01:00", "原则一：赛季节奏与数量取舍", [
            ("00:32", "frame_0016_00-32.jpg", "赛季奖励界面，字幕「每赛季 45 天左右」，解释赛季节奏快的依据。"),
            ("00:36", "frame_0018_00-36.jpg", "部队阵容界面显示多支队伍，字幕「大多在前三队刚出完的样子」。"),
            ("00:42", "frame_0021_00-42.jpg", "铁匠铺画面，字幕「完全不需要强行追求出 5 队」。"),
            ("00:46", "frame_0023_00-46.jpg", "大字「前三队」配绿色对勾，强调「一定是前两三队的强度」。"),
            ("00:54", "frame_0027_00-54.jpg", "关键画面：「适配百战神赏体系的武将」列表，展示多个武将头像，为后续缺卡分析做铺垫。"),
            ("00:58", "frame_0029_00-58.jpg", "武将详情界面，字幕「没有合纵」，明确缺失的关键卡/战法之一。")
        ]),
        ("01:00–01:30", "作者账号示范：缺卡与冲突", [
            ("01:02", "frame_0030_01-00.jpg", "刘备卡与 S 战法「百战无怯」，字幕「组刘备百战体系根本组不出来」。"),
            ("01:04", "frame_0032_01-04.jpg", "曹操详情界面，字幕「只能出螃蟹」；01:06 显示「还要占攻其」。"),
            ("01:08", "frame_0034_01-08.jpg", "曹操携带「反计之策」「攻其不备」，字幕「还跟法刀抢反计」。"),
            ("01:10", "frame_0035_01-10.jpg", "荀彧详情界面，字幕「大营唯一合适的荀彧」；01:12 显示「还跟魏智起冲突」。"),
            ("01:14", "frame_0037_01-14.jpg", "吕蒙详情界面，字幕「没有吕蒙」，法刀体系因此不完整。"),
            ("01:18", "frame_0039_01-18.jpg", "部队阵容界面，讨论卫瓘/月英替代方案。"),
            ("01:22", "frame_0041_01-22.jpg", "字幕「强度也不容乐观」，说明替代方案同样不给力。"),
            ("01:28", "frame_0044_01-28.jpg", "字幕「永远面临两体系二选一的境地」。")
        ]),
        ("01:30–02:00", "决策：两队弱不如一队强", [
            ("01:32", "frame_0046_01-32.jpg", "招募/抽卡界面，配狗头表情包，字幕「囊中羞涩」，说明资源不足。"),
            ("01:36", "frame_0048_01-36.jpg", "大字「怎么出？」；01:38 给出答案「一定不如出一队强的」。"),
            ("01:42", "frame_0051_01-42.jpg", "核心画面：作者选择的队伍界面，字幕「神赏出木鹿斩龙」，展示三名武将及 9 个战法位。"),
            ("01:46", "frame_0053_01-46.jpg", "战报界面「勇冠三军」显示一场败绩，字幕称此队为「平民最有底气的法刀」。"),
            ("01:50", "frame_0055_01-50.jpg", "木鹿兵种详情「象兵特性」，解释为何选择木鹿。"),
            ("01:52", "frame_0056_01-52.jpg", "三人组合画面，字幕「还能压制一手司马懿汉荀彧」。"),
            ("01:58", "frame_0059_01-58.jpg", "部队阵容界面，字幕「让我其余三队」进入下一话题。")
        ]),
        ("02:00–02:30", "砍掉百战后的连锁收益", [
            ("02:00", "frame_0060_02-00.jpg", "第一支剩余队伍满战法界面，字幕「也全都能给足顶配」。"),
            ("02:02", "frame_0061_02-02.jpg", "第二支剩余队伍满战法界面，字幕「不会有任何强度损耗」。"),
            ("02:04", "frame_0062_02-04.jpg", "第三支剩余队伍界面，字幕「赛季也差不多结束了」。"),
            ("02:08", "frame_0064_02-08.jpg", "字幕「质量大于数量的效果」。"),
            ("02:18", "frame_0069_02-18.jpg", "大张鲁队伍界面，字幕「我的大张鲁给的是避锐治气非常克制菜刀队」。"),
            ("02:22", "frame_0071_02-22.jpg", "数据统计/战报界面，字幕「满红鸟刀来也讨不到好处」。"),
            ("02:24", "frame_0072_02-24.jpg", "战磐程昱魏智队伍界面。"),
            ("02:26", "frame_0073_02-26.jpg", "战报「胜」，字幕「打大菜刀斩龙更是轻轻松松」。")
        ]),
        ("02:30–03:00", "原则二：克制链与缺口补齐", [
            ("02:28", "frame_0074_02-28.jpg", "战报「平」，字幕「王异法刀也能接一接」。"),
            ("02:30", "frame_0075_02-30.jpg", "多张战报列表，字幕「砍各类半脆皮队伍也非常舒服」。"),
            ("02:36", "frame_0078_02-36.jpg", "战报列表，字幕「马超不一定能稳吃对吧」。"),
            ("02:40", "frame_0080_02-40.jpg", "马超队界面，字幕「外加没有破规避手段呀」。"),
            ("02:44", "frame_0082_02-44.jpg", "高配垒实队界面（庞统、刘备、司马懿），字幕「面对高配垒实也算不上好打」。"),
            ("02:46", "frame_0083_02-46.jpg", "作者掏出「斩龙」队伍，狗头表情包配文「我掏一队斩龙」。"),
            ("02:48", "frame_0084_02-48.jpg", "大字「克制链就非常完整了」。"),
            ("02:56", "frame_0088_02-56.jpg", "反面队伍：「降配的螃蟹」+「白白的核弹」，字幕「这俩上去可能被高配雷识一脚都给踹死了」。")
        ]),
        ("03:00–03:27", "收尾：两原则合一", [
            ("03:04", "frame_0092_03-04.jpg", "字幕「从两支弱队」。"),
            ("03:06", "frame_0093_03-06.jpg", "字幕「变成了一支强队」。"),
            ("03:10", "frame_0095_03-10.jpg", "字幕「所以我舍弃百战体系 走斩龙这个思路」。"),
            ("03:14", "frame_0097_03-14.jpg", "关羽形象特写，字幕「所以遵循质量大于数量原则疯狂堆料」。"),
            ("03:20", "frame_0100_03-20.jpg", "海边独行者画面，字幕「不断完善你的克制链」。"),
            ("03:22", "frame_0101_03-22.jpg", "武将持矛画面，字幕「才能去跟老六们斗智斗勇」。视频结束。")
        ])
    ]

    for sec_title, sec_subtitle, frames in sections:
        add_heading(doc, sec_title + " " + sec_subtitle, level=2)
        for ts, fn, caption in frames:
            path = os.path.join(dense_dir, fn)
            embed_image(doc, path, f"{ts} | {caption}", width=5.2)

    # ---------- Comparison ----------
    doc.add_page_break()
    add_heading(doc, "四、逐帧版 vs 既有音频版报告对照", level=1)
    add_para(doc, "下表列出两项报告在关键信息点上的差异。既有报告基于 8 帧稀疏画面 + 音频转写；逐帧版基于 104 帧密集画面 + 音频转写 + 人工判读。")

    table = doc.add_table(rows=1, cols=4)
    table.style = 'Light Grid Accent 1'
    hdr = table.rows[0].cells
    hdr[0].text = "信息点"
    hdr[1].text = "既有音频版报告"
    hdr[2].text = "逐帧版报告"
    hdr[3].text = "差异说明"
    for cell in hdr:
        for run in cell.paragraphs[0].runs:
            run.font.bold = True
            run.font.name = 'Microsoft YaHei'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')

    comparisons = [
        ("作者最终队伍", "仅描述为「把资源集中到一队」", "明确为「神赏出木鹿斩龙」，并展示 3 名武将及战法位", "画面给出具体队伍名称与构成"),
        ("百战体系缺卡", "「缺少多张关键卡（转写不清）」", "缺「合纵」；刘备+百战无怯无法成型", "画面显示具体缺失项"),
        ("螃蟹队冲突", "「会跟法刀抢反击、抢大营荀彧」", "占用曹操、攻其不备、反计之策；与法刀抢反计、与魏智抢荀彧", "画面补充具体战法与武将冲突"),
        ("法刀体系缺口", "未明确", "「没有吕蒙」", "画面直接显示"),
        ("木鹿价值", "未提及", "木鹿带象兵，能压制司马懿汉荀彧", "画面展示象兵特性与三人组合"),
        ("其余三队是否顶配", "文字结论", "连续展示 3–4 个满战法队伍界面", "视觉实证"),
        ("克制链战报", "「视频未展示战报」", "02:24–02:38 展示多张个人战报（胜/平）", "重要修正：视频确有战报"),
        ("大张鲁技能", "「闭锐质气」（转写）", "「避锐治气」", "画面文字校正"),
        ("补链方案", "「拖一队斩龙思路的队伍」", "明确掏出「斩龙」队伍，克制链完整", "画面展示队伍与结论文字"),
        ("反面案例", "未详细展开", "展示「降配螃蟹」+「白白核弹」两队，说明被高配雷识踹死", "画面补充"),
        ("转写失真示例", "标记为「查不到」", "「寻域→荀彧」「履蒙→吕蒙」「司马一汉寻域→司马懿汉荀彧」", "画面可校正音近字"),
    ]
    for info, old, new, diff in comparisons:
        row = table.add_row().cells
        row[0].text = info
        row[1].text = old
        row[2].text = new
        row[3].text = diff
        for cell in row:
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.name = 'Microsoft YaHei'
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
                    run.font.size = Pt(9)

    # ---------- What frame-by-frame added ----------
    doc.add_page_break()
    add_heading(doc, "五、逐帧版独有的新增价值", level=1)
    add_para(doc, "以下结论在仅听音频时难以得出，必须通过画面判读：")
    adds = [
        "具体队伍可视化：作者选择「神赏出木鹿斩龙」作为替代百战的方案，画面显示该队三名武将及全部战法图标。",
        "资源冲突可视化：曹操、荀彧、吕蒙等核心卡在不同体系间的争夺，通过角色详情页与部队阵容页连续展示。",
        "战报实证：克制链论述并非空口无凭，视频中展示了多张个人战报界面（胜/平），但样本量和对手红度未量化。",
        "兵种与特性：木鹿的「象兵特性」在画面中有文字说明，解释其被选用的部分原因。",
        "反面教材可视化：「降配螃蟹」+「白白核弹」两队的界面被明确展示，用于论证「两队弱不如一队强」。",
        "系列定位：00:14 的合集卡片证明本视频是「全率土最全入门攻略合集」第 11 集（收官），与音频中「11 期长视频」呼应。"
    ]
    for a in adds:
        add_bullet(doc, a)

    # ---------- Limitations ----------
    add_heading(doc, "六、逐帧版仍无法确认的内容", level=2)
    limits = [
        "战法/武将的具体数值、概率、触发机制：画面仅展示图标与名称，未展示具体数值。",
        "战报样本量与胜率：虽有战报截图，但无法统计总体胜率、对手练度、赛季阶段。",
        "部分字幕为网络梗或谐音（如 02:38「催奶」），其真实含义需结合主播语境推断，无法 100% 确认。",
        "「斩龙」「螃蟹」「核弹」等属于玩家黑话，画面未给出官方定义或固定配将表。",
        "视频中 104 帧为 2 秒/帧的均匀采样，未做到真正的 30fps 逐帧；极短的文字提示可能被跳过。"
    ]
    for l in limits:
        add_bullet(doc, l)

    # ---------- Sources ----------
    add_heading(doc, "七、证据来源索引", level=1)
    add_para(doc, "视频文件：D:\\Desktop\\shandou\\抖音\\配将焚决来了 全体系队伍搭建思路最后一期，真焚决—宏观配将法，来了! 跟合集内容全部融会贯通，你也能成配将大手子!.mp4")
    add_para(doc, "音频转写：D:\\Desktop\\shandou\\抖音_transcripts\\配将焚决来了 全体系队伍搭建思路最后一期，真焚决—宏观配将法，来了! 跟合集内容全部融会贯通，你也能成配将大手子!.json")
    add_para(doc, "逐帧画面：D:\\Desktop\\shandou\\抖音_frames_dense\\配将焚决来了 全体系队伍搭建思路最后一期，真焚决—宏观配将法，来了! 跟合集内容全部融会贯通，你也能成配将大手子!\\（共 104 帧）")
    add_para(doc, "既有报告：D:\\Desktop\\shandou\\资料库\\reports_json\\配将焚决来了 全体系队伍搭建思路最后一期，真焚决—宏观配将法，来了! 跟合集内容全部融会贯通，你也能成配将大手子!.json")

    doc.save(out_docx)
    print("SAVED", out_docx)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else r"D:/Desktop/shandou/学习汇报/配将焚决来了 全体系队伍搭建思路最后一期，真焚决—宏观配将法，来了! 跟合集内容全部融会贯通，你也能成配将大手子!_逐帧深度学习报告.docx"
    build_report(out)
