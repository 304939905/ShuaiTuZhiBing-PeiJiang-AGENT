# -*- coding: utf-8 -*-
"""精确抽取疑似宝物名/词条：被断言为宝物名或词条、但不属于任何已知率土实体的 token。"""
import sys, glob, re, os
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

REP = "D:/Desktop/shandou/学习汇报"

# ---- 权威白名单（来源：网易大神/百度百科/官网 + 名词概念.md） ----
BAOWU = set("""
游飘 元戎 大将 博浪 彤素 沧海 别鸣 惊鲵 承影 万仞 乌号 劲弩 钜黍 棕竹扇 昆吾
悬翦 铭鸿 冥山勾月 屈卢 铮角枪 真刚 子母刀 仁风扇 犀角弓 大柯斧 两仪刀 玄铁剑
旌阳万仞 随侯剑 锟铻 戚 少府 狰角枪 木鹿 天降 短弩 连弩 白羽扇 雕翎扇 长枪
大斧 巨斧 双戟 玄头双戟 三尖刀 环首刀 铁脊蛇矛 古锭刀 古锭 养由基弓 宝雕弓
蹶张弩 宣花斧 凤凰 大橹 星汉 仁风 乌金九环刀 点钢枪 罕俦随侯剑 罕铸乌金九环刀
犀角弓 真刚刀 斫刀 铁匕首 比翼 腾蛇
""".split())

CITIAO = set("""
骁锐 英勇 至策 筹算 天资 颖悟 仁心 机敏 坚忍 艮止 灵动 惑言 亢厉 熟虑 破敌 破甲
奔袭 陷阵 强击 驱火 固阵 不移 善谋 鬼谋 疾行 千钧 迸发 无畏 齐射 射马 长兵 先导
掩日 止戈 备武 威风 天威 神锋 众谋 利兵 久战 百战 攻其 反计 不攻 避其 一夫 单骑
浑水 当阳 河内 枭雄 及锋 戒备 济世 归心 妙算 先知 护主 稳固 强韧 明智 武略 王道
铁壁 守备 列阵 勇毅 迂回 地利 天威 威风 神锋 备武
""".split())

# ---- 散文黑名单：出现在'宝物'之后但非宝物名的描述词 ----
PROSE = set("""
介绍 面板 界面 系统 名称 词条 打造 仓库 详情 锻造 强化 进阶 列表 信息 配置 画面
才能 方面 即为 分别为 代表 名为 也 均 可 推荐 携带 写作 误写 标注 显示 展开 确认
给出 可见 栏 模型 与 和 及 下 中 上 内 外 后 前 首 全 完 新 旧 完整 具体 选择 方案
类型 自带 效果 数值 价格 材料 流通 交易 商队 商店 毕业 库存 最优 普通 右侧 左侧
正名 二次 现有 术语 库 打通 恢复 减 限制 门槛 曹操 专 障日 龙林 龙鳞 等大槺
""".split())

# 从名词概念.md 补充已立专条
term_doc = open("D:/Desktop/shandou/资料库/名词概念.md", encoding="utf-8").read()
for m in re.finditer(r"^###\s+([一-龥A-Za-z（）、，·\s]{1,12})", term_doc, re.M):
    w = m.group(1).strip()
    BAOWU.add(w); CITIAO.add(w)

def clean_baowu_assertions(text):
    """返回被断言为宝物名的候选 token（干净 2-4 字中文）。"""
    cands = set()
    # X（宝物）
    for m in re.finditer(r"([\u4e00-\u9fff]{2,4})[（(]宝物[)）]", text):
        cands.add(m.group(1))
    # 宝物[名叫做是为:：]? NAME
    for m in re.finditer(r"宝物[名叫做是为:：]?\s*[「『]?([\u4e00-\u9fff]{2,4})", text):
        cands.add(m.group(1))
    # 携带/带/用 + NAME + 宝物
    for m in re.finditer(r"(?:携带|带|用|持)[「『]?([\u4e00-\u9fff]{2,4})[」』]?宝物", text):
        cands.add(m.group(1))
    return cands

def citiao_tokens(text):
    return set(re.findall(r"【([\u4e00-\u9fff]{2,4})】", text))

suspect_baowu = {}   # report -> set(cand not in BAOWU & not in PROSE)
suspect_citiao = {}  # report -> set(cand not in BAOWU & not in CITIAO)

for f in sorted(glob.glob(REP + "/*_逐帧深度学习报告_1秒版.docx")):
    name = os.path.basename(f).replace("_逐帧深度学习报告_1秒版.docx", "")
    doc = Document(f)
    text = "\n".join(p.text for p in doc.paragraphs)
    # 也扫表格
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                text += "\n" + cell.text
    b = clean_baowu_assertions(text)
    sb = {x for x in b if x not in BAOWU and x not in PROSE}
    c = citiao_tokens(text)
    sc = {x for x in c if x not in BAOWU and x not in CITIAO}
    if sb or sc:
        suspect_baowu[name] = sb
        suspect_citiao[name] = sc

print("########## 疑似宝物名（不在宝物白名单，且非散文词）##########")
allb = set()
for name, sb in suspect_baowu.items():
    if sb:
        print(f"\n▸ {name}")
        print("   " + " / ".join(sorted(sb)))
        allb |= sb
print(f"\n[宝物名候选全集 {len(allb)}] " + " / ".join(sorted(allb)))

print("\n\n########## 疑似词条【X】（不在宝物∪词条白名单）##########")
allc = set()
for name, sc in suspect_citiao.items():
    if sc:
        print(f"\n▸ {name}")
        print("   " + " / ".join(sorted(sc)))
        allc |= sc
print(f"\n[词条候选全集 {len(allc)}] " + " / ".join(sorted(allc)))

import json
json.dump({"baowu": {k: sorted(v) for k, v in suspect_baowu.items() if v},
           "citiao": {k: sorted(v) for k, v in suspect_citiao.items() if v}},
          open("D:/Desktop/shandou/资料库/scan_baowu_candidates.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\n[完成] 写出 scan_baowu_candidates.json")
