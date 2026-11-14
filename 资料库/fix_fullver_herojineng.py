# -*- coding: utf-8 -*-
"""把 1秒版 帧级权威校正反哺 完整版（武将/战法名音译误识修复）。
   按视频定位，备份后做 docx run 级全文替换（遍历 paragraphs + tables）。"""
import sys, glob, os, json, shutil
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

REP = "D:/Desktop/shandou/学习汇报"
BACKUP = "D:/Desktop/shandou/学习汇报/_backup_before_errata/herojineng_20260809"
os.makedirs(BACKUP, exist_ok=True)

# keyword(唯一标识视频) -> {wrong: correct}
JOBS = {
    "贾诩": {  # 率土武将志—贾诩
        "重谋": "众谋不懈", "夹许": "众谋不懈", "三势": "三术奇谋", "河内": "河内世泽",
        "风生火烧": "风声鹤唳+火烧连营", "顶足": "鼎足江东", "当仰巧": "当阳桥",
        "壁瑞": "避锐治气", "鸟云山兵": "乌云山兵",
    },
    "体系篇": {  # 战磐体系
        "成立": "程昱", "几封讯类": "疾风迅雷",
    },
    "神赏体系粉丝投稿": {"Boss": "褒姒"},
    "垒实篇投稿讲解": {"重整": "重整旗鼓"},
    "攻其篇—粉丝投稿": {"操缠": "衡轭"},
    "垒实篇 评论抢点评": {"垒实迎虚": "垒实迎击", "唐童": "庞统"},
    "文鸯、程昱": {"豹文刀": "曹纯"},
    "高顺领衔群骑": {"机势": "击势", "胜负先征": "胜负先征"},  # 胜负先争->胜负先征
    "杜预也能走垒实": {"以逸待劳": "以诱待来"},
    "距离思路究极细节": {"奉移艇": "掎角之势"},
    "魏晋篇": {"极锋而适": "及锋而试"},
}

def resolve_base(kw):
    fs = glob.glob(REP + f"/*{kw}*_逐帧深度学习报告_1秒版.docx")
    if not fs:
        return None
    return os.path.basename(fs[0]).replace("_逐帧深度学习报告_1秒版.docx", "")

def replace_in_doc(doc, mp):
    counts = {}
    def do_runs(paras):
        for p in paras:
            for r in p.runs:
                for old, new in mp.items():
                    if old in r.text:
                        c = r.text.count(old)
                        r.text = r.text.replace(old, new)
                        counts[old] = counts.get(old, 0) + c
    do_runs(doc.paragraphs)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                do_runs(cell.paragraphs)
    return counts

log = []
for kw, mp in JOBS.items():
    base = resolve_base(kw)
    if not base:
        log.append(f"[跳过] 找不到含「{kw}」的 1秒版文件")
        continue
    full = os.path.join(REP, base + "_完整学习报告.docx")
    if not os.path.exists(full):
        log.append(f"[跳过] 完整版缺失: {base}")
        continue
    # 备份
    shutil.copy2(full, os.path.join(BACKUP, os.path.basename(full)))
    doc = Document(full)
    before = " | ".join(f"{k}→{v}" for k, v in mp.items())
    counts = replace_in_doc(doc, mp)
    doc.save(full)
    log.append(f"[修复] {base}\n   映射: {before}\n   实际替换: {counts if counts else '（0 处，完整版未出现该误识）'}")

print("\n".join(log))
json.dump(log, open("D:/Desktop/shandou/资料库/fix_fullver_hj_log.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n[完成] 备份目录: {BACKUP}")
print(f"[完成] 处理视频数: {len(JOBS)}  日志: fix_fullver_hj_log.json")
