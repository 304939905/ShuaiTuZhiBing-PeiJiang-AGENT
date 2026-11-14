"""赛季三份独立学习报告的当前标杆母本。

内容来自 2026-09-04 至 2026-09-05 已完成的原帧、转写和本地库核验。
报告只保留可独立学习的结论、条件、配置和边界，不把案例当成当前账号答案。
"""
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


BENCHMARK = Path(r"D:\Desktop\shandou\报告库\标杆\攻其不备体系投稿解析与配队判断_当前标杆_20260907.docx")

TITLE = "最强四星0氪蜀之智，萌新玩家必看"
RANK_TITLE = "盘点全网最强四星神队排名，从第八到第一，越往后越离谱，都有配置和战报！"
KEEP_TITLE = "萌新这些四星卡千万别拆了，s赛季有大用！"
MERGED_TITLE = "一分钟了解率土之滨玩家要经历的赛季和试师赛季征服赛季，推荐百业争鸣和北伐兴汉作为新手初入试师副本。"


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


def set_cell_margins(cell, top=80, start=85, bottom=80, end=85):
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


def set_table_borders(table, color="D9D9D9", size="6"):
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        node = borders.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            borders.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), size)
        node.set(qn("w:color"), color)


def set_repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    node = OxmlElement("w:tblHeader")
    node.set(qn("w:val"), "true")
    tr_pr.append(node)


def add_para(document, text="", bold_lead=None, keep=False):
    p = document.add_paragraph()
    if bold_lead and text.startswith(bold_lead):
        font_run(p.add_run(bold_lead), 10.5, True)
        font_run(p.add_run(text[len(bold_lead):]), 10.5)
    else:
        font_run(p.add_run(text), 10.5)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.25
    p.paragraph_format.keep_with_next = keep
    return p


_number_counts = {}


def add_heading(document, text):
    p = document.add_heading(text, level=1)
    for run in p.runs:
        font_run(run, 14, True)
    p.paragraph_format.space_before = Pt(15)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.keep_with_next = True
    _number_counts[id(document)] = 0
    return p


def add_bullet(document, text):
    p = document.add_paragraph(style="List Bullet")
    font_run(p.add_run(text), 10.5)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.2
    return p


def add_number(document, text):
    key = id(document)
    _number_counts[key] = _number_counts.get(key, 0) + 1
    p = document.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.18)
    p.paragraph_format.first_line_indent = Inches(-0.18)
    font_run(p.add_run(f"{_number_counts[key]}. "), 10.5)
    font_run(p.add_run(text), 10.5)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.2
    return p


def new_report(title):
    document = Document(BENCHMARK)
    clear_body(document)
    section = document.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.left_margin = section.right_margin = Inches(1.25)
    section.top_margin = section.bottom_margin = Inches(1.0)

    normal = document.styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor(0, 0, 0)

    title_p = document.add_paragraph(style="Title")
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font_run(title_p.add_run(title), 25, True)
    title_p.paragraph_format.space_after = Pt(8)

    subtitle = document.add_paragraph(style="Subtitle")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font_run(subtitle.add_run("精编学习报告  当前标杆结构  2026 09 07"), 11.5, italic=True)
    subtitle.paragraph_format.space_after = Pt(20)
    return document


