# -*- coding: utf-8 -*-
"""抽检若干 docx：用 LibreOffice 转 PDF 并输出前几页 PNG，确认非空白。"""
import os, sys, glob, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_docx import convert_docx_to_pdf
try:
    import pymupdf as fitz
except ImportError:
    import fitz

REP = r"D:\Desktop\shandou\学习汇报"
OUT = r"D:\Desktop\shandou\资料库\_spotcheck"
os.makedirs(OUT, exist_ok=True)

targets = sys.argv[1:]
if not targets:
    allf = sorted(glob.glob(os.path.join(REP, "*_逐帧深度学习报告_1秒版.docx")))
    random.seed(20260809)
    targets = random.sample(allf, 3)

for i, dx in enumerate(targets, 1):
    name = os.path.basename(dx)
    pdf = os.path.join(OUT, "chk_%d.pdf" % i)
    try:
        convert_docx_to_pdf(dx, pdf)
        d = fitz.open(pdf)
        npg = d.page_count
        # 检查文字量与图片量
        txt = 0
        imgs = 0
        for pi in range(min(npg, 30)):
            pg = d[pi]
            txt += len(pg.get_text().strip())
            imgs += len(pg.get_images(full=True))
        # 导出第 1 页和第 5 页
        for pi in (0, min(4, npg - 1)):
            pix = d[pi].get_pixmap(dpi=90)
            pix.save(os.path.join(OUT, "chk_%d_p%d.png" % (i, pi + 1)))
        d.close()
        print("OK   %-55s 页数=%3d 前30页文字=%6d 图=%3d" % (name[:55], npg, txt, imgs))
    except Exception as e:
        print("FAIL %-55s %s: %s" % (name[:55], type(e).__name__, e))
