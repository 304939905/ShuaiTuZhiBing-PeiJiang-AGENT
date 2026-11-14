# -*- coding: utf-8 -*-
"""按当前标杆结构生成《战法阈值精简学习报告》。"""
from pathlib import Path
import json

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(r"D:\Desktop\shandou")
DB_PATH = ROOT / "资料库" / "threshold_db.json"
BENCHMARK = ROOT / "报告库" / "标杆" / "攻其不备体系投稿解析与配队判断_当前标杆_20260907.docx"
OUT = ROOT / "报告库" / "战法阈值精简学习报告.docx"
MULTI_EFFECT = {"始计", "徽言龙凤", "审时定计", "鼎足江东", "同仇敌忾", "奉令护蜀"}


def font_run(run, size=None, bold=None, color="000000", italic=None):
    run.font.name = "Microsoft YaHei"
    rpr = run._element.get_or_add_rPr()
    for key in ("eastAsia", "ascii", "hAnsi"):
        rpr.rFonts.set(qn(f"w:{key}"), "Microsoft YaHei")
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)


def clear_body(document):
    body = document._element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def set_cell_fill(cell, color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), color)


def set_cell_margins(cell, top=45, start=55, bottom=45, end=55):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table, color="D9D9D9", size="5"):
    borders = table._tbl.tblPr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        table._tbl.tblPr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        node = borders.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            borders.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), size)
        node.set(qn("w:color"), color)


def repeat_header(row):
    node = OxmlElement("w:tblHeader")
    node.set(qn("w:val"), "true")
    row._tr.get_or_add_trPr().append(node)


def add_para(document, text="", bold_lead=None, italic=False, color="000000"):
    p = document.add_paragraph()
    if bold_lead and text.startswith(bold_lead):
        font_run(p.add_run(bold_lead), 9.6, True, color)
        font_run(p.add_run(text[len(bold_lead):]), 9.6, color=color, italic=italic)
    else:
        font_run(p.add_run(text), 9.6, color=color, italic=italic)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.13
    return p


def add_heading(document, text, level=1):
    p = document.add_heading(text, level=level)
    for run in p.runs:
        font_run(run, 13 if level == 1 else 11, True, "243A55" if level == 1 else "365F91")
    p.paragraph_format.space_before = Pt(9 if level == 1 else 6)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    return p


