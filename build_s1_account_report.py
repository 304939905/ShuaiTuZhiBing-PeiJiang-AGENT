from __future__ import annotations

from pathlib import Path
from typing import Iterable

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


OUT = Path(r"D:\Desktop\新建文件夹 (2)\S1赛季末_账号配将与施政建议_二次修订版_2026-08-25.docx")

NAVY = "17324D"
BLUE = "2E74B5"
DARK_BLUE = "1F4D78"
PALE_BLUE = "E8EEF5"
PALE_GRAY = "F2F4F7"
PALE_GOLD = "FFF4D6"
GOLD = "9A6B00"
RED = "9B1C1C"
GREEN = "246B45"
MUTED = "5B6573"
WHITE = "FFFFFF"
BLACK = "202124"


def set_run_font(run, size=None, bold=None, color=None, italic=None):
    run.font.name = "Calibri"
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), "Calibri")
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), "Calibri")
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = RGBColor.from_string(color)
    if italic is not None:
        run.italic = italic


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=80, start=120, bottom=80, end=120):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for m, v in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{m}"))
        if node is None:
            node = OxmlElement(f"w:{m}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(v))
        node.set(qn("w:type"), "dxa")


def set_cell_width(cell, width_dxa):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(width_dxa))
    tc_w.set(qn("w:type"), "dxa")


def set_table_geometry(table, widths: Iterable[int], indent=120):
    widths = list(widths)
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(sum(widths)))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_ind = tbl_pr.find(qn("w:tblInd"))
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), str(indent))
    tbl_ind.set(qn("w:type"), "dxa")
    layout = tbl_pr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tbl_pr.append(layout)
    layout.set(qn("w:type"), "fixed")
    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for w in widths:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(w))
        grid.append(col)
    for row in table.rows:
        for i, cell in enumerate(row.cells):
            set_cell_width(cell, widths[min(i, len(widths) - 1)])
            set_cell_margins(cell)


def repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_repeat_table_header_and_no_split(table):
    repeat_header(table.rows[0])
    for row in table.rows:
        tr_pr = row._tr.get_or_add_trPr()
        cant_split = OxmlElement("w:cantSplit")
        tr_pr.append(cant_split)


def cell_text(cell, text, bold=False, color=BLACK, size=9.2, align=None):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.08
    if align is not None:
        p.alignment = align
    r = p.add_run(str(text))
    set_run_font(r, size=size, bold=bold, color=color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_table(doc, headers, rows, widths, header_fill=PALE_BLUE, font_size=9.1):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False
    table.style = "Table Grid"
    for i, h in enumerate(headers):
        set_cell_shading(table.rows[0].cells[i], header_fill)
        cell_text(table.rows[0].cells[i], h, bold=True, color=NAVY, size=9.2)
        table.rows[0].cells[i].paragraphs[0].paragraph_format.keep_with_next = True
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cell_text(cells[i], value, size=font_size)
    set_table_geometry(table, widths)
    set_repeat_table_header_and_no_split(table)
    after = doc.add_paragraph()
    after.paragraph_format.space_after = Pt(2)
    return table


def add_para(doc, text="", *, size=11, bold=False, color=BLACK, italic=False,
             align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=6, keep=False):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.25
    p.paragraph_format.keep_together = keep
    r = p.add_run(text)
    set_run_font(r, size=size, bold=bold, color=color, italic=italic)
    return p


def add_lead(doc, label, text, color=NAVY):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.25
    a = p.add_run(label + "：")
    set_run_font(a, size=11, bold=True, color=color)
    b = p.add_run(text)
    set_run_font(b, size=11, color=BLACK)
    return p


def add_heading(doc, text, level=1):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    set_run_font(r)
    return p


def add_callout(doc, label, text, fill=PALE_GOLD, label_color=GOLD):
    table = doc.add_table(rows=1, cols=1)
    table.style = "Table Grid"
    table.autofit = False
    set_table_geometry(table, [9360])
    tr_pr = table.rows[0]._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement("w:cantSplit"))
    cell = table.cell(0, 0)
    set_cell_shading(cell, fill)
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.18
    a = p.add_run(label + "  ")
    set_run_font(a, size=10.5, bold=True, color=label_color)
    b = p.add_run(text)
    set_run_font(b, size=10.5, color=BLACK)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_hyperlink(paragraph, text, url):
    part = paragraph.part
    rid = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), rid)
    run = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), BLUE)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    rfonts = OxmlElement("w:rFonts")
    rfonts.set(qn("w:ascii"), "Calibri")
    rfonts.set(qn("w:hAnsi"), "Calibri")
    rfonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    rpr.extend([rfonts, color, underline])
    text_el = OxmlElement("w:t")
    text_el.text = text
    run.extend([rpr, text_el])
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def configure_styles(doc):
    doc.settings.odd_and_even_pages_header_footer = False
    sec = doc.sections[0]
    sec.different_first_page_header_footer = False
    sec.top_margin = Inches(1)
    sec.bottom_margin = Inches(1)
    sec.left_margin = Inches(1)
    sec.right_margin = Inches(1)
    sec.header_distance = Inches(0.492)
    sec.footer_distance = Inches(0.492)
    sec.page_width = Inches(8.5)
    sec.page_height = Inches(11)

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.25

    tokens = {
        "Heading 1": (16, BLUE, 18, 10),
        "Heading 2": (13, BLUE, 14, 7),
        "Heading 3": (12, DARK_BLUE, 10, 5),
    }
    for name, (size, color, before, after) in tokens.items():
        s = doc.styles[name]
        s.font.name = "Calibri"
        s._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
        s._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
        s._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        s.font.size = Pt(size)
        s.font.bold = True
        s.font.color.rgb = RGBColor.from_string(color)
        s.paragraph_format.space_before = Pt(before)
        s.paragraph_format.space_after = Pt(after)
        s.paragraph_format.keep_with_next = True


