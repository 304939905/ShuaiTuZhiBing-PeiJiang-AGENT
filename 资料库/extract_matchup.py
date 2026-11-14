# -*- coding: utf-8 -*-
"""抽取 51 份 1秒版报告中的「对战结果/赛季机制」类可证伪硬断言，按可核密度排序选报告。"""
import os, re, glob, json
import docx

REP_DIR = "D:/Desktop/shandou/学习汇报"
OUT = "D:/Desktop/shandou/资料库/step5_matchup_candidates.txt"

# 关键词分类
MATCHUP = re.compile(r"(克制|被克|打过|打不过|打不赢|能打|打不了|碾压|吊打|稳赢|稳吃|天敌|怕\s*[\u4e00-\u9fa5]|劣势|优势|胜率|五五开|单挑|对阵|碰见|遇到.{0,6}队|专克|怕.{0,4}队)")
SEASON  = re.compile(r"(征服赛季|S赛季|X赛季|赛季奖励|土地.{0,4}名额|州府|宝物|兵种特性|内政.{0,4}(点|系统)|战法距离|赛季机制|开荒.{0,4}(机制|规则|玩法)|名额|霸业|割据|洛阳)")
MECH    = re.compile(r"(机制|结算|玩法|规则|触发条件|生效条件|每回合|首回合|第二回合|前.{0,2}回合|满级效果|基础效果|递增|叠加规则|距离思路|COST)")

def text_of(p):
    d = docx.Document(p); out = []
    for para in d.paragraphs:
        if para.text.strip(): out.append(para.text)
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                if c.text.strip(): out.append(c.text)
    return out

def sents_of(text):
    # 以中英文句号/换行切句，保留较长句
    raw = re.split(r'[。！？\n；;]', text)
    return [s.strip() for s in raw if len(s.strip()) >= 6]

files = sorted(glob.glob(os.path.join(REP_DIR, "*_逐帧深度学习报告_1秒版.docx")))
# 排除已备份目录
files = [f for f in files if "_backup" not in f]

stats = {}
per_file = {}
for f in files:
    name = os.path.basename(f)
    try:
        txt = "\n".join(text_of(f))
    except Exception as e:
        print("ERR", name, e); continue
    sents = sents_of(txt)
    hits = []
    for s in sents:
        if MATCHUP.search(s) or SEASON.search(s) or MECH.search(s):
            # 排除纯问句/纯引用音频转写标记
            if s.startswith("图") or "？" in s[-3:]: 
                pass
            hits.append(s)
    per_file[name] = hits
    stats[name] = len(hits)

# 排序
ranked = sorted(stats.items(), key=lambda x: -x[1])
with open(OUT, "w", encoding="utf-8") as fo:
    fo.write("# Step5 对战/赛季机制 硬断言候选（按可核密度排序）\n")
    fo.write("# 总数文件: %d\n\n" % len(files))
    for i,(name,cnt) in enumerate(ranked,1):
        fo.write("[%d] %s  => %d 候选\n" % (i, name, cnt))
    fo.write("\n\n===== 明细 =====\n\n")
    for name, hits in per_file.items():
        fo.write("\n### FILE: %s  (%d)\n" % (name, len(hits)))
        for h in hits:
            tag = []
            if MATCHUP.search(h): tag.append("MATCHUP")
            if SEASON.search(h): tag.append("SEASON")
            if MECH.search(h): tag.append("MECH")
            fo.write("  [%s] %s\n" % ("/".join(tag), h))

print("files:", len(files))
print("TOP15:")
for i,(name,cnt) in enumerate(ranked[:15],1):
    print("  %2d. %4d  %s" % (i, cnt, name[:50]))
print("written:", OUT)