def add_bullet(document, text):
    p = document.add_paragraph(style="List Bullet")
    font_run(p.add_run(text), 9.6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.1
    return p


def add_number(document, number, text):
    p = document.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.18)
    p.paragraph_format.first_line_indent = Inches(-0.18)
    font_run(p.add_run(f"{number}. "), 9.6, True, "365F91")
    font_run(p.add_run(text), 9.6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.1
    return p


def add_table(document, headers, rows, widths, font_size=7.3, center=(1, 2, 3, 4, 5)):
    table = document.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for cell, text, width in zip(table.rows[0].cells, headers, widths):
        cell.width = Inches(width)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_fill(cell, "3F5264")
        set_cell_margins(cell)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        font_run(p.add_run(text), 7.7, True, "FFFFFF")
    repeat_header(table.rows[0])
    for ri, row_data in enumerate(rows, 1):
        cells = table.add_row().cells
        table.rows[-1]._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for ci, (cell, text, width) in enumerate(zip(cells, row_data, widths)):
            cell.width = Inches(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            if ri % 2 == 1:
                set_cell_fill(cell, "F3F6F8")
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if ci in center else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            font_run(p.add_run(str(text)), font_size, ci == 0)
    set_table_borders(table)
    return table


def note_for(entry):
    skill = entry["skill"]
    notes = []
    if skill in MULTI_EFFECT:
        notes.append("多效分项")
    if entry.get("growth") in (None, "无数据", "待数据"):
        notes.append("增长率无数据")
    if entry.get("table_spelling"):
        notes.append(f"原表名：{entry['table_spelling']}")
    if skill == "遗志":
        notes.append("9999%=回满血占位；不套公式")
    if skill in {"巧音唤蝶一", "巧音唤蝶二", "其徐如林（增长）"}:
        notes.append("同一战法的子效果")
    return "；".join(notes) or "—"


def build():
    db = json.loads(DB_PATH.read_text(encoding="utf-8"))
    document = Document(BENCHMARK)
    clear_body(document)
    section = document.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.left_margin = section.right_margin = Inches(0.72)
    section.top_margin = section.bottom_margin = Inches(0.62)
    normal = document.styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.font.size = Pt(9.6)
    title_style_ppr = document.styles["Title"]._element.get_or_add_pPr()
    old_border = title_style_ppr.find(qn("w:pBdr"))
    if old_border is not None:
        title_style_ppr.remove(old_border)

    p = document.add_paragraph(style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font_run(p.add_run("战法属性阈值与参数速查"), 22, True, "243A55")
    p.paragraph_format.space_after = Pt(5)
    p = document.add_paragraph(style="Subtitle")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font_run(p.add_run("精编学习报告  当前标杆结构  2026 09 12"), 10.5, italic=True, color="555555")
    p.paragraph_format.space_after = Pt(10)

    add_para(document, "这份报告把玩家整理的63条参数作为稳定参考表保留，同时纠正旧版的证据混写与绝对化结论。它用于估算战法显示数值、比较下一档属性成本，并辅助配将加点；不替代当前客户端战法文本和实际战报。")
    add_heading(document, "报告索引")
    add_para(document, "关键词：战法阈值、属性加成、基础值、增长率、四舍五入、大赏三军、神兵天降、加点、队内卡速、参数表")
    add_para(document, "资料性质：机制方法 + 玩家整理参数速查。参数表录入于2026-08-20，本次复核于2026-09-12；参数默认持续使用，用户提供新版资料时整体更新。战法名称和多效结构已用本地当前战法库复核，隐藏增长率仍以玩家表为来源。")

    add_heading(document, "一 核心结论")
    add_bullet(document, "本报告所说的“阈值”，首先是公式取整后显示数值跨档：属性继续提高，但未跨过取整边界时，面板整数可能不变。现有材料不足以证明游戏底层结算必然丢弃全部小数，因此不再把档间属性写成绝对“无效”。")
    add_bullet(document, "玩家表使用共同计算框架：最终显示值 = 基础值 + 增长率 ×（对应属性 − 80），再按该行取舍方式处理。大赏三军簇的30%基础、0.150%增长率已由用户确认；其他战法必须读取各自行参数。")
    add_bullet(document, "“受某属性影响”只说明存在属性关联，不能单凭这句话反推出增长率、取整方式或是否与本表相同；主动、指挥、被动、追击也不能只按类型一刀切。")
    add_bullet(document, "加点目标不是机械“过线后全速度”。应比较跨下一档需要多少点、行动顺序是否关键、主属性对其他战法是否仍有收益，再决定主属性、速度或生存属性。")

    add_heading(document, "二 证据等级与使用边界")
    add_table(document, ["内容", "当前证据", "可以怎么用", "不能怎么用"], [
        ["战法名与多效结构", "本地当前战法库", "锁定正确名称、关联属性和多效分项", "不能证明隐藏增长率"],
        ["基础值/增长率/取整", "天阶功法玩家参数表", "作为配点估算和档位速查", "不能伪装成官方公布参数"],
        ["大赏三军簇公式", "玩家表 + 用户确认", "按30% + 0.150%×（谋略−80）计算", "不能自动套到所有战法"],
        ["90%减伤上限、兵力阈值", "视频口述", "仅作待验证线索", "不纳入本报告通用规则"],
    ], [1.15, 1.45, 2.25, 2.15], font_size=8.0, center=(0, 1))

    add_heading(document, "三 计算与加点方法")
    add_para(document, "计算模板：显示值 = 基础值 B + 增长率 g ×（最终对应属性 A − 80），再按该行写明的方式取整。最终对应属性应读取属性界面长按后的值，并计入宝物、阵营和兵种特性等已显示加成。", bold_lead="计算模板：")
    add_para(document, "示例：大赏三军取 B=30%、g=0.150%，当谋略 A=176 时，30 + 0.150×（176−80）=44.4，按四舍五入取整显示为44%。旧视频口述的46%来自另一套错误公式，已不采用。", bold_lead="示例：")
    steps = [
        "先确认当前战法版本和具体效果分项；同一战法可能同时有增伤、减伤或恢复，不能只算一行代替全部效果。",
        "读取最终属性 A，代入该行的 B、g 和取整方式；增长率写“无数据”的行不能反推，保持未知。",
        "逐点增加 A 并重复计算，找到显示值第一次变化的位置；这比背固定“每6至7点一档”更稳，因为不同增长率的步长不同。",
        "比较跨档成本与机会成本：速度能否改变关键先后、主属性是否同时提升其他战法、生存属性是否解决首轮暴毙。",
        "最后看战报。若显示值跨档却没有改变队伍关键事件，或者为抢档破坏了行动顺序，就不应把跨档当成唯一目标。",
    ]
    for i, text in enumerate(steps, 1):
        add_number(document, i, text)

    add_heading(document, "四 参数速查表")
    add_para(document, "共63行，覆盖增伤、减伤、恢复、属性及其他数值效果。重复战法通常是多效或子效果分项；“基础/增长率”沿用玩家表，战法名和已知属性错误按本地战法库校正。")
    headers = ["战法", "效果", "属性", "基础", "增长率", "取整", "注记"]
    widths = [1.28, 0.88, 0.68, 0.72, 0.78, 1.18, 1.52]
    for category in db["categories"]:
        add_heading(document, category["name"], level=2)
        rows = []
        for entry in category["entries"]:
            rows.append([
                entry["skill"], entry["effect"], entry.get("main_attr") or "—",
                entry.get("base") if entry.get("base") is not None else "—",
                entry.get("growth") if entry.get("growth") is not None else "—",
                entry.get("rounding") or "—", note_for(entry),
            ])
        add_table(document, headers, rows, widths)

    add_heading(document, "五 已完成的关键校正")
    add_bullet(document, "视频画面中的示例武将是魏·曹操，不是旧报告写的“曹聪”；示例公式按已确认的大赏三军簇公式重算为44%。")
    add_bullet(document, "奉令护蜀是多效战法：普攻增伤受攻击影响，减伤受防御影响；原玩家表把减伤属性写成攻击，现已校正为防御。")
    add_bullet(document, "徽言龙凤同时包含士气提升与伤害提升等效果；增伤增长率没有确切数据，保留“无数据”，不自行补值。")
    add_bullet(document, "遗志的9999%是“回复至满血”的占位编码，不是可代入通用公式的基础值。")
    add_bullet(document, "伏波扬砂、僭号天子、威震河朔、缓师徐持四处名称已按本地战法库校正，原表写法仅保留在注记中。")

    add_heading(document, "六 AI独立判断")
    add_para(document, "这张表的真正价值不是给每名武将生成固定加点，而是把“多投入一点属性”转化成可比较的边际收益。账号配将时，应先确定队伍职责和关键行动顺序，再用表计算跨档成本；表格不能反过来替代队伍设计。")
    add_para(document, "对于同时影响多个战法的主属性，即使某一行显示值尚未跨档，属性也可能继续提高其他伤害、恢复或效果；因此“未跨档等于白点”不能作为通用结论。速度同样只在改变关键先后时有明确价值。")

    add_heading(document, "七 适用边界")
    add_para(document, "参数表按用户要求作为稳定参考长期保留；收到新版参数资料前不主动废弃。若当前客户端更改了战法基础值、关联属性、效果结构或取整显示，应以新文本为准并更新整行。精确到单点的加点建议仍需结合当前最终面板、宝物、兵种、队内卡速和近期战报。")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUT)
    print(f"SAVED {OUT}")
    print(f"SIZE {OUT.stat().st_size}")


if __name__ == "__main__":
    build()
