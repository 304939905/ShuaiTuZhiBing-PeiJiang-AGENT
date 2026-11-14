# -*- coding: utf-8 -*-
import os, re, json

ROOT = "D:/Desktop/shandou"
OUT = "D:/Desktop/shandou/资料库/inventory_report.txt"

def human(n):
    for unit in ["B","KB","MB","GB","TB"]:
        if n < 1024: return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"

def dir_size(path):
    tot = 0; cnt = 0
    for dp, _, fns in os.walk(path):
        for fn in fns:
            try:
                fp = os.path.join(dp, fn)
                tot += os.path.getsize(fp); cnt += 1
            except OSError:
                pass
    return tot, cnt

def list_top(dirp):
    out = []
    try:
        for name in sorted(os.listdir(dirp)):
            fp = os.path.join(dirp, name)
            if os.path.isdir(fp):
                sz, cnt = dir_size(fp)
                out.append(("DIR", name, cnt, sz))
            else:
                out.append(("FILE", name, 1, os.path.getsize(fp)))
    except FileNotFoundError:
        pass
    return out

def frame_dirs():
    base = os.path.join(ROOT, "抖音_frames_dense_1s")
    res = {}
    for name in sorted(os.listdir(base)):
        fp = os.path.join(base, name)
        if os.path.isdir(fp) and name != "contact_sheets":
            cnt = sum(1 for f in os.listdir(fp) if f.lower().endswith(".jpg"))
            res[name] = cnt
    return res

def classify_docx(name):
    if "精编学习报告" in name: return "精编"
    if "完整学习报告" in name: return "完整版"
    if "逐帧深度学习报告_1秒版" in name: return "逐帧1秒版"
    return "其他"

lines = []
def w(s=""): lines.append(s)

w("=" * 70)
w("率土之滨项目 物理归置前 INVENTORY 快照")
w("生成时间基准: 2026-08-19")
w("=" * 70)

# 1. 顶层
w("\n【1】顶层目录/文件 (ROOT = D:/Desktop/shandou)")
w(f"{'类型':<5}{'名称':<40}{'文件数':>8}{'体积':>12}")
for typ, name, cnt, sz in list_top(ROOT):
    w(f"{typ:<5}{name:<40}{cnt:>8}{human(sz):>12}")

# 2. 抖音视频 已学/未学
w("\n【2】抖音/ 视频 已学 vs 未学 (已学=抖音_frames_dense_1s 有同名帧目录)")
frames = frame_dirs()
mp4s = [f for f in os.listdir(os.path.join(ROOT,"抖音")) if f.lower().endswith(".mp4")] if os.path.isdir(os.path.join(ROOT,"抖音")) else []
# 帧目录可能带 _top_0_N 截断/或开荒子目录；用核心名粗略匹配
def core(s):
    s = re.sub(r"_top_\d+_\d+.*$","",s)
    return re.sub(r"\.(mp4|json)$","",s)
learned = []; unlearned = []
for m in sorted(mp4s):
    cm = core(m)
    hit = any(core(fd)==cm for fd in frames) or cm in [core(x) for x in frames]
    (learned if hit else unlearned).append(m)
w(f"视频总数: {len(mp4s)}  已学(有帧目录): {len(learned)}  未学: {len(unlearned)}")
w("--- 未学视频清单 ---")
for m in unlearned: w(f"  {m}")
w("--- 已学视频(前20) ---")
for m in learned[:20]: w(f"  {m}")
if len(learned)>20: w(f"  ... 共 {len(learned)} 个")

# 3. 帧目录
w("\n【3】抖音_frames_dense_1s/ 帧目录 (不含 contact_sheets)")
w(f"帧目录总数: {len(frames)}  帧总数: {sum(frames.values())}")
fsz, fcnt = dir_size(os.path.join(ROOT,"抖音_frames_dense_1s"))
w(f"总体积: {human(fsz)}  总文件数: {fcnt}")
# 开荒子目录
kh = os.path.join(ROOT,"抖音_frames_dense_1s","开荒")
if os.path.isdir(kh):
    sub = [d for d in os.listdir(kh) if os.path.isdir(os.path.join(kh,d))]
    w(f"开荒子目录: {len(sub)} 个 -> {sub}")

# 4. 学习成果汇总
w("\n【4】学习成果汇总/ 子项目")
sc = os.path.join(ROOT,"学习成果汇总")
for name in sorted(os.listdir(sc)):
    fp = os.path.join(sc,name)
    if os.path.isdir(fp):
        docs = [f for f in os.listdir(fp) if f.lower().endswith(".docx")]
        cats = {}
        for d in docs:
            cats[classify_docx(d)] = cats.get(classify_docx(d),0)+1
        w(f"  {name}/ : {len(docs)} docx  {cats}")

# 5. 学习汇报 + 学习汇报_*
w("\n【5】学习汇报/ 与 学习汇报_*/ 报告分类")
report_dirs = [os.path.join(ROOT,"学习汇报")]
report_dirs += [os.path.join(ROOT,d) for d in os.listdir(ROOT) if d.startswith("学习汇报_") and os.path.isdir(os.path.join(ROOT,d))]
for rd in report_dirs:
    name = os.path.basename(rd)
    w(f"\n  >>> {name}/")
    cats = {}
    for f in sorted(os.listdir(rd)):
        fp = os.path.join(rd,f)
        if os.path.isdir(fp):
            w(f"      [子目录] {f}/  (文件 {len(os.listdir(fp))}个)")
        elif f.lower().endswith(".docx"):
            c = classify_docx(f)
            cats[c] = cats.get(c,0)+1
    w(f"      docx分类: {cats}")

# 6. 备份目录
w("\n【6】所有 _ 开头备份/临时目录")
for dp, dirs, _ in os.walk(ROOT):
    for d in dirs:
        if d.startswith("_"):
            fp = os.path.join(dp,d)
            sz, cnt = dir_size(fp)
            w(f"  {fp}  ({cnt}文件, {human(sz)})")

# 7. 转写
w("\n【7】抖音_transcripts/ 文件")
td = os.path.join(ROOT,"抖音_transcripts")
if os.path.isdir(td):
    jsons = [f for f in os.listdir(td) if f.endswith(".json")]
    wavs = [f for f in os.listdir(td) if f.endswith(".wav")]
    subdirs = [d for d in os.listdir(td) if os.path.isdir(os.path.join(td,d))]
    w(f"  json: {len(jsons)}  wav: {len(wavs)}  子目录: {subdirs}")

# 8. D盘空间
w("\n【8】D盘剩余空间")
try:
    import shutil
    total, used, free = shutil.disk_usage("D:/")
    w(f"  total={human(total)} used={human(used)} free={human(free)}")
except Exception as e:
    w(f"  (获取失败: {e})")

w("\n" + "=" * 70)
w("INVENTORY 结束")
w("=" * 70)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\n".join(lines))