def add_header_footer(doc):
    # Named override: omit running furniture because the local Word PDF exporter
    # renders identical odd/even header parts inconsistently. The report body and
    # source appendix carry all document-identification information.
    return


def cover(doc):
    add_para(doc, "率土之滨 · 账号定制报告", size=10.5, bold=True, color=GOLD,
             align=WD_ALIGN_PARAGRAPH.CENTER, before=90, after=20)
    add_para(doc, "S1 赛季末\n配将、战法与施政建议", size=27, bold=True, color=NAVY,
             align=WD_ALIGN_PARAGRAPH.CENTER, before=0, after=14, keep=True)
    add_para(doc, "三支主力 + 甘宁低配碰瓷 · 战法按初始数量核算",
             size=13, color=DARK_BLUE, align=WD_ALIGN_PARAGRAPH.CENTER, after=42)
    add_table(
        doc,
        ["核对项", "本报告采用的账号条件"],
        [
            ("赛季", "S1 赛季末期"),
            ("主力目标", "优先做 3 支可同时出战的队伍；其余只给轮换与功能建议"),
            ("五星觉醒", "现有 5 名已觉醒；新增仅 1 个五星觉醒名额"),
            ("四星觉醒", "按用户说明，所需四星均可觉醒"),
            ("统帅值", "主城统帅值按 10 计算，不构成配队限制"),
            ("战法数量", "按截图分数的分母（初始拥有数量）核算；允许卸下并重组全部队伍"),
            ("等级", "不作为限制条件"),
            ("账号证据", "3 张武将截图、4 张战法截图、1 张施政截图"),
        ],
        [1900, 7460],
        header_fill=PALE_GRAY,
        font_size=10,
    )
    add_para(doc, "结论有效期：以 2026-08-25 的截图和当前 S1 状态为准。游戏后续平衡调整及未展示卡牌，均可能改变最优解。",
             size=9.5, color=MUTED, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, before=22, after=0)
    doc.add_page_break()


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    configure_styles(doc)
    add_header_footer(doc)
    cover(doc)

    add_heading(doc, "先给结论", 1)
    add_callout(doc, "最终建议", "新增五星觉醒仍给周瑜。结合你反馈的战场环境，前三队改为魏法控、吴法控、汉弓抗爆头；太史慈 + 马云禄的双追击改为轮换队。第四队组四星甘宁低配碰瓷。你没有先驱突击，截图中的 D 级战法是“先驱”，两者不是同一战法，因此本版不再使用先驱突击，也放弃竹林七贤队。四队同时装配不超出截图分母所示数量。")
    add_lead(doc, "第一主力", "荀彧 + 曹植 + 魏关羽。三人均已觉醒，魏阵营加成完整，是账号当前最稳的第一队框架。")
    add_lead(doc, "第二主力", "周瑜 + 小乔 + 四星周泰。新增觉醒给周瑜，小乔负责控制联动和回复，周泰负责前锋承伤。")
    add_lead(doc, "第三主力", "灵帝 + 四星李儒 + 何太后。不是因为太史慈、马云禄弱，而是你当前经常遇到高速爆头队；何太后的母仪浮梦能给全队首次受击规避，并压低敌军前四回合伤害，更适合当前环境。")
    add_lead(doc, "甘宁碰瓷", "四星朱儁 + 四星甘宁 + 四星凌统，三将齐全。甘宁改带连战 + 温酒斩将，凌统改带百战精兵 + 破甲；可以做低配换兵工具队，但不再称为完整的先驱突击版。")
    add_lead(doc, "拆解底线", "不拆任何截图中仅有一张的五星。张春华拆浑水摸鱼、周瑜拆不攻、何太后拆空城都只在获得第二张后再做。")
    add_lead(doc, "施政", "竹林七贤队已经放弃，山涛与向秀可稳定留在施政。灵帝若作为第三主力出战就不能同时施政；金币方案以周姬、向秀为常驻核心，停用汉弓时再把灵帝转回施政。")
    add_lead(doc, "战场适配", "不和成熟高速队盲目拼全速。用战必断金防普攻/追击爆发，用反计之策防主动爆发，用大营规避与何太后处理首次高伤；速度只用于队内调序和同类武将内战。")

    doc.add_page_break()
    add_heading(doc, "1. 账号盘点与信息边界", 1)
    add_heading(doc, "1.1 五星与觉醒", 2)
    five_rows = [
        ("已觉醒（卡面有“极”）", "魏关羽、魏曹植、吴太史慈、魏荀彧、吴小乔", "可直接使用两个学习战法位"),
        ("未觉醒（战斗截图）", "吴周瑜、魏张春华、蜀关银屏、吴甘宁、吴孙策、蜀马云禄、魏卞夫人、汉孙坚、汉何太后、蜀诸葛亮", "当前只有一个学习战法位"),
        ("施政页另见", "汉灵帝、吴周姬", "未从施政截图确认觉醒；本报告不把二者计为已觉醒"),
    ]
    add_table(doc, ["状态", "武将", "配将含义"], five_rows, [2100, 4700, 2560])
    add_callout(doc, "识别规则", "卡面右上角“极”表示已觉醒并开启第三战法格；红星是进阶红度，不等于觉醒。截图中可明确确认 5 名五星带“极”。", fill=PALE_BLUE, label_color=DARK_BLUE)

    add_heading(doc, "1.2 四星资源", 2)
    add_para(doc, "截图可见的四星核心包括汉刘备、吴周泰、吴凌统、汉朱儁、四星甘宁、山涛、向秀、阮咸、王戎等。按你的说明，四星觉醒材料不是限制，因此本报告按四队所需四星均可开启第三战法格处理。")
    add_para(doc, "四星里必须保留战斗本体的优先级：刘备、周泰、朱儁、甘宁、凌统、李儒；山涛和向秀保留作施政。阮咸、王戎不进入本版战斗队。只有多余副本才进入战法研究。", bold=True, color=NAVY)

    add_heading(doc, "1.3 战法数量口径与四队总账", 2)
    add_para(doc, "按你最新说明，战法数量直接取截图分数的分母：例如落雷 0/2 按 2 份、连战 0/2 按 2 份。分子只代表当前闲置数量，不限制本报告。截图中的“先驱 2/3”是 D 级战法先驱，不是先驱突击；本版对四队的配置不使用先驱。重新组队前先卸下旧队全部学习战法，再按下表重装。")
    doc.add_page_break()
    add_table(
        doc,
        ["高价值库存", "本报告分配", "作用"],
        [
            ("唯一核心", "大赏 1/1、反计 1/1、战必 1/1、共饮 1/1、焰焚 1/1、激水 1/1、奇术 1/1、温酒 1/1、危崖 1/1", "全部各分配 1 份，不超量"),
            ("两份用满", "连战 2/2、青囊秘要 2/2、规避 2/2", "四队合计全部用满"),
            ("仍有余量", "落雷 1/2、援军秘策 1/2、长兵 1/2、反击之策 1/2、百战 1/2、破甲 1/2、成竹 1/2", "左侧为本报告使用数/初始数量"),
            ("明确不使用", "先驱 0/3", "截图为 D 级“先驱”，不能按“先驱突击”使用"),
        ],
        [2600, 2600, 4160],
    )

    add_heading(doc, "1.4 为什么部分五星不进三主力", 2)
    add_para(doc, "结论不是“五星越多越该上”。三队同时出战时，限制你的是觉醒格、顶级战法和队内联动，而不是五星卡数量。下面逐张说明未进当前三主力的原因与启用条件。")
    add_table(
        doc,
        ["五星", "当前判断", "什么时候上"],
        [
            ("太史慈、马云禄", "不弱；原第三队输出很直接，但缺少稳定的全队前三回合保护，当前高速爆头环境下容错偏低", "对手偏慢或先由前两队探明阵容后，作为补刀/追击轮换队启用"),
            ("张春华", "控制价值高，但未觉醒时只有一个学习格，自带准备控制也需要保护；现有反计和奇术优先服务周瑜、小乔队", "以后有第二个五星觉醒名额，或获得浑水摸鱼、始计等更完整控制链时"),
            ("关银屏", "不是弱将；当前缺适合她的高质量物理主动战法组合，未觉醒时输出上限受限", "补到强力物理主动战法并能给她觉醒后，可替换第三队做物理大营"),
            ("五星甘宁", "自带偏物理主动体系，但当前高质量物理主动战法不足；四星甘宁用现有温酒、连战做碰瓷更省资源", "获得更完整的物理主动输出和增伤战法，再考虑五星甘宁主力化"),
            ("孙策", "单卡能打，但目前缺少让他稳定连段的追击、增伤和保护组合，且未觉醒", "战法池补强后与吴系物理核重组；当前不抢太史慈和甘宁的战法"),
            ("卞夫人", "功能型辅助，但当前队伍里曹植、小乔、何太后的功能更直接，且她未觉醒", "需要补控制或单独组魏系副队时再用"),
            ("汉孙坚", "可当前锋，但魏关羽、周泰、何太后已经覆盖三队前排与保护，继续上会摊薄防御战法", "需要第四支满兵战斗队，或前锋被占用时作为替换"),
            ("蜀诸葛亮", "谋略与辅助能力不差，但当前缺少完整蜀智伙伴和对应战法链，未觉醒时也只有一个学习格", "凑齐蜀智框架或获得更多策略核心战法后"),
            ("周姬", "本版优先保留施政税收；转战斗会失去金币收益，且现有吴法队位置已经满", "金币压力解除、且另有完整吴系战斗体系时"),
        ],
        [1700, 4300, 3360],
        font_size=8.6,
    )

    add_heading(doc, "2. 三主力 + 一支功能队总表", 1)
    add_table(
        doc,
        ["优先级", "队伍", "站位", "学习战法（不含自带）", "定位"],
        [
            ("1", "魏法控·抗爆头", "大营荀彧\n中军曹植\n前锋魏关羽", "荀彧：激水之疾 + 规避\n曹植：大赏三军 + 援军秘策\n关羽：战必断金 + 青囊秘要", "战必压普攻/追击；大营规避挡首次高伤"),
            ("2", "吴法控·抗爆头", "大营周瑜\n中军小乔\n前锋四星周泰", "周瑜：焰焚箕轸 + 规避\n小乔：反计之策 + 奇术折冲\n周泰：青囊秘要 + 成竹在胸", "反计压主动；大营规避避免早早被点掉"),
            ("3", "汉弓抗爆头", "大营灵帝\n中军四星李儒\n前锋何太后", "灵帝：连战（未确认觉醒）\n李儒：落雷 + 危崖困军\n何太后：共饮避世（未确认觉醒）", "母仪浮梦给全队首次受击规避，并削前四回合伤害"),
            ("4", "甘宁低配碰瓷", "大营四星朱儁\n中军四星甘宁\n前锋四星凌统", "朱儁：长兵方阵 + 反击之策\n甘宁：连战 + 温酒斩将\n凌统：百战精兵 + 破甲", "三将齐全；没有先驱突击，爆发上限低于标准版"),
        ],
        [850, 1250, 1750, 3150, 2360],
        font_size=8.6,
    )
    add_callout(doc, "数量核验", "上表已经按战法初始数量核算：连战、青囊秘要、规避各用 2 份；其余已列核心各用 1 份。四队可以同时装配，不需要互相借战法。D 级“先驱”没有进入任何队伍。", fill=PALE_GOLD, label_color=RED)

    doc.add_page_break()
    add_heading(doc, "2.1 高速与爆头环境怎么处理", 2)
    add_table(
        doc,
        ["对面主要爆发来源", "本账号应对", "要点"],
        [
            ("普攻 / 追击", "第一队战必断金", "前三回合直接压普攻链；不要靠单纯堆速度硬追成熟菜刀"),
            ("主动战法", "第二队反计之策", "反计优先保周瑜准备输出；大营再带规避防漏网高伤"),
            ("指挥伤害 / 首次高伤", "第三队何太后 + 共饮", "母仪浮梦提供首次受击规避；同级指挥先后可能受速度影响，需看战报准备回合顺序"),
            ("不确定类型", "前三队分工试探", "先用相克保护队碰一次，再根据战报判断是普攻、主动还是指挥爆头"),
        ],
        [2200, 2600, 4560],
        font_size=9.0,
    )
    add_lead(doc, "速度原则", "荀彧、周瑜、太史慈这类输出可先以 5 至 10 点速度作为经验性微调起点，用于同类武将内战和队内调序；最终阈值必须看你自己的战报，不是官方固定数值。成熟高速骑兵有武将与兵种先手加成，单靠全速加点往往追不上，反而会损失输出。", color=GOLD)
    add_lead(doc, "何太后例外", "何太后不要先无脑全速。只有战报准备回合明确显示敌方同级指挥伤害先于母仪浮梦生效时，才逐步补速度；否则以谋略为主，提高减伤效果。", color=RED)
    add_lead(doc, "输出模式切换", "如果连续战报确认对手不是爆头队，可把荀彧的规避换回落雷，把周瑜的规避换回声东击西。每换一项都同步降低大营保护，只建议在已知对手类型时切换。")

    add_heading(doc, "3. 主力一：魏法控", 1)
    add_heading(doc, "定位与站位", 2)
    add_para(doc, "大营荀彧负责核心策略输出；中军曹植用七步释嫌持续减伤、累计触发回复，并挂大赏三军；前锋魏关羽用千里单骑边打边回，青囊和百战补前锋生存。三人都是截图中已经觉醒的五星，不再消耗新的五星觉醒名额。")
    add_table(
        doc,
        ["武将", "自带 + 学习战法", "加点", "理由"],
        [
            ("大营 荀彧", "驱虎吞狼\n激水之疾\n规避", "先加 5 至 10 点速度，其余谋略", "保留瞬发策略输出；规避挡首次高伤，避免被爆头提前结束战斗"),
            ("中军 曹植", "七步释嫌\n大赏三军\n援军秘策", "全谋略", "大赏放大荀彧前三回合；七步释嫌承担减伤与恢复；援军补后半程"),
            ("前锋 魏关羽", "千里单骑\n战必断金\n青囊秘要", "全攻击；若战损过高再转部分防御", "战必压普攻和追击爆发；青囊稳定自奶，优先保护大营输出窗口"),
        ],
        [1250, 2300, 1500, 4310],
    )
    add_lead(doc, "优点", "三人均已觉醒；阵营一致；无需新增五星材料；打法不依赖未拥有的征服赛季战法。")
    add_lead(doc, "短板", "为了对付高速爆头，本版牺牲了落雷和百战的部分输出/属性。若对面不是普攻追击队，可把战必临时换回百战，但必须接受大营更容易被快速压低兵力。", color=RED)

    doc.add_page_break()
    add_heading(doc, "4. 主力二：吴法控", 1)
    add_heading(doc, "新增五星觉醒名额：给周瑜", 2)
    add_para(doc, "周瑜本身是大营策略输出，新增觉醒后可以同时装焰焚箕轸与规避：保留一项核心输出，同时给大营一次直接免伤机会。小乔已经觉醒，带主动奇术折冲后可以触发鸾凤和鸣的回复，并把控制效果扩到额外目标。四星周泰按你的条件直接觉醒，承担前锋。确认对手不是爆头队时，再把周瑜的规避换回声东击西。")
    add_table(
        doc,
        ["武将", "自带 + 学习战法", "加点", "理由"],
        [
            ("大营 周瑜", "玄武洰流\n焰焚箕轸\n规避", "先加 5 至 10 点速度，其余谋略", "新增觉醒同时容纳核心输出与大营自保；规避挡一次高伤，降低早退风险"),
            ("中军 小乔", "鸾凤和鸣\n反计之策\n奇术折冲", "全谋略", "反计保护周瑜准备；奇术是主动，可触发小乔每回合回复并补妖术控制"),
            ("前锋 四星周泰", "战伤无畏\n青囊秘要\n成竹在胸", "全防御", "自带反击和受伤减免；青囊补持续恢复；成竹补防御和谋略抗性"),
        ],
        [1250, 2300, 1500, 4310],
    )
    add_lead(doc, "为什么不用回马", "周泰自带战伤无畏已经有反击；回马仍是同类反击，优先级不如直接补防御和规避。")
    add_lead(doc, "备选觉醒", "如果你明确不想玩准备法系，才把觉醒改给马云禄。此时周瑜只带焰焚箕轸，马云禄改为钝兵挫锐 + 温酒斩将，太史慈改为连战 + 攻心。", color=GOLD)

    add_heading(doc, "5. 主力三：汉弓抗爆头", 1)
    add_para(doc, "这次把原双追击队改为灵帝 + 四星李儒 + 何太后，原因是战场环境而不是武将星级。灵帝提供稳定输出，李儒负责控制和策略伤害；何太后自带母仪浮梦，使我军全体首次受到攻击时获得规避，并在前四回合概率压低敌军伤害。灵帝、何太后的觉醒状态没有从施政截图确认，因此本版保守地只给各自一个学习战法位。")
    add_table(
        doc,
        ["武将", "自带 + 学习战法", "加点", "理由"],
        [
            ("大营 灵帝", "帝临回光\n连战", "全攻击；内战需要时微调速度", "自带提供稳定输出；未确认觉醒，保守只装连战"),
            ("中军 四星李儒", "计谕废立\n落雷\n危崖困军", "全谋略", "落雷补即时控制；危崖补策略输出；四星可直接觉醒"),
            ("前锋 何太后", "母仪浮梦\n共饮避世", "全谋略；仅按战报需要补速度", "首次受击规避 + 前四回合概率减伤；共饮再补前三回合保护"),
        ],
        [1250, 2300, 1500, 4310],
    )
    add_lead(doc, "克制提醒", "何太后的减伤带概率，不能把它当作稳定全免；遇到禁疗、持续高伤或对方多段伤害时仍可能被穿透。它的价值是提高前三四回合容错，不是保证不被爆头。", color=RED)

    add_heading(doc, "6. 甘宁碰瓷队：可组低配版，不是先驱突击版", 1)
    add_para(doc, "结论是可以组低配版。这里用的是四星甘宁，不是五星甘宁。你同时拥有四星朱儁、四星甘宁、四星凌统，三名武将齐全；四星均可觉醒，统帅值按 10 也没有限制。但你没有先驱突击，所以不能按原报告的双普攻爆发模板配置。改为甘宁携带连战 + 温酒斩将，仍可利用前三回合洞察和增伤换兵，但稳定性与爆发上限都会下降。")
    add_table(
        doc,
        ["站位", "武将与战法", "加点", "作用"],
        [
            ("大营", "四星朱儁\n西乡武功 + 长兵方阵 + 反击之策", "全谋略", "前两回合先手与动摇；长兵给群体分兵，反击提高换兵上限"),
            ("中军", "四星甘宁\n轻侠妄为 + 连战 + 温酒斩将", "全攻击", "前三回合洞察、增伤；连战增加普攻和温酒触发机会"),
            ("前锋", "四星凌统\n国士 + 百战精兵 + 破甲", "全攻击", "前四回合洞察；百战补属性，破甲补追击并削防"),
        ],
        [1050, 3100, 1300, 3910],
    )
    add_lead(doc, "定位", "这是碰瓷工具队，不是第四支满兵主力。用少量兵先撞对方主力，制造战损后由前三队收割；打不过并不等于配错。")
    add_lead(doc, "与标准模板的差异", "你没有先驱突击，也没有截图可见的破魂、迷阵、疑兵。核心先手与洞察机制仍成立，但爆发频率和控制上限都低于标准模板；因此只把它当低兵力换战损工具，不按第四主力培养。", color=RED)

    add_heading(doc, "7. 四队之外：轮换与拆迁", 1)
    add_heading(doc, "7.1 双追击轮换队", 2)
    add_para(doc, "太史慈 + 马云禄 + 四星刘备并不弱，只是面对你当前常见的高速爆头队，保护链不如何太后汉弓。对手偏慢或已经探明阵容时可换回：太史慈用连战 + 钝兵挫锐，马云禄未觉醒时用破甲，四星刘备用共饮避世 + 百战精兵。连战、共饮已被主力/碰瓷占用，因此这是一支轮换队，不能与四队同时满配。")
    add_heading(doc, "7.2 拆迁与铺路", 2)
    add_para(doc, "剩余满红四星用于拆迁、铺路和斯巴达即可，不再追求战斗强度。优先挑本身不进前三队的低 COST 四星，装云梯、毁墙、冲车、投石轰击等攻城战法；不要占用三队的 S/A 核心战法，也不要为了凑满 10 队分散战法经验。")
    add_callout(doc, "队伍数量建议", "当前账号合理状态是 3 支正式主力 + 1 支甘宁低配碰瓷 + 1 支双追击轮换 + 1 至 2 支拆迁/铺路队。竹林七贤队已经放弃，没有必要为了凑数量硬配满 10 支战斗队。", fill=PALE_BLUE, label_color=DARK_BLUE)

    add_heading(doc, "8. 战法拆解与研究", 1)
    add_heading(doc, "8.1 现在不要拆的五星", 2)
    add_table(
        doc,
        ["武将", "可研究战法", "当前结论"],
        [
            ("张春华", "浑水摸鱼", "强战法，但唯一张春华仍是高价值控制将；等第二张再拆"),
            ("周瑜", "不攻", "本报告新增觉醒主力，绝对不拆当前这张"),
            ("何太后", "空城", "本版第三主力的抗爆头核心；绝不拆当前这张，等第二张"),
            ("魏关羽", "无心恋战", "第一主力前锋，且已觉醒；不拆"),
            ("马云禄", "愈战愈勇", "第三队副核；不拆"),
            ("曹植 / 荀彧 / 小乔 / 太史慈", "三术奇谋 / 怯心夺志 / 掎角之势 / 钝兵挫锐", "均为已觉醒现役核心；不拆"),
        ],
        [1700, 2500, 5160],
    )
    add_heading(doc, "8.2 四星研究顺序", 2)
    add_para(doc, "原则是“先留一张满红、觉醒、可战斗的本体，再拆多余副本”。李儒、朱儁、四星甘宁、凌统进入四队方案，不能拆本体；山涛、向秀保留作施政。以下顺序只针对以后出现的多余副本。")
    add_table(
        doc,
        ["优先级", "多余四星来源", "研究目标", "用途"],
        [
            ("高", "李儒", "楚歌四起", "S1 法系持续输出；当前汉弓主力可用"),
            ("高", "朱然", "伐谋", "低门槛策略输出/削弱，补第二队或轮换队"),
            ("中", "韩当", "长兵方阵", "四星物理队、拆迁队补输出；已有副本时不急"),
            ("中", "典韦或汉刘备", "青囊秘要", "只有确认缺第二份前锋自奶时再研究"),
            ("中", "鲁肃或王美人", "声东击西", "已有一份时只为第二套法队准备"),
            ("低", "周泰", "回马", "与周泰自带反击同类，当前不优先"),
            ("低", "甘宁或朱儁", "长驱直入", "偏过渡；当前主力不需要"),
        ],
        [850, 2100, 1800, 4610],
    )
    add_lead(doc, "战法经验", "先把三队 0 号自带战法升满，再升战必、反计、大赏；随后升各队核心输出。B/C 过渡战法不必与 S/A 同步拉满。")

    add_heading(doc, "9. 施政方案", 1)
    add_para(doc, "施政页明确可见：灵帝 Lv.1、周姬 Lv.1、皇甫嵩 Lv.13、山涛 Lv.10、向秀 Lv.7。灵帝进入第三主力后不能同时施政，所以金币方案把灵帝列为“战斗与税收二选一”。下表效果文字来自本地资料库的政策完整描述；政策等级会影响实际数值时，应以游戏内当前等级详情为准，本报告不把完整描述直接当作你此刻的实时收益。", color=MUTED)
    add_heading(doc, "方案 A：金币获取方向", 2)
    add_table(
        doc,
        ["顺序", "武将 / 政策", "完整描述中的效果", "操作建议"],
        [
            ("1", "周姬 · 食租衣税", "税收提高 4800", "第三主力不占用周姬，作为常驻金币核心"),
            ("2", "向秀 · 备位充数", "税收提高 2500；部队维持粮草消耗提高 5%", "赛季末缺金币时启用；粮草紧张时降低优先级"),
            ("3", "灵帝 · 卖官鬻爵", "税收提高 6000", "若停用汉弓第三队才回施政；战斗与税收不能同时计算"),
            ("4", "皇甫嵩 · 尽忠职守", "部队维持消耗降低 50%", "抵消多队维持压力，也缓和向秀副作用"),
            ("5", "山涛 · 山公启事", "补给范围内出征战斗后恢复伤兵 15%", "不直接产金币，但减少征兵和资源损耗"),
        ],
        [700, 2100, 3100, 3460],
    )
    add_lead(doc, "加点次序", "汉弓第三队常驻时，先投周姬，再看粮草决定向秀；皇甫嵩现有等级较高，先保留而不是继续无脑追加。若停用汉弓并把灵帝转回施政，灵帝重新升为金币第一优先。")
    add_heading(doc, "方案 B：自由建议——战斗续航与资源节流", 2)
    add_table(
        doc,
        ["顺序", "武将 / 政策", "为什么这样排"],
        [
            ("1", "皇甫嵩 · 尽忠职守", "三主力和多支功能队并存时，维持消耗下降最直接；赛季末连续作战更省粮"),
            ("2", "山涛 · 山公启事", "在所属建筑补给范围内连续出征时回伤兵，降低回城补兵频率"),
            ("3", "周姬 · 食租衣税", "不占用战斗武将，保留稳定税收底盘"),
            ("4", "灵帝 · 卖官鬻爵", "只有停用汉弓第三队时才启用；不要同时计算战斗与施政收益"),
            ("5", "向秀 · 备位充数", "最后考虑；5% 维持粮草增加与本方案目标相反"),
        ],
        [700, 2500, 6160],
    )
    add_callout(doc, "施政选择", "要金币就选方案 A；要赛季末打架、驻守、频繁调兵，就选方案 B。灵帝如果作为第三主力出战，就必须退出施政；若你更看重金币，可以停用汉弓，换回太史慈双追击，再让灵帝回施政。", fill=PALE_BLUE, label_color=DARK_BLUE)
    add_heading(doc, "10. 实施顺序", 1)
    steps = [
        ("第 1 步", "卸下旧队全部学习战法；战法数量按截图分母计，不再按分子计。"),
        ("第 2 步", "觉醒周瑜；四星周泰、李儒、朱儁、甘宁、凌统按需觉醒。"),
        ("第 3 步", "先装第一队魏法控并把 0 号自带战法、落雷/激水、大赏升起来。"),
        ("第 4 步", "装第二队吴法控，确认小乔至少带一项主动战法，才能稳定触发鸾凤和鸣回复。"),
        ("第 5 步", "装第三队汉弓：灵帝连战，李儒落雷 + 危崖，何太后共饮；灵帝同时退出施政。"),
        ("第 6 步", "装甘宁低配碰瓷队：甘宁用连战 + 温酒，凌统用百战 + 破甲；少量兵先撞，不当满兵主力。"),
        ("第 7 步", "前三主力各打 10 场同等级对手，记录对方爆发来源和准备回合先后；碰瓷队只看换兵效率。"),
        ("第 8 步", "需要输出补刀时再换太史慈双追击；它与汉弓、碰瓷共享战法，不能同时按满配计算。"),
    ]
    add_table(doc, ["顺序", "动作"], steps, [1300, 8060], header_fill=PALE_GRAY, font_size=9.6)

    add_heading(doc, "11. 需要你在游戏内自行核实的项目", 1)
    add_lead(doc, "战法数量口径", "本修订版已按你的指示把分母当作初始拥有数量。若客户端分母实际表示演练上限而非账号拥有数，需要立刻回退到保守方案；这是唯一需要你确认的数量口径。")
    add_lead(doc, "政策当前数值", "资料库给的是政策完整描述；你当前不同政策等级的实时收益，以游戏内政策详情为准。")
    add_lead(doc, "未展示卡牌", "武将库截图只覆盖当前排序的主要五星/四星。若还有未展示的五星核心或第二张材料卡，觉醒和拆解顺序可能变化。")
    add_lead(doc, "战场环境", "如果本服菜刀极多，战必优先级上升；如果法系主动队多，反计优先级上升。三队核心结构不变，只做战必/反计的临时互换。")

    add_heading(doc, "来源与核验说明", 1)
    add_para(doc, "一手账号证据：D:\\Desktop\\新建文件夹 (2) 中的 8 张截图，时间为 2026-08-25。武将名、卡面“极”、战法名称与初始数量、施政武将和等级均以截图为准。", size=9.5)
    add_para(doc, "本地交叉核验：D:\\Desktop\\shandou\\资料库\\hero_extra.json、official_skill_db.json。用于核对武将自带战法、学习战法效果及政策完整描述；它们是本地资料快照，不等同于当前游戏客户端公告。", size=9.5)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(5)
    r = p.add_run("机制参考：")
    set_run_font(r, size=9.5, bold=True, color=NAVY)
    add_hyperlink(p, "4399《武将属性一览》", "https://news.4399.com/shtzb/xinde/m/690681.html")
    r = p.add_run("（说明“极”、觉醒与第三战法格）。")
    set_run_font(r, size=9.5, color=BLACK)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(5)
    r = p.add_run("碰瓷结构参考：")
    set_run_font(r, size=9.5, bold=True, color=NAVY)
    add_hyperlink(p, "17173《碰瓷队介绍》", "https://news.17173.com/z/stzb/content/11152019/152638303.shtml")
    r = p.add_run("；用于核对四星朱儁、甘宁、凌统的经典结构与碰瓷定位。具体战法按本账号库存替换。")
    set_run_font(r, size=9.5, color=BLACK)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(5)
    r = p.add_run("S1 结构参考：")
    set_run_font(r, size=9.5, bold=True, color=NAVY)
    add_hyperlink(p, "17173《平民如何玩转 S1 赛季》", "https://news.17173.com/z/stzb/content/04092022/154548752.shtml")
    r = p.add_run("；用于交叉确认 S1 常见的灵帝/李儒/何太后结构。该文章是攻略资料，不是官方实时平衡公告。")
    set_run_font(r, size=9.5, color=BLACK)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(5)
    r = p.add_run("何太后机制参考：")
    set_run_font(r, size=9.5, bold=True, color=NAVY)
    add_hyperlink(p, "小米游戏中心《母仪浮梦》解析", "https://game.xiaomi.com/viewpoint/1392551438_1644929387265_148")
    r = p.add_run("；用于核对全队首次受击规避、前四回合概率降伤，以及同级指挥先后可能受速度影响。该页面是玩家攻略，不是官方公告。")
    set_run_font(r, size=9.5, color=BLACK)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(5)
    r = p.add_run("S1 普攻队克制参考：")
    set_run_font(r, size=9.5, bold=True, color=NAVY)
    add_hyperlink(p, "17173《经典菜刀队搭配解析》", "https://news.17173.com/z/stzb/content/04012020/073650069.shtml")
    r = p.add_run("；用于交叉确认 S1 中战必断金对普攻型菜刀的克制关系。具体对局仍以你的战报为准。")
    set_run_font(r, size=9.5, color=BLACK)

    add_para(doc, "速度微调参考：D:\\Desktop\\shandou\\资料库\\reports_json\\武将咋加点？ 一篇看明白!.json。5 至 10 点仅为攻略经验起点，不是官方固定阈值；最终以你自己的战报行动顺序校准。", size=9.5, color=MUTED)

    add_para(doc, "报告原则：账号截图与用户确认优先于网络攻略；本地数据用于核字和战法机制；政策实时等级收益和未展示卡牌均明确列为待核实，不作猜测。", size=9.5, bold=True, color=NAVY, before=10)

    # Make all paragraphs use East Asian font and protect short heading rows.
    for p in doc.paragraphs:
        for r in p.runs:
            rpr = r._element.get_or_add_rPr()
            rfonts = rpr.rFonts
            if rfonts is None:
                rfonts = OxmlElement("w:rFonts")
                rpr.insert(0, rfonts)
            rfonts.set(qn("w:eastAsia"), "Microsoft YaHei")

    doc.core_properties.title = "S1赛季末账号配将与施政建议（二次修订版）"
    doc.core_properties.subject = "率土之滨账号定制配将、战法拆解与施政报告"
    doc.core_properties.author = "Codex"
    doc.core_properties.keywords = "率土之滨,S1,配将,战法,觉醒,施政"
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
