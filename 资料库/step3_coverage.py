# -*- coding: utf-8 -*-
"""Step3：低密度报告覆盖度抽样审计。
1) 用 video_meta.json 的真实时长计算 字/秒 密度，对 51 份一秒版排名。
2) 取密度最低 8 份，做覆盖度抽样：提取报告内时间戳引用，看是否跨越整段视频
   （若最大引用时间 << 视频时长，提示尾部内容可能遗漏）。
"""
import docx, os, re, json, glob

REPORT_DIR = r"D:\Desktop\shandou\学习汇报"
META = r"D:\Desktop\shandou\资料库\video_meta.json"
OUT = r"D:\Desktop\shandou\资料库\step3_coverage.txt"

TS = re.compile(r"(\d{1,2})[:：](\d{2})")  # MM:SS or HH:MM

def text_of(path):
    d = docx.Document(path)
    out = []
    for p in d.paragraphs:
        if p.text.strip(): out.append(p.text)
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                if c.text.strip(): out.append(c.text)
    return out

def char_count(texts):
    return sum(len(t.replace(" ", "").replace("\u3000", "")) for t in texts)

def max_ts(texts):
    mx = 0
    for t in texts:
        for mm, ss in TS.findall(t):
            s = int(mm) * 60 + int(ss)
            if s > mx: mx = s
    return mx

def main():
    meta = json.load(open(META, encoding="utf-8"))["videos"]
    dur = {}
    for v in meta:
        base = v["file"].replace(".mp4", "")
        dur[base] = v["duration_s"]
    files = sorted(glob.glob(os.path.join(REPORT_DIR, "*_1秒版.docx")))
    rows = []
    for fp in files:
        name = os.path.basename(fp)
        base = name.replace("_逐帧深度学习报告_1秒版.docx", "")
        texts = text_of(fp)
        ch = char_count(texts)
        d = dur.get(base)
        density = (ch / d) if d else None
        rows.append({"name": name, "base": base, "chars": ch, "dur": d,
                     "density": density, "max_ts": max_ts(texts)})
    # rank by density (only those with dur)
    ranked = [r for r in rows if r["density"] is not None]
    ranked.sort(key=lambda r: r["density"])
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("# Step3 密度排名（字/秒，升序）\n")
        f.write(f"{'密度':>7} {'字数':>7} {'时长s':>7} {'最大引用s':>8} {'覆盖%':>6}  文件\n")
        for r in ranked:
            cov = (r["max_ts"] / r["dur"] * 100) if r["dur"] else 0
            f.write(f"{r['density']:7.1f} {r['chars']:7d} {r['dur']:7.1f} {r['max_ts']:8d} {cov:6.0f}  {r['name']}\n")
        f.write("\n# 密度最低 8 份（覆盖度抽样）\n")
        for r in ranked[:8]:
            cov = (r["max_ts"] / r["dur"] * 100) if r["dur"] else 0
            flag = " [!尾部可能遗漏]" if cov < 70 else ""
            f.write(f"\n- {r['name']}\n  密度={r['density']:.1f} 字/秒 | 时长={r['dur']:.0f}s | 最大引用={r['max_ts']}s | 时间覆盖={cov:.0f}%{flag}\n")
    print("done ->", OUT)
    print("bottom8 densities:", [round(r['density'],1) for r in ranked[:8]])

if __name__ == "__main__":
    main()
