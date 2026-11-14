import sys, os, json
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def add_meta(doc, meta):
    if not meta:
        return
    p = doc.add_paragraph()
    if isinstance(meta, dict):
        text = "\n".join(f"{k}：{v}" for k, v in meta.items())
    else:
        text = str(meta)
    r = p.add_run(text)
    r.italic = True
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

def add_images(doc, images, captions=None):
    if not images:
        return
    # 新结构：images 是 [{path, caption}] 对象列表
    if isinstance(images[0], dict):
        for im in images:
            path = im.get('path') or im.get('image')
            cap = im.get('caption')
            if path and os.path.exists(path):
                doc.add_picture(path, width=Inches(5.8))
                if cap:
                    cp = doc.add_paragraph()
                    cr = cp.add_run(cap)
                    cr.italic = True
                    cr.font.size = Pt(8.5)
                    cr.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
                    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        # 旧结构：images 是路径字符串列表，captions 对应
        for img, cap in zip(images, (captions or [])):
            if img and os.path.exists(img):
                doc.add_picture(img, width=Inches(5.8))
                if cap:
                    cp = doc.add_paragraph()
                    cr = cp.add_run(cap)
                    cr.italic = True
                    cr.font.size = Pt(8.5)
                    cr.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
                    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER

def build(out_path, data):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Microsoft YaHei'
    style.font.size = Pt(10.5)

    doc.add_heading(data.get('title', '学习汇报'), level=0)
    add_meta(doc, data.get('meta'))

    if data.get('summary'):
        doc.add_heading('一、视频简介', level=1)
        doc.add_paragraph(data['summary'])

    for i, sec in enumerate(data.get('sections', []), start=2):
        h = sec.get('heading') or sec.get('h') or f'章节{i-1}'
        lvl = sec.get('level', 1)
        doc.add_heading(h, level=lvl)
        for para in sec.get('paragraphs', []):
            doc.add_paragraph(para)
        for it in sec.get('items', sec.get('bullet_points', [])):
            doc.add_paragraph(it, style='List Bullet')
        add_images(doc, sec.get('images', []), sec.get('captions'))

    unk = data.get('unknown') or data.get('unknowns')
    if unk:
        doc.add_heading('待补充 / 查不到', level=1)
        for u in unk:
            doc.add_paragraph(u, style='List Bullet')

    doc.save(out_path)

if __name__ == '__main__':
    out = sys.argv[1]
    js = sys.argv[2]
    with open(js, 'r', encoding='utf-8') as f:
        data = json.load(f)
    build(out, data)
    print("DOC_SAVED", out)
