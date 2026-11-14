# -*- coding: utf-8 -*-
"""
物理归置脚本（在完整备份完成后运行）。
方案（用户确认 2026-08-19）：
  1) 归档：项目内所有 _ 开头非活跃目录 -> 归档_备份_20260819/（保持相对层级）
  2) 报告库：三版报告按子项目收编 -> 报告库/<子项目>/{精编,完整版,逐帧1秒版}/
     - 精编来自 学习成果汇总/<子项目>/
     - 完整版/逐帧1秒版来自 学习汇报/ 顶层 + 学习汇报_海之呼唤/ + 学习汇报_赛季/
  3) 视频/静帧/转写 不动（已是按视频分组的干净输入源）
自检：D:/WorkBuddyData/shandou_backup_20260819 必须存在且非空，否则 abort。
"""
import os, shutil, sys

ROOT = "D:/Desktop/shandou"
ARCHIVE = os.path.join(ROOT, "归档_备份_20260819")
REPORT_LIB = os.path.join(ROOT, "报告库")
BACKUP = "D:/WorkBuddyData/shandou_backup_20260819"

LOG = []

def log(s):
    LOG.append(s)
    print(s)

def ensure(d):
    os.makedirs(d, exist_ok=True)

def classify(name):
    if "精编学习报告" in name: return "精编"
    if "完整学习报告" in name: return "完整版"
    if "逐帧深度学习报告_1秒版" in name: return "逐帧1秒版"
    return None

def safe_move(src, dst):
    if not os.path.exists(src):
        log(f"  [跳过-源已随父目录移动] {src}")
        return None
    ensure(os.path.dirname(dst))
    if os.path.exists(dst):
        base, ext = os.path.splitext(dst)
        dst = base + "_dup" + ext
    shutil.move(src, dst)
    return dst

# ---- 自检 ----
if not os.path.isdir(BACKUP) or len(os.listdir(BACKUP)) == 0:
    log("❌ 备份不存在或为空，abort。先跑备份。")
    sys.exit(1)
log("✅ 备份存在，开始归置")

# ---- 1) 归档所有 _ 目录 ----
log("\n=== 1) 归档 _ 目录 ===")
archive_dirs = []
for dp, dirs, _ in os.walk(ROOT):
    if "归档_备份" in dp or dp.replace("\\","/").endswith(".workbuddy"):
        continue
    for d in list(dirs):
        if d.startswith("_"):
            archive_dirs.append(os.path.join(dp, d))
log(f"发现 {len(archive_dirs)} 个 _ 目录待归档")
# 浅路径优先 + 剔除嵌套（父目录移动时子目录会跟着走）
archive_dirs.sort(key=lambda p: p.count(os.sep))
top_archive = []
for d in archive_dirs:
    if not any(d.startswith(t + os.sep) for t in top_archive):
        top_archive.append(d)
for src in top_archive:
    rel = os.path.relpath(src, ROOT)
    dst = os.path.join(ARCHIVE, rel)
    moved = safe_move(src, dst)
    if moved:
        log(f"  归档: {rel}  ->  {os.path.relpath(moved, ROOT)}")

# ---- 2) 报告库 ----
log("\n=== 2) 报告库归置 ===")

# 2a 精编 from 学习成果汇总/<子项目>/
sc = os.path.join(ROOT, "学习成果汇总")
if os.path.isdir(sc):
    for sub in os.listdir(sc):
        if sub.startswith("_"):
            continue
        fp = os.path.join(sc, sub)
        if not os.path.isdir(fp):
            continue
        for f in os.listdir(fp):
            if not f.endswith(".docx"):
                continue
            tgt_sub = "开荒" if "开荒" in f else sub
            dst = os.path.join(REPORT_LIB, tgt_sub, "精编", f)
            safe_move(os.path.join(fp, f), dst)
            log(f"  精编: {sub}/{f}  ->  {os.path.relpath(dst, ROOT)}")

# 2b 学习汇报/ 顶层 (完整版/逐帧1秒版/精编)
lh = os.path.join(ROOT, "学习汇报")
if os.path.isdir(lh):
    for f in os.listdir(lh):
        if not f.endswith(".docx"):
            continue
        cat = classify(f)
        if cat is None:
            log(f"  [跳过-未分类] 学习汇报/{f}")
            continue
        tgt_sub = "开荒" if "开荒" in f else "旧56项目"
        dst = os.path.join(REPORT_LIB, tgt_sub, cat, f)
        safe_move(os.path.join(lh, f), dst)
        log(f"  {cat}: 学习汇报/{f}  ->  {os.path.relpath(dst, ROOT)}")

# 2c 学习汇报_海之呼唤/ (逐帧1秒版)
for sub_src, sub_tgt in [("学习汇报_海之呼唤", "海之呼唤"), ("学习汇报_赛季", "赛季")]:
    sd = os.path.join(ROOT, sub_src)
    if not os.path.isdir(sd):
        continue
    for f in os.listdir(sd):
        if not f.endswith(".docx"):
            continue
        cat = classify(f) or "逐帧1秒版"
        dst = os.path.join(REPORT_LIB, sub_tgt, cat, f)
        safe_move(os.path.join(sd, f), dst)
        log(f"  {cat}: {sub_src}/{f}  ->  {os.path.relpath(dst, ROOT)}")

# ---- 汇总 ----
log("\n=== 归置完成 ===")
for dp, dirs, files in os.walk(REPORT_LIB):
    docs = [f for f in files if f.endswith(".docx")]
    if docs:
        log(f"  {os.path.relpath(dp, ROOT)}/ : {len(docs)} docx")
with open(os.path.join(ROOT, "资料库", "organize_log.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(LOG))
log("日志已写 资料库/organize_log.txt")