def add_table(document, headers, rows, widths, font_size=8.2, center_columns=(0,)):
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
        font_run(p.add_run(text), 8.7, True, "FFFFFF")
    set_repeat_header(table.rows[0])

    for ri, row_data in enumerate(rows, 1):
        cells = table.add_row().cells
        tr_pr = table.rows[-1]._tr.get_or_add_trPr()
        tr_pr.append(OxmlElement("w:cantSplit"))
        for ci, (cell, text, width) in enumerate(zip(cells, row_data, widths)):
            cell.width = Inches(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            if ri % 2 == 1:
                set_cell_fill(cell, "F3F6F8")
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if ci in center_columns else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.08
            font_run(p.add_run(text), font_size, ci == 0)
    set_table_borders(table)
    return table


def build_shuzhi(out):
    d = new_report("四星蜀智案例的配置与取舍")
    add_para(d, "这份报告整理一套由五星诸葛亮、四星庞统和四星徐庶组成的蜀智案例。它的学习价值在于把阵位、实际兵系、战法触发和替换代价放在一起判断；视频题名中的“四星”“零氪”不能代替真实资源核算。")
    add_heading(d, "报告索引")
    add_para(d, "关键词：蜀智、形兵之极、实际兵系、策略易伤、追击、暴走、替换条件、物理普攻弱点")
    add_para(d, "核心版本：蜀五星诸葛亮〔诸葛锦囊〕，本场出战弓兵；蜀步四星庞统〔索命连环〕；蜀骑四星徐庶〔沙场破阵〕。")
    add_heading(d, "一 核心结论")
    add_bullet(d, "本场弓、步、骑三种实际兵系满足形兵之极的队伍条件。换将或改变兵系后必须重新核对，不能只看战法仍在就认定生效。")
    add_bullet(d, "庞统负责单点移除增益、策略易伤和谋略伤害；徐庶依靠普攻触发追击并尝试施加暴走；诸葛亮承担辅助与补充输出。")
    add_bullet(d, "先驱突击增加前期普攻机会，但始计的洞察需要受伤后触发。先行动不等于关键控制到来前已经获得洞察。")
    add_bullet(d, "作者承认队伍面对物理普攻类对手吃亏。精选胜仗不能证明稳定胜率，也不能证明该队不需要稀缺战法和宝物。")
    add_heading(d, "二 配置与职责")
    add_table(d, ["位置", "武将版本", "实际兵系", "战法配置", "职责与条件"], [
        ["大营", "蜀五星诸葛亮\n〔诸葛锦囊〕", "弓", "连环\n形兵之极", "辅助并补充策略输出。形兵条件按本场兵系核对。"],
        ["中军", "蜀步四星庞统\n〔索命连环〕", "步", "绝水遏敌\n焰焚箕轸", "单点移除增益与策略易伤；学习战法需要准备。"],
        ["前锋", "蜀骑四星徐庶\n〔沙场破阵〕", "骑", "先驱突击\n始计", "用普攻触发追击与暴走；始计洞察受时序限制。"],
    ], [0.55, 1.35, 0.62, 1.35, 2.13])
    add_para(d, "画面中的诸葛亮基础资料对应步兵版本，但本场实际出战为弓兵。报告分别记录基础版本与出战兵系，不据此另造武将版本，也不推测兵系变化的取得方式。")
    add_heading(d, "三 机制判断方法")
    add_number(d, "先检查形兵之极。以实际出战兵系判断三人是否各不相同，再确认大营发动率、前锋保护和中军首次伤害分别服务谁。")
    add_number(d, "再拆解庞统的伤害链。索命连环的易伤是单体，学习战法的目标可能不同，不能把全部伤害都按同时命中同一易伤目标计算。")
    add_number(d, "然后检查徐庶的行动链。无法普攻时不能按正常次数估计追击收益；增加尝试次数也不等于保证暴走。")
    add_number(d, "最后检查速度和承伤。面对更快的普攻爆发队，先看前锋能否撑过首轮、徐庶能否完成普攻，以及始计洞察是否及时取得。")
    add_heading(d, "四 替换方案与代价")
    add_number(d, "绝水遏敌可以换火烧连营。换后输出结构改变，并可能失去禁疗作用；应按主要对手决定，而不是只比较伤害。")
    add_number(d, "焰焚箕轸可以换三术奇谋。视频中的“大火”和“3术”只在本来源中分别指这两个战法，不能扩展成全局简称。")
    add_number(d, "作者不建议在本队改用河内世泽，但没有提供充分同条件对照。这是作者对本组合的取舍，不是战法强弱的通用结论。")
    add_number(d, "作者建议徐庶条件允许时使用元戎提高上限。宝物建议不替代先驱突击或始计，也不证明其他宝物不可用。")
    add_heading(d, "五 AI独立判断")
    add_para(d, "这队的低星武将容易取得，但战法成本并不低。账号缺少形兵之极、先驱突击或始计时，不能因题名含“零氪”便视为可直接复刻。")
    add_para(d, "伤害评估应分开发动、准备、命中目标和增益覆盖。形兵只提高中军每回合首次伤害，庞统易伤又是单体，因此不能把所有增伤乘到整队每段输出上。")
    add_para(d, "替换三术奇谋或火烧连营会改变目标、附带效果和伤害节奏。没有当前战法文本和对照战报时，只能保留为待测试方案。")
    add_heading(d, "六 适用边界")
    add_para(d, "本案例提供完整配置、作者观点和定点核验后的替换方向，没有统一样本量、完整胜率或同条件对照。具体数值和战法效果以当前客户端为准。")
    add_para(d, "应用到账号前，重新核对武将版本、实际兵系、战法数量、赛季可用性、速度顺序和主要对手。该报告用于学习判断方法，不是固定配将答案。")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    d.save(out)


def build_rank(out):
    d = new_report("七组低星队伍案例的配置与适用条件")
    add_para(d, "视频实际按第七至第一介绍七组队伍，题名“第八到第一”与内容数量不一致。本报告保留完整配置和成立条件，用于比较不同投入方式；作者顺序不代表经过统一战报验证的客观强弱。")
    add_heading(d, "报告索引")
    add_para(d, "关键词：低星队伍、资源成本、称号、恢复控制、追击、神赏、重复战法、替换代价")
    add_para(d, "七组案例：三星小晋弓、四星小桃园、竹林七贤、蜀智、宁元刀、甘宁曹仁关兴与张苞、荀彧甘宁孙策。报告完整记录21个阵位、63个战法位；队伍之间存在武将和战法重复，不能视为同一账号可同时组建的七队。")
    add_heading(d, "一 核心结论")
    add_bullet(d, "低星只说明部分武将取得成本较低，不代表整队战法便宜。后几组占用形兵之极、先驱突击、反计之策、神兵天降和大赏三军等资源。")
    add_bullet(d, "七组队伍分别服务消耗、恢复控制和前期输出。评价标准应随用途变化，不能只按作者名次比较。")
    add_bullet(d, "作者展示的是挑选后的个例战报，没有统一兵力、对手和样本量，不能支持“全网最强”“稳定八回合”或“全程免控”等结论。")
    add_bullet(d, "重复控制、重复战法和共享武将都要全局核算。单队纸面成立，不等于多队配置可以同时落地。")
    add_heading(d, "二 七组配置对比")
    rows = [
        ["七", "三星小晋弓", "大营 晋弓3冯紞〔落石〕：夹攻、伏兵\n中军 晋弓3王衍〔速战坚守〕：伏兵、谋攻\n前锋 晋步3荣晦〔游击〕：突击、追击", "低成本消耗。两份伏兵需分别计数；打平与高收益不是一回事。"],
        ["六", "四星小桃园", "大营 汉步4刘备〔义勇军〕：援军秘策、增援\n中军 蜀步4关羽〔迎险御侮〕：斩铁、破胆\n前锋 蜀步4张飞〔锐矛贯体〕：青囊秘要、斩铁", "恢复与控制要在大量失兵前生效。两份斩铁不会自动叠加控制。"],
        ["五", "竹林七贤", "大营 魏步4阮籍〔青白分明〕：落雷、声东击西\n中军 魏步4嵇康〔广陵绝唱〕：落雷、迷阵\n前锋 晋步4刘伶〔幕天席地〕：危崖困军、迷阵", "称号提供低配空间，但全队并非晋阵营。重复落雷和迷阵要检查状态与目标。"],
        ["四", "蜀智", "大营 蜀5诸葛亮〔诸葛锦囊〕：连环、形兵之极\n中军 蜀步4庞统〔索命连环〕：焰焚箕轸、绝水遏敌\n前锋 蜀骑4徐庶〔沙场破阵〕：先驱突击、始计", "形兵按实际出战兵系核对。单体易伤不覆盖全部目标，且队伍怕物理普攻。"],
        ["三", "宁元刀", "大营 吴弓4甘宁〔轻侠妄为〕：先驱突击、温酒斩将\n中军 5卫瓘〔持节镇西〕：长兵方阵、衡轭\n前锋 蜀骑4徐庶〔沙场破阵〕：连战、攻心", "徐庶两槽可整体改计险远近、疾战；需重查距离差和失去攻心后的功能。"],
        ["二", "甘宁 曹仁\n关兴与张苞", "大营 吴弓4甘宁〔轻侠妄为〕：先声夺人、衡轭\n中军 魏步4曹仁〔八门金锁〕：反计之策、计险远近\n前锋 5关兴与张苞〔勇将继传〕：先驱突击、枭雄", "计险远近要求三将基础攻击距离不同。枭雄与轻侠妄为都不能推出全程免控。"],
        ["一", "荀彧 甘宁\n孙策", "大营 5荀彧〔驱虎吞狼〕：大赏三军、神兵天降\n中军 吴弓4甘宁〔轻侠妄为〕：先驱突击、三军齐出\n前锋 5孙策〔霸王渡江〕：衡轭、反计之策", "高投入前期体系。神赏和先驱不是全程增益；应先比较主力让渡资源的损失。"],
    ]
    add_table(d, ["顺序", "案例", "完整画面配置", "可复用判断"], rows, [0.48, 1.12, 2.55, 1.85], 7.9, (0, 1))
    add_heading(d, "三 比较方法")
    add_number(d, "先确定用途。廉价消耗队看投入与补兵收益；恢复控制队看生效时间；前期输出队看先手、爆发和保护窗口。")
    add_number(d, "再核算资源。把同名武将、两份伏兵、两份斩铁、两份落雷和迷阵，以及先驱、衡轭、反计等共享资源统一计数。")
    add_number(d, "然后检查条件。形兵看实际兵系，计险远近看基础攻击距离，追击看能否普攻，枭雄看主动战法限制，神赏看前期覆盖。")
    add_number(d, "最后比较替换代价。宁元刀换计险远近和疾战会改变连击、距离与控制功能，不能把替换方案与原配置同时计算。")
    add_heading(d, "四 可执行建议")
    add_number(d, "资源较少时先从用途明确的消耗队或恢复控制队试验，不因名次靠前就优先拆出稀缺战法。")
    add_number(d, "需要主力输出时，先锁定神兵天降、大赏三军、反计之策、先驱突击和形兵之极的全账号去向，再决定后四组是否值得投入。")
    add_number(d, "遇到速度更快或爆头队，重新检查前两回合保护和大营承伤。前期体系失去先手后，原有强度判断可能不成立。")
    add_heading(d, "五 AI独立判断")
    add_para(d, "前三组的价值主要是低成本承担特定任务，不宜与满兵主力用同一标准评价。低战损、拖平和换取敌方体力应分别记录。")
    add_para(d, "蜀智与宁元刀体现条件型联动：兵系、攻击距离、普攻和追击缺一项，纸面配置就可能失真。配队时应先验证条件，再讨论强度。")
    add_para(d, "最后两组集中占用前期核心战法。它们适合解释资源如何换取爆发窗口，但不能用被动输出或短期洞察推导整队长期免控。")
    add_heading(d, "六 适用边界")
    add_para(d, "本报告保留七组完整配置和已核实的替换线索，没有把展示战报换算成统一胜率。作者顺序只用于识别案例，不作为当前版本强度排名。")
    add_para(d, "正式应用时，以当前客户端、赛季、账号武将版本、战法数量和实际战报为准。七组案例用于学习资源分层与条件检查，不能直接拼成多队答案。")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    d.save(out)


def build_keep(out):
    d = new_report("低星武将留卡的用途与取舍")
    add_para(d, "这份报告把视频中的留卡建议整理为拆解前检查表。留卡价值来自账号仍需要的铺路、金币、体力、资源上限或战斗功能；题名中的“千万别拆”不是所有账号永久保留全部重复卡的规则。")
    add_heading(d, "报告索引")
    add_para(d, "关键词：低星留卡、铺路、金币政策、体力恢复、资源上限、战斗候选、版本核对、拆解取舍")
    add_para(d, "重点政策与版本线索：安定众心、奇功解围、长坂风威、颠沛太妃、祸乱是非；战斗卡用自带战法区分轻侠妄为、侵掠如火、沙场破阵、节镇关东与西乡武功等同名版本。")
    add_heading(d, "一 核心结论")
    add_bullet(d, "先锁定具体卡牌版本和政策，再判断账号是否缺少对应功能。姓名或星级不能代替版本识别。")
    add_bullet(d, "政策展示值受等级、任职设施、阵营和目标部队等条件影响。视频预览数值不能直接当作当前账号收益。")
    add_bullet(d, "保留候选可以避免以后重新获取，但已有稳定替代、部署名额紧张或政策岗位更稀缺时，追加保留价值会下降。")
    add_bullet(d, "战斗用途只提供成员线索。视频没有完整战法与统一战报，不能据此承诺这些队伍已经能够作为主力使用。")
    add_heading(d, "二 五类用途对比")
    rows = [
        ["铺路", "旗本八骑相关候选", "作者建议保留3至6张，组成1至2队", "称号成员、速度、攻击距离、兵力与部署名额", "已有足够铺路队或缺少称号成员"],
        ["金币", "蜀糜夫人、晋向秀、蜀马姬、群袁术", "作为金币内政候选", "具体版本、政策全文、任职和城建税收条件", "其他政策收益更高或税收条件不足"],
        ["体力", "蜀三相〔安定众心〕\n徐晃〔奇功解围〕\n张飞〔长坂风威〕", "缩短符合条件部队的体力恢复时间", "主城或军事设施任职、阵营、待命状态；张飞政策还降低设施耐久上限", "前线设施需要抗拆，或主力不满足目标条件"],
        ["资源上限", "杜氏〔颠沛太妃〕\n蔡夫人〔祸乱是非〕", "提高石料或四项资源储存上限", "目标建筑需求、当前上限、政策等级", "现有上限已满足目标，其他岗位收益更高"],
        ["战斗", "四星郭嘉、徐庶、甘宁、凌统、朱儁、刘伶、阮籍、嵇康", "作为低成本或特定体系候选", "版本、自带战法、完整战法供给和队伍任务", "缺少配套战法，或同名武将版本不符"],
    ]
    add_table(d, ["用途", "视频候选", "作者用途", "使用前检查", "降低优先级的条件"], rows, [0.62, 1.32, 1.25, 1.55, 1.26], 8.0, (0,))
    add_heading(d, "三 政策判断方法")
    add_number(d, "金币收益分开计算固定收益和依赖分城税收的收益，再代入账号城建、任职和政策等级。视频没有完整税收日志，不能保证每日固定收入。")
    add_number(d, "体力政策逐项核对设施、阵营和目标部队。恢复速度增加不等于恢复时间等比例减少；速度变为1.5倍时，同样体力所需时间约为原来的三分之二。")
    add_number(d, "张飞长坂风威适合集中待命恢复，但会降低设施耐久上限。前线位置使用时必须把抗拆风险计入收益。")
    add_number(d, "资源上限只增加容量，不直接生产资源。先算目标建筑的资源缺口，再决定是否占用政策位置。")
    add_heading(d, "四 战斗留卡线索")
    rows2 = [
        ["小魏骑", "四星郭嘉、荀彧、曹仁", "四星郭嘉与五星郭嘉不是同一战法效果，不能按姓名无损替换。"],
        ["宁元刀", "四星甘宁、卫瓘、四星徐庶", "先核对甘宁〔轻侠妄为〕、徐庶〔沙场破阵〕及完整战法数量。"],
        ["甘宁碰瓷", "甘宁、凌统、朱儁", "区分甘宁版本与朱儁〔节镇关东／西乡武功〕；按低投入损耗收益评价。"],
        ["竹林七贤", "刘伶、阮籍、嵇康", "成员可锁定四星版本，但视频未提供完整战法和足够战报。"],
    ]
    add_table(d, ["用途线索", "成员", "复用条件"], rows2, [1.0, 2.0, 3.0], 8.4, (0,))
    add_heading(d, "五 拆解前检查顺序")
    add_number(d, "用自带战法、SP或XP标志、阵营、兵种和星级锁定版本。存在多个合理版本时先保留，不凭同名猜测。")
    add_number(d, "检查是否为唯一有用副本，以及是否正在施政、战斗或预定队伍中使用。")
    add_number(d, "比较保留用途与拆解所得战法对全账号的价值，同时核对政策岗位、部署名额和替代卡。")
    add_number(d, "多队配置时统一计算学习战法数量和同名武将占用，最后再处理确实没有用途的重复卡。")
    add_heading(d, "六 AI独立判断")
    add_para(d, "留卡不是越多越安全。最有价值的是账号短缺功能的唯一候选，以及未来获取成本高、用途明确的版本；重复且已有替代的卡应降低优先级。")
    add_para(d, "政策卡和战斗卡应分开评价。内政价值由岗位与生效条件决定，战斗价值由完整队伍和战法供给决定，不能用一个用途证明另一用途。")
    add_para(d, "碰瓷队的目标是以较低投入换取对方损耗，不应与满兵主力按胜率单一比较。没有配套战法时，保留成员只代表保留未来选择。")
    add_heading(d, "七 适用边界")
    add_para(d, "原视频定点展示了金币候选、体力政策和资源上限政策，但没有为战斗队提供完整配置，也没有证明政策收益在所有等级和城建条件下相同。")
    add_para(d, "实际拆解前以当前账号卡牌版本、政策文本、岗位需求、战法数量和赛季可用性为准。本报告用于防止误拆，不替账号作一律保留的决定。")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    d.save(out)


def maybe_build(src, out):
    name = Path(src).name
    if name == MERGED_TITLE + "_逐帧深度学习报告_1秒版.docx":
        print("已并入官方机制库，不再生成独立报告")
        return True
    for title, builder in ((TITLE, build_shuzhi), (RANK_TITLE, build_rank), (KEEP_TITLE, build_keep)):
        if name == title + "_逐帧深度学习报告_1秒版.docx":
            builder(out)
            return True
    return False


def build_all(out_dir):
    out_dir = Path(out_dir)
    outputs = [
        out_dir / (TITLE + "_精修学习报告.docx"),
        out_dir / (RANK_TITLE + "_精修学习报告.docx"),
        out_dir / (KEEP_TITLE + "_精修学习报告.docx"),
    ]
    for builder, output in zip((build_shuzhi, build_rank, build_keep), outputs):
        builder(output)
        print(output)
    return outputs


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == "--all":
        build_all(sys.argv[2])
    elif len(sys.argv) == 2:
        build_shuzhi(sys.argv[1])
    else:
        raise SystemExit("usage: saiji_standalone_v2.py --all OUTPUT_DIR | OUTPUT_DOCX")
