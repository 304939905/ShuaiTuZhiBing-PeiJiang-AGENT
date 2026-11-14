# -*- coding: utf-8 -*-
"""全量抽取 学习汇报/ 下全部 docx（1秒版+完整版+开荒双版）的可核对断言。
分类：MATCHUP(对战结论) / SEASON(剧本赛季机制) / MECH(具体机制) / NUMERIC(数值事实) / GEAR(宝物) / HERO(武将)。
输出到 step_all_claims.txt，供离线 parity 与在线核验两路消费。
"""
import os, re, glob, json
import docx

REP_DIR = "D:/Desktop/shandou/学习汇报"
OUT = "D:/Desktop/shandou/资料库/step_all_claims.txt"

MATCHUP = re.compile(r"(克制|被克|打过|打不过|打不赢|能打|打不了|碾压|吊打|稳赢|稳吃|天敌|专克|怕.{0,4}队|遇到.{0,6}队|对阵|单挑|胜率|五五开|优势|劣势|打满|翻车|吃.{0,3}队|被.{0,3}队吃)")
SEASON  = re.compile(r"(征服赛季|S赛季|X赛季|赛季奖励|土地.{0,4}名额|州府|宝物系统|兵种特性|内政.{0,4}(点|系统)|战法距离|赛季机制|开荒.{0,4}(机制|规则|玩法)|名额|霸业|割据|洛阳|流浪军|资源州|剧本|南中之战|兵合|群雄|铁城|兴平|太监|穿越|潼关|凉州|赤壁|官渡|结义|涿鹿|两汉|八阵|应天|社稷|山河|风卷|甲子)")
MECH    = re.compile(r"(机制|结算|玩法|规则|触发条件|生效条件|每回合|首回合|第二回合|前.{0,2}回合|满级效果|基础效果|递增|叠加规则|距离思路|COST|兵力|普攻|指挥.{0,3}战法|被动战法|主动战法|追击战法|突击战法|阵法战法)")
NUMERIC = re.compile(r"(发动率|发动概率|触发率|触发概率|品质[:：为是]?[SABC级]|[SABC]级|距离[为是]?[1-8]|宝物品质|品质[:：]?\s*(稀世|精品|良才|普通|极|寻常|神|珍|凡)|六韬|武略|天资|骁锐|筹算|英勇|天枪|机敏|坚韧|坚忍|规避|强韧|陷阵|无畏|迸发|无妄|选锋|骁锐|游飘|元戎|大将|博浪|彤素|别鸣|沧海|星汉|大橹|大柯斧|两仪刀|比翼|及锋而试|九锡黄龙|正始之变|百战无怯|一骑当千)")
GEAR    = re.compile(r"(宝物|博浪|大将|元戎|彤素|游飘|星汉|大橹|大柯斧|两仪刀|比翼|别鸣|沧海|及锋而试|九锡黄龙|正始之变|百战无怯|一骑当千|骁锐|筹算|英勇|天资|机敏|坚韧|坚忍|规避|强韧|陷阵|无畏|迸发|无妄|选锋)")
HERO    = re.compile(r"(武将|马岱|孟获|甘宁|高顺|程昱|孙权|张机|刘备|曹操|赵云|吕布|司马懿|周瑜|陆逊|诸葛亮|关羽|张飞|黄忠|魏延|姜维|sp|SP|甄洛|严颜|杜预|徐庶|周泰|张鲁|木鹿|张角|董卓|袁绍|公孙瓒|孙尚香|大乔|小乔|貂蝉|华佗|黄月英|荀彧|郭嘉|贾诩|李儒|陈宫|吕蒙|孙坚|太史慈|甘宁|凌统|吕玲绮|张春华|王异|sp赵云|sp马超|sp关羽|sp庞德|sp张飞|sp朱儁|sp姜维)")

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
    raw = re.split(r'[。！？\n；;]', text)
    return [s.strip() for s in raw if len(s.strip()) >= 6]

files = sorted(glob.glob(os.path.join(REP_DIR, "*.docx")))
files = [f for f in files if "_backup" not in f]

cats = {"MATCHUP": MATCHUP, "SEASON": SEASON, "MECH": MECH, "NUMERIC": NUMERIC, "GEAR": GEAR, "HERO": HERO}
per_file = {}
stats = {c: 0 for c in cats}
for f in files:
    name = os.path.basename(f)
    try:
        txt = "\n".join(text_of(f))
    except Exception as e:
        print("ERR", name, e); continue
    sents = sents_of(txt)
    hits = []
    for s in sents:
        matched = [c for c in cats if cats[c].search(s)]
        if matched:
            hits.append((matched, s))
            for c in matched: stats[c] += 1
    per_file[name] = hits

with open(OUT, "w", encoding="utf-8") as fo:
    fo.write("# 全量可核对断言抽取（%d 文件）\n" % len(files))
    fo.write("# 分类计数: " + ", ".join("%s=%d"%(c,stats[c]) for c in cats) + "\n\n")
    for name, hits in per_file.items():
        fo.write("\n### FILE: %s  (%d)\n" % (name, len(hits)))
        for matched, s in hits:
            fo.write("  [%s] %s\n" % ("/".join(matched), s))

print("files:", len(files))
print("stats:", json.dumps(stats, ensure_ascii=False))
print("written:", OUT)
