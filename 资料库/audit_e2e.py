# -*- coding: utf-8 -*-
"""端到端复核 v1：视频 <-> 报告 <-> 转录 <-> 帧 四方对齐清点"""
import os, json, re, glob
from docx import Document

ROOT = r"D:\Desktop\shandou"
VID_DIRS = [os.path.join(ROOT, "抖音"), os.path.join(ROOT, "抖音", "开荒")]
REP = os.path.join(ROOT, "学习汇报")
TRANS = os.path.join(ROOT, "抖音_transcripts")
FR1S = os.path.join(ROOT, "抖音_frames_dense_1s")

def norm(s):
    # 标点/空格归一化用于模糊匹配
    t = s
    for a, b in [("！","!"),("？","?"),("，",","),("：",":"),("；",";"),
                 ("（","("),("）",")"),("、",","),("　"," "),("｜","|")]:
        t = t.replace(a, b)
    t = re.sub(r"\s+", "", t)
    return t

# 1) 源视频清单
videos = {}   # base -> 相对目录
for d in VID_DIRS:
    if not os.path.isdir(d):
        continue
    sub = "开荒" if d.endswith("开荒") else ""
    for f in os.listdir(d):
        if f.lower().endswith(".mp4"):
            videos[os.path.splitext(f)[0]] = sub

kaihuang = sorted([k for k, v in videos.items() if v == "开荒"])
solo = sorted([k for k, v in videos.items() if v == ""])

# 2) 报告清单
docs = [f for f in os.listdir(REP) if f.endswith(".docx") and not f.startswith("~$")]
r_full = [f for f in docs if f.endswith("_完整学习报告.docx")]
r_1s   = [f for f in docs if f.endswith("_逐帧深度学习报告_1秒版.docx")]
r_other= [f for f in docs if f not in r_full and f not in r_1s]

print("=" * 70)
print("【1】清点")
print(f"源视频: 总 {len(videos)}  (根目录 {len(solo)} + 开荒 {len(kaihuang)})")
print(f"报告 docx 总 {len(docs)}: 完整版 {len(r_full)} / 1秒版 {len(r_1s)} / 其它 {len(r_other)}")
for f in r_other:
    print(f"   其它: {f}")

# 3) 对应关系：每个 solo 视频应有 1 完整版 + 1 一秒版；开荒合并为 1 专题
def stem(f, suf):
    return f[: -len(suf)]

full_stems = {norm(stem(f, "_完整学习报告.docx")): f for f in r_full}
s1_stems   = {norm(stem(f, "_逐帧深度学习报告_1秒版.docx")): f for f in r_1s}

miss_full, miss_1s = [], []
for v in solo:
    nv = norm(v)
    if nv not in full_stems: miss_full.append(v)
    if nv not in s1_stems:   miss_1s.append(v)

print("\n【2】视频 -> 报告 覆盖")
print(f"缺完整版: {len(miss_full)}  {miss_full if miss_full else ''}")
print(f"缺1秒版 : {len(miss_1s)}  {miss_1s if miss_1s else ''}")

# 反向：报告有但视频没有
vset = {norm(v) for v in solo}
extra_full = [f for k, f in full_stems.items() if k not in vset]
extra_1s   = [f for k, f in s1_stems.items()   if k not in vset]
print(f"多出的完整版(无对应视频): {len(extra_full)}")
for f in extra_full: print(f"   {f}")
print(f"多出的1秒版(无对应视频): {len(extra_1s)}")
for f in extra_1s: print(f"   {f}")

# 4) 转录覆盖
tj = {norm(os.path.splitext(f)[0]): f for f in os.listdir(TRANS) if f.endswith(".json")}
print("\n【3】转录覆盖")
allv = solo + kaihuang
miss_t = [v for v in allv if norm(v) not in tj]
print(f"转录 json 数: {len(tj)} / 视频 {len(allv)}；缺转录: {len(miss_t)} {miss_t if miss_t else ''}")

# 5) 1s 帧目录覆盖
fr_dirs = set()
for d, subs, files in os.walk(FR1S):
    if any(f.endswith(".jpg") for f in files):
        fr_dirs.add(norm(os.path.basename(d)))
miss_f = [v for v in allv if norm(v) not in fr_dirs]
print(f"\n【4】1秒帧目录数: {len(fr_dirs)} / 视频 {len(allv)}；缺帧目录: {len(miss_f)} {miss_f if miss_f else ''}")

# 6) 报告体检：字数 / 图片数 / 段落数
print("\n【5】报告体检 (1秒版)")
rows = []
for f in sorted(r_1s):
    p = os.path.join(REP, f)
    try:
        d = Document(p)
    except Exception as e:
        rows.append((f, -1, -1, f"打开失败:{e}"))
        continue
    txt = "\n".join(par.text for par in d.paragraphs)
    nch = len(re.sub(r"\s", "", txt))
    nimg = len(d.inline_shapes)
    size = os.path.getsize(p) / 1024 / 1024
    rows.append((f, nch, nimg, f"{size:.1f}MB"))

rows.sort(key=lambda r: r[1])
print(f"{'字数':>7} {'图':>4} {'体积':>8}  文件")
for f, nch, nimg, sz in rows:
    flag = ""
    if nch < 2000: flag = "  <-- 字数偏少"
    if nimg < 5:   flag += "  <-- 插图偏少"
    print(f"{nch:>7} {nimg:>4} {sz:>8}  {f[:44]}{flag}")

tot_ch = sum(r[1] for r in rows if r[1] > 0)
tot_img = sum(r[2] for r in rows if r[2] > 0)
print(f"\n合计：字数 {tot_ch}，插图 {tot_img}，报告 {len(rows)} 份")

out = {
    "videos": len(videos), "solo": len(solo), "kaihuang": len(kaihuang),
    "docx_total": len(docs), "full": len(r_full), "s1": len(r_1s), "other": r_other,
    "miss_full": miss_full, "miss_1s": miss_1s,
    "extra_full": extra_full, "extra_1s": extra_1s,
    "miss_transcript": miss_t, "miss_frames": miss_f,
    "report_stats": [{"file": r[0], "chars": r[1], "imgs": r[2], "size": r[3]} for r in rows],
    "total_chars": tot_ch, "total_imgs": tot_img,
}
with open(os.path.join(ROOT, "资料库", "audit_e2e.json"), "w", encoding="utf-8") as fp:
    json.dump(out, fp, ensure_ascii=False, indent=2)
print("\n已写出 资料库/audit_e2e.json")
