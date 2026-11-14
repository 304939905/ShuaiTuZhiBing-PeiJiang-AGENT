# -*- coding: utf-8 -*-
"""以官方 114 宝物名为铁律，精确抽取报告中"被断言为宝物名/词条"的 token，
   凡不在官方宝物名清单、也不在词条白名单的，列为疑似 OCR 误识。"""
import sys, glob, re, os, json
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

REP = "D:/Desktop/shandou/学习汇报"

# ---- 官方宝物名（来自官网 gear_id.json，114 个，权威） ----
OFFICIAL_BAOWU = set(json.load(open("D:/Desktop/shandou/资料库/official_baowu_names.json", encoding="utf-8")))

# ---- 词条白名单：gear_id 示例词条 + 已知权威词条 + 名词概念.md ----
gear = json.load(open("D:/Desktop/shandou/资料库/gear_id.json", encoding="utf-8"))
citiao = set()
for e in gear:
    for f in ("skillName", "policyName"):
        v = e.get(f) or ""
        for p in re.split(r"[；;、/]", str(v)):
            p = p.strip()
            if p:
                citiao.add(p)
KNOWN_CITIAO = set("""
骁锐 英勇 至策 筹算 天资 颖悟 仁心 机敏 坚忍 艮止 灵动 惑言 亢厉 熟虑 破敌 破甲
奔袭 陷阵 强击 驱火 固阵 不移 善谋 鬼谋 疾行 千钧 迸发 无畏 齐射 射马 长兵 先导
掩日 止戈 备武 威风 天威 神锋 众谋 利兵 久战 百战 攻其 反计 不攻 避其 一夫 单骑
浑水 当阳 河内 枭雄 及锋 戒备 济世 归心 妙算 先知 护主 稳固 强韧 明智 武略 王道
铁壁 守备 列阵 勇毅 迂回 地利 清毅 亢力 眩惑 识破 取衡 安居 安贞 强固 再战 奇袭
盛气 睚眦 矜节 破浪 破障 穿杨 繁荣 英才 课增 谋断 豪纵 迅猛 逐胜 避险 采石 阵舞
抖擞 慑心 炎势 燮理 明镜 机先 丰收 鸠佑 劲弩 勇猛
""".split())
CITIAO = citiao | KNOWN_CITIAO

# 名词概念.md 专条也并入（防漏）
term_doc = open("D:/Desktop/shandou/资料库/名词概念.md", encoding="utf-8").read()
for m in re.finditer(r"^###\s+([一-龥A-Za-z（）、，·\s]{1,12})", term_doc, re.M):
    CITIAO.add(m.group(1).strip())

# ---- 描述词黑名单：出现在宝物语境但非宝物名 ----
PROSE = set("""
介绍 面板 界面 系统 名称 词条 打造 仓库 详情 锻造 强化 进阶 列表 信息 配置 画面
才能 方面 即为 分别为 代表 名为 也 均 可 推荐 携带 写作 误写 标注 显示 展开 确认
给出 可见 栏 模型 与 和 及 下 中 上 内 外 后 前 首 全 完 新 旧 完整 具体 选择 方案
类型 自带 效果 数值 价格 材料 流通 交易 商队 商店 毕业 库存 最优 普通 右侧 左侧
正名 二次 现有 术语 库 打通 恢复 减 限制 门槛 曹操 专 障日 龙林 龙鳞 等大槺 修正 援护
下达 专题 条件下 称与 称为 称写作 称存疑 跟钜黍 都改名 佩戴 详情页 交易场 证据 既有
""".split())

def baowu_assertions(text):
    out = set()
    # X（宝物）
    for m in re.finditer(r"([\u4e00-\u9fff]{2,5})[（(]宝物[)）]", text):
        out.add(m.group(1))
    # 宝物[名叫做是为:：]? X(边界)
    for m in re.finditer(r"宝物[名叫做是为:：]?\s*[「『]?([\u4e00-\u9fff]{2,5})(?=[，。、）」\s])", text):
        out.add(m.group(1))
    # 为/是/叫/即/： X 宝物
    for m in re.finditer(r"(?:为|是|叫|即|：|:)\s*[「『]?([\u4e00-\u9fff]{2,5})宝物", text):
        out.add(m.group(1))
    # 携带/带 X 宝物
    for m in re.finditer(r"(?:携带|带)[「『]?([\u4e00-\u9fff]{2,5})[」』]?宝物", text):
        out.add(m.group(1))
    # X宝物(边界,无括号)
    for m in re.finditer(r"([\u4e00-\u9fff]{2,5})宝物(?=[，。、）」\s])", text):
        out.add(m.group(1))
    return out

def citiao_tokens(text):
    return set(re.findall(r"【([\u4e00-\u9fff]{2,5})】", text))

suspect_b = {}
suspect_c = {}
for f in sorted(glob.glob(REP + "/*_逐帧深度学习报告_1秒版.docx")):
    name = os.path.basename(f).replace("_逐帧深度学习报告_1秒版.docx", "")
    doc = Document(f)
    text = "\n".join(p.text for p in doc.paragraphs)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                text += "\n" + cell.text
    b = baowu_assertions(text)
    sb = {x for x in b if x not in OFFICIAL_BAOWU and x not in PROSE}
    c = citiao_tokens(text)
    sc = {x for x in c if x not in OFFICIAL_BAOWU and x not in CITIAO}
    if sb or sc:
        suspect_b[name] = sb
        suspect_c[name] = sc

print("########## 疑似宝物名（不在官方114宝物名，且非描述词）##########")
allb = set()
for name, sb in suspect_b.items():
    if sb:
        print(f"\n▸ {name}\n   " + " / ".join(sorted(sb)))
        allb |= sb
print(f"\n[宝物名候选全集 {len(allb)}] " + " / ".join(sorted(allb)))

print("\n\n########## 疑似词条【X】（不在宝物∪词条白名单）##########")
allc = set()
for name, sc in suspect_c.items():
    if sc:
        print(f"\n▸ {name}\n   " + " / ".join(sorted(sc)))
        allc |= sc
print(f"\n[词条候选全集 {len(allc)}] " + " / ".join(sorted(allc)))

json.dump({"baowu": {k: sorted(v) for k, v in suspect_b.items() if v},
           "citiao": {k: sorted(v) for k, v in suspect_c.items() if v}},
          open("D:/Desktop/shandou/资料库/scan_baowu_final.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\n[完成] 写出 scan_baowu_final.json")
