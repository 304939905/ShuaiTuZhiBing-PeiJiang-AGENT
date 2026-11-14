import sys, os, json
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

GREY = RGBColor(0x66, 0x66, 0x66)

def rgb_grey():
    return GREY

def H(doc, text, level):
    doc.add_heading(text, level=level)

def meta_line(doc, label, value):
    if value is None:
        return
    p = doc.add_paragraph()
    r = p.add_run(f"{label}：")
    r.bold = True
    r.font.size = Pt(10)
    r2 = p.add_run(str(value))
    r2.font.size = Pt(10)

def add_page_number_and_header(section, title, vid):
    # 页眉
    hp = section.header.paragraphs[0]
    hr = hp.add_run(f"{title}  ·  {vid}")
    hr.font.size = Pt(8)
    hr.font.color.rgb = GREY
    # 页脚页码
    fp = section.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fp.add_run()
    f1 = OxmlElement('w:fldChar'); f1.set(qn('w:fldCharType'), 'begin')
    it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = 'PAGE'
    f2 = OxmlElement('w:fldChar'); f2.set(qn('w:fldCharType'), 'end')
    run._r.append(f1); run._r.append(it); run._r.append(f2)
    run.font.size = Pt(8)
    run.font.color.rgb = GREY

def insert_screenshot(doc, shot, shots_by_id):
    sid = shot.get("shot") if isinstance(shot, dict) else shot
    s = shots_by_id.get(sid)
    if not s:
        return
    path = s.get("path")
    if path and os.path.exists(path):
        doc.add_picture(path, width=Inches(5.6))
        cap = doc.add_paragraph()
        r = cap.add_run(f"[{s.get('time','')}] {s.get('caption','')}")
        r.italic = True
        r.font.size = Pt(8.5)
        r.font.color.rgb = GREY
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER

def build(out_path, d):
    doc = Document()
    st = doc.styles['Normal']
    st.font.name = 'Microsoft YaHei'
    st.font.size = Pt(10.5)

    title = d.get('video_title', '学习报告')
    vid = d.get('video_id', '')
    section = doc.sections[0]
    add_page_number_and_header(section, title, vid)

    # 封面
    doc.add_heading(title, level=0)
    meta_line(doc, "视频编号", vid)
    meta_line(doc, "精确时长", d.get('duration'))
    meta_line(doc, "分辨率", d.get('resolution'))
    meta_line(doc, "字幕轨", "有独立字幕轨" if d.get('has_subtitle_stream') else "无独立字幕轨（字幕为画面硬字幕）")
    meta_line(doc, "音频转写", "已完整转写（faster-whisper）" if d.get('audio_transcribed') else "未转写")
    meta_line(doc, "报告日期", d.get('report_date'))
    meta_line(doc, "学习范围", d.get('scope'))
    doc.add_page_break()

    # 1 结论摘要
    H(doc, "一、结论摘要", 1)
    sm = d.get('summary', {})
    if sm.get('what_it_teaches'):
        p = doc.add_paragraph()
        p.add_run("本视频真正讲了什么：").bold = True
        p.add_run(sm['what_it_teaches'])
    if sm.get('core_conclusions'):
        doc.add_paragraph("核心结论（3~6条）：")
        for c in sm['core_conclusions']:
            doc.add_paragraph(c, style='List Number')
    if sm.get('not_concluded'):
        doc.add_paragraph("不适合从本视频得出的结论：")
        for c in sm['not_concluded']:
            doc.add_paragraph(c, style='List Bullet')

    # 2 内容范围
    H(doc, "二、视频内容范围", 1)
    cs = d.get('content_scope', {})
    for label, key in [("正式讲解", "formal"), ("简单提及", "mentioned"),
                       ("系列预告/后续选题", "preview"), ("未讲内容", "not_covered")]:
        items = cs.get(key)
        if items:
            doc.add_paragraph(label + "：")
            for x in items:
                doc.add_paragraph(x, style='List Bullet')

    # 3 核心知识详解
    H(doc, "三、核心知识详解", 1)
    shots_by_id = {s.get('id'): s for s in d.get('screenshots', [])}
    for sec in d.get('knowledge', []):
        H(doc, sec.get('topic', '主题'), 2)
        for pt in sec.get('points', []):
            extra = ""
            if pt.get('time'):
                extra += f" [时间点 {pt['time']}]"
            if pt.get('evidence'):
                extra += f" 证据:{pt['evidence']}"
            if pt.get('confidence'):
                extra += f" 可信度:{pt['confidence']}"
            p = doc.add_paragraph(style='List Bullet')
            p.add_run(pt.get('text', ''))
            if extra:
                r = p.add_run(extra)
                r.italic = True
                r.font.size = Pt(8.5)
                r.font.color.rgb = GREY
            if pt.get('shot'):
                insert_screenshot(doc, pt['shot'], shots_by_id)

    # 4 案例分析
    H(doc, "四、视频案例分析", 1)
    for c in d.get('cases', []):
        p = doc.add_paragraph()
        p.add_run(c.get('title', '案例')).bold = True
        if c.get('time'):
            p.add_run(f" [时间点 {c['time']}]").italic = True
        if c.get('proves'):
            doc.add_paragraph("该案例证明了：" + c['proves'])
        if c.get('not_prove'):
            doc.add_paragraph("该案例不能证明：" + c['not_prove'])

    # 5 可执行方法
    H(doc, "五、可执行方法", 1)
    for a in d.get('actionable', []):
        p = doc.add_paragraph(style='List Number')
        p.add_run(a.get('step', ''))
        if a.get('detail'):
            doc.add_paragraph(a['detail'])

    # 6 常见误区
    H(doc, "六、常见误区", 1)
    for x in d.get('pitfalls', []):
        doc.add_paragraph(x, style='List Bullet')

    # 7 查不到
    H(doc, "七、查不到或无法确认的内容", 1)
    for x in d.get('unknown', []):
        doc.add_paragraph(x, style='List Bullet')

    # 8 证据索引
    H(doc, "八、来源与证据索引", 1)
    ei = d.get('evidence_index', [])
    if ei:
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Light Grid Accent 1'
        hdr = table.rows[0].cells
        for i, h in enumerate(["结论", "时间点", "截图编号", "可信度"]):
            hdr[i].text = h
            hdr[i].paragraphs[0].runs[0].bold = True
        for e in ei:
            row = table.add_row().cells
            row[0].text = e.get('conclusion', '')
            row[1].text = e.get('time', '')
            row[2].text = e.get('screenshot', '')
            row[3].text = e.get('confidence', '')
    else:
        doc.add_paragraph("（本报告暂无独立证据索引条目）")

    # 9 截图汇总
    H(doc, "九、截图（按时间点）", 1)
    for s in d.get('screenshots', []):
        path = s.get('path')
        if path and os.path.exists(path):
            doc.add_picture(path, width=Inches(5.6))
            cap = doc.add_paragraph()
            r = cap.add_run(f"[{s.get('time', '')}] {s.get('id', '')}：{s.get('caption', '')}")
            r.italic = True
            r.font.size = Pt(8.5)
            r.font.color.rgb = GREY
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.save(out_path)
    print("REPORT_SAVED", out_path)

if __name__ == '__main__':
    out = sys.argv[1]
    js = sys.argv[2]
    with open(js, 'r', encoding='utf-8') as f:
        data = json.load(f)
    build(out, data)
