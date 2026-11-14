# -*- coding: utf-8 -*-
"""断言型名称扫描器（高信噪比）。
核心区分：
  引用型 —— 「既有报告写作「壁瑞」」「音频转写为「夹许」」→ 错名是被引用的，合法，跳过。
  断言型 —— 「实为「磐阵擅守」」「逐帧确认为「击势」」「画面显示为「X」」→ 修正结论本身，
            必须落在官方白名单内，否则是高危错误（把错的改成另一个错的）。
输出 red-list：断言型 token 不在 武将/战法/宝物 官方白名单中的全部命中。
用法: python scan_assert.py [full|1s|both]
"""
import sys, glob, re, os, json
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

BASE = "D:/Desktop/shandou/资料库"
REP = "D:/Desktop/shandou/学习汇报"
ONLY = sys.argv[1] if len(sys.argv) > 1 else "both"

hero = set(json.load(open(BASE + "/official_hero_names.json", encoding="utf-8"))["names"])
jin = set(json.load(open(BASE + "/official_jineng_names_full.json", encoding="utf-8"))["names"])
gear = set(json.load(open(BASE + "/official_gear_names.json", encoding="utf-8"))["names"])
baowu = set(json.load(open(BASE + "/official_baowu_names.json", encoding="utf-8")))
gear_raw = json.load(open(BASE + "/gear_id.json", encoding="utf-8"))
citiao = set()
for e in gear_raw:
    for f in ("skillName", "policyName"):
        for p in re.split(r"[；;、/]", str(e.get(f) or "")):
            p = p.strip()
            if p:
                citiao.add(p)
KNOWN_CITIAO = set("""骁锐 英勇 至策 筹算 天资 颖悟 仁心 机敏 坚忍 艮止 灵动 惑言 亢厉 熟虑 破敌 破甲
奔袭 陷阵 强击 驱火 固阵 不移 善谋 鬼谋 疾行 千钧 迸发 无畏 齐射 射马 长兵 先导 掩日 止戈 备武
威风 天威 神锋 众谋 利兵 久战 百战 攻其 反计 不攻 避其 一夫 单骑 浑水 当阳 河内 枭雄 及锋 戒备
济世 归心 妙算 先知 护主 稳固 强韧 明智 武略 王道 铁壁 守备 列阵 勇毅 迂回 地利 清毅 亢力 眩惑
识破 取衡 安居 安贞 强固 再战 奇袭 盛气 睚眦 矜节 破浪 破障 穿杨 繁荣 英才 课增 谋断 豪纵 迅猛
逐胜 避险 采石 阵舞 抖擞 慑心 炎势 燮理 明镜 机先 丰收 鸠佑 劲弩 勇猛 承影 大橹 障日""".split())
WHITE = hero | jin | gear | baowu | citiao | KNOWN_CITIAO

# 非战法/武将的合法通用词（体系名、俗称、界面词、队伍黑话、常见游戏术语），断言里出现属正常
OK_OTHER = set("""法刀 菜刀 钢板 螃蟹 核弹 核弹弓 斩龙 斩龙刀 流氓 小流氓 战磐 垒实 神赏 攻其 磐阵
豹文刀 豹文辽 苗刀 鬼吕 衡轭 枭雄 长弓 长枪 长兵 弓兵 骑兵 步兵 器械 盾兵 藤甲 藤甲兵 象兵
大营 中军 前锋 主将 副将 指挥 主动 被动 追击 突击 阵法 兵种 词条 宝物 战法 武将 队伍 体系
南蛮 蜀骑 魏骑 群骑 吴弓 混乱 暴走 眩晕 沙暴 焚烧 虚弱 计穷 犹豫 缴械 溃逃 震慑 妖术 空城
一级 二级 三级 满级 白板 红度 士气 玉符 内政 开荒 赛季 征服 流浪军 主公 战报 立绘 头像
以诱待来 以逸待劳 心愿武将 北冥 西凉铁骑 九万八千玉 浑水摸鱼 重置列表 真谛 筹算游飘""".split())

def doc_text(f):
    d = Document(f)
    t = "\n".join(p.text for p in d.paragraphs)
    for tb in d.tables:
        for r in tb.rows:
            for c in r.cells:
                t += "\n" + c.text
    return t

# 断言触发词：其后紧跟的名称是"修正结论/画面确认结果"，必须正确
# 强制要求名称带 「」『』【】 定界，避免把流程箭头/散文误当断言
ASSERT = re.compile(
    r"(?:实为|实际为|确认为|逐帧确认为|明确为|画面确认为|画面显示为|画面明确为|画面可读为|应为|"
    r"正确名称[为是]?|更正为|订正为|正名为|全名为|战法全名为|→|纠正为)\s*"
    r"[「『【]([\u4e00-\u9fff]{2,7})[」』】]"
)
# 名称类别标记：断言的对象必须是 战法/武将/宝物/词条，否则是普通词汇修正，跳过
KIND = re.compile(r"(?:战法|武将|宝物|词条|携带|自带|拆解|阵容|队伍|兵种|技能|S级|A级|B级|XP|指挥|主动|被动|追击)")
# 引用触发词：其后名称是被引用的错名，合法
QUOTE_MARK = re.compile(r"(?:既有报告|既有音频|音频转写|音频版|转写为|转写作|误写|误读|误作|写作|记为|"
                        r"称为|音译|近音|读音|无法确认|猜测|泛称|标注「?推断|旧版)")

def is_cited(text, pos, span=34):
    """判断位置 pos 前 span 字内是否有引用标记 —— 有则该 token 属被引用错名。"""
    return bool(QUOTE_MARK.search(text[max(0, pos - span):pos]))

def scan(f):
    text = doc_text(f)
    out, seen = [], set()
    for m in ASSERT.finditer(text):
        tok = m.group(1)
        if tok in WHITE or tok in OK_OTHER:
            continue
        if len(tok) < 2:
            continue
        # 断言词本身若处在"引用从句"中（如：既有报告称实为X），仍按断言处理，
        # 但若断言词紧跟在引用标记后 8 字内，视为复述，降级
        pre = text[max(0, m.start() - 8):m.start()]
        if QUOTE_MARK.search(pre):
            continue
        # 必须是"名称类"断言：附近须出现 战法/武将/宝物 等类别词
        near = text[max(0, m.start() - 25):m.end() + 25]
        if not KIND.search(near):
            continue
        if tok in seen:
            continue
        seen.add(tok)
        ctx = text[max(0, m.start() - 40):m.end() + 30].replace("\n", " ")
        out.append({"tok": tok, "trigger": m.group(0)[:6], "ctx": ctx})
    return out

SETS = []
if ONLY in ("both", "full"):
    SETS.append(("完整版", sorted(glob.glob(REP + "/*_完整学习报告.docx"))))
if ONLY in ("both", "1s"):
    SETS.append(("一秒版", sorted(glob.glob(REP + "/*_逐帧深度学习报告_1秒版.docx"))))

result = {}
for label, files in SETS:
    hits = {}
    for f in files:
        r = scan(f)
        if r:
            hits[os.path.basename(f)] = r
    result[label] = hits
    n = sum(len(v) for v in hits.values())
    print("=" * 70)
    print(f"【{label}】断言型非白名单命中 {n} 条 / {len(hits)} 份")
    for bn, v in hits.items():
        print(f"--- {bn}")
        for x in v:
            print(f"    「{x['tok']}」 ({x['trigger']})  例: {x['ctx'][:70]}")

json.dump(result, open(BASE + "/scan_assert_report.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\n[完成] 写出 scan_assert_report.json")
