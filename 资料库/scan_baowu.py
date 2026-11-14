# -*- coding: utf-8 -*-
"""全量巡检 51 份报告中的 宝物名 + 宝物词条，找出疑似 OCR 误识。"""
import sys, glob, re, json, os
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

REP = "D:/Desktop/shandou/学习汇报"

# ---- 权威参考集（真实存在的率土宝物/词条，来源：名词概念.md + 官网 + 已知） ----
REF_BAOWU = set("""
游飘 元戎 大将 博浪 彤素 沧海 别鸣 大柯斧 两仪刀 铁匕首 惊鲵 承影 万仞 乌号 劲弩
木鹿 天降 短弩 连弩 白羽扇 雕翎扇 长枪 大斧 巨斧 双戟 玄头双戟 三尖刀 环首刀
铁脊蛇矛 古锭刀 养由基弓 宝雕弓 蹶张弩 宣花斧 凤凰 钜黍 大橹 星汉 游飘 元戎
""".split())

REF_CITIAO = set("""
英勇 筹算 骁锐 天资 仁心 机敏 灵动 坚忍 艮止 惑言 至策 破敌 奔袭 破甲 无畏 不移
清毅 善谋 亢力 驱火 眩惑 识破 勇毅 列阵 守备 迂回 地利 稳固 强韧 护主 先知 妙算
颖悟 不懈 戒备 济世 归心 长兵 先导 齐射 射马 掩日 止戈 备武 威风 天威 神锋
众谋 利兵 久战 百战 攻其 反计 不攻 避其 一夫 单骑 浑水 当阳 河内 枭雄 及锋
""".split())

# 从名词概念.md 解析已立专条的术语，补入参考集
term_doc = open("D:/Desktop/shandou/资料库/名词概念.md", encoding="utf-8").read()
for m in re.finditer(r"^###\s+([一-龥A-Za-z（）、，·\s]{1,12})", term_doc, re.M):
    REF_BAOWU.add(m.group(1).strip())
    REF_CITIAO.add(m.group(1).strip())

# ---- 抽取每份报告的 宝物名 + 词条 ----
def extract(path):
    t = "\n".join(p.text for p in Document(path).paragraphs)
    # 宝物名：宝物「X」 / X（宝物） / 宝物X / X宝物
    names = set()
    for m in re.finditer(r"宝物[「『]?([\u4e00-\u9fff]{1,6})[」』]?", t):
        names.add(m.group(1))
    for m in re.finditer(r"([\u4e00-\u9fff]{2,4})[（(]宝物[)）]", t):
        names.add(m.group(1))
    # 词条：【X】
    citiao = set(re.findall(r"【([\u4e00-\u9fff]{1,6})】", t))
    # 也抓 （X） 形式的词条描述
    return names, citiao, t

results = []
for f in sorted(glob.glob(REP + "/*_逐帧深度学习报告_1秒版.docx")):
    name = os.path.basename(f)
    names, citiao, _ = extract(f)
    susp_names = sorted(n for n in names if n not in REF_BAOWU and len(n) >= 2)
    susp_citiao = sorted(c for c in citiao if c not in REF_CITIAO and len(c) >= 2)
    if susp_names or susp_citiao:
        results.append((name, susp_names, susp_citiao))

print(f"扫描 51 份，命中疑似宝物/词条的报告 {len(results)} 份\n")
for name, sn, sc in results:
    print(f"▸ {name[:32]}")
    if sn: print(f"    宝物名疑似: {sn}")
    if sc: print(f"    词条疑似:   {sc}")

# 汇总所有疑似词
all_names = sorted({n for _, sn, _ in results for n in sn})
all_citiao = sorted({c for _, _, sc in results for c in sc})
print(f"\n=== 疑似宝物名全集 ({len(all_names)}) ===")
print("  " + " ".join(all_names))
print(f"\n=== 疑似词条全集 ({len(all_citiao)}) ===")
print("  " + " ".join(all_citiao))

json.dump({"results": results, "all_names": all_names, "all_citiao": all_citiao},
          open("D:/Desktop/shandou/资料库/scan_baowu_out.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\n[完成] 写出 资料库/scan_baowu_out.json")
