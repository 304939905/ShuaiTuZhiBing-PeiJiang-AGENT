import os, glob, sys
from docx import Document

OUT = "D:/Desktop/shandou/学习汇报"

SECTION_MARKERS = ["一、结论摘要","二、视频内容范围","三、核心知识详解","四、视频案例分析",
                   "五、可执行方法","六、常见误区","七、查不到或无法确认","八、来源与证据索引","九、截图"]

def qc(path):
    doc = Document(path)
    paras = doc.paragraphs
    headings = [p.text for p in paras if p.style.name.startswith('Heading')]
    text_len = sum(len(p.text) for p in paras)
    # count inline images
    img = 0
    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            img += 1
    missing = [m for m in SECTION_MARKERS if not any(m in h for h in headings)]
    size = os.path.getsize(path)
    problems = []
    if text_len < 300: problems.append("文本过短")
    if missing: problems.append("缺章节:" + ",".join(missing))
    if img == 0: problems.append("无插图")
    if size < 20000: problems.append("文件过小")
    return dict(name=os.path.basename(path), size=size, text_len=text_len,
                n_headings=len(headings), images=img, missing=missing, problems=problems)

def main():
    paths = sorted(glob.glob(os.path.join(OUT, "*_完整学习报告.docx")))
    print("FOUND_DOCX", len(paths))
    bad = 0
    for p in paths:
        r = qc(p)
        flag = "OK" if not r['problems'] else "BAD"
        if r['problems']: bad += 1
        print(f"[{flag}] {r['name']} | size={r['size']} text={r['text_len']} head={r['n_headings']} img={r['images']} {r['problems']}")
    print("SUMMARY bad=", bad, "of", len(paths))

if __name__ == '__main__':
    main()
