# -*- coding: utf-8 -*-
"""
Phase A docx 级重核验扫描器
==========================
对 学习汇报/ 下 *_逐帧深度学习报告_1秒版.docx（旧 56 视频项目最终交付物，51 份）
做实体级扫描，复用 gate_whitelist 的硬白名单（武将428/战法1127/宝物114 + SLANG + EXTRA）。

判定逻辑：
  - 复用 gate.extract 抓「位置槽/队伍三元/括号清单」实体；额外抓【】内清单。
  - 命中 KNOWN / 含已知子串 / 边界伪影 / 散文词 → 跳过。
  - 其余候选：编辑距离 1 到某白名单实体名 → 近名（疑似 OCR 错误，优先核查）。
  - 否则 → 未知（需人工/联网核查）。
输出分级报告到 _phaseA_docx_scan.txt。
"""
import sys, os, re, glob
sys.path.insert(0, r"D:\Desktop\shandou\资料库")
import gate_whitelist as G
from docx import Document

REPORT_DIR = r"D:\Desktop\shandou\学习汇报"
OUT = r"D:\Desktop\shandou\资料库\_phaseA_docx_scan.txt"

ENT = G.hero | G.skill | G.gear   # 全部实体名
# 散文/UI/描述 抑制词（描述画面或机制，非实体名）
PROSE = re.compile(r"(六维属性|成长值|红字|漫画|粉兔|龙袍|光柱|立绘|字幕|弹幕|面板|紫色|紫光|"
                   r"男子|表情|连贯|截图|规则表|卡包|积分|心愿|保底|COST|Lv|属性|攻击距离|战法点|"
                   r"宝物|白板|平民|月卡|零氪|低氪|同盟|赛季|区服|势力值|坐标|瞭望塔|视野|集火|"
                   r"菜刀|物理刀|法刀|控制|击败|胜利|占领|战果|聊天|战术|后手|空城|斩龙|替换|选项|"
                   r"剩余|阵容|核心队|指出|明确|确认|展示|显示|触发|利用|组织|打开|个人资料|盟友|"
                   r"都能|战队|队伍|车队|压秒|连捷|夷陵|决战|海棠|诗CPU|小诗|天天涨停|河南|同支|"
                   r"正始之变|知己知彼|侵掠如火|及锋而试|汜水关|皇裔流离|谋议宏图|全军突击|"
                   r"安抚军心|侵掠|四段|两段|三段|一段|五段|漫画粉兔|紫色光柱|龙袍男子)")

def lev(a, b):
    m, n = len(a), len(b)
    if abs(m - n) > 1:
        return 99
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]; dp[0] = i
        for j in range(1, n + 1):
            cur = dp[j]
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + (0 if a[i - 1] == b[j - 1] else 1))
            prev = cur
    return dp[n]

def closest(tok):
    best = (99, None)
    for nm in ENT:
        if abs(len(nm) - len(tok)) > 1:
            continue
        d = lev(tok, nm)
        if d < best[0]:
            best = (d, nm)
    return best

docx_paren = re.compile(r"[【\[]([^】\]]*)[】\]]")
doc_files = sorted(glob.glob(os.path.join(REPORT_DIR, "*_逐帧深度学习报告_1秒版.docx")))

agg = {}   # token -> list of (doc, kind, snippet)
open_fail = []
for fp in doc_files:
    name = os.path.basename(fp)
    try:
        doc = Document(fp)
    except Exception as e:
        open_fail.append(f"{name}: {e}")
        continue
    texts = [p.text for p in doc.paragraphs if p.text]
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                if c.text:
                    texts.append(c.text)
    for tx in texts:
        for tok, kind in G.extract(tx):
            agg.setdefault(tok, []).append((name, kind, tx))
        for m in docx_paren.finditer(tx):
            inner = m.group(1).strip()
            for t2 in re.split(r"[／/＋+，,、\s]", inner):
                t2 = t2.strip()
                if 2 <= len(t2) <= 5 and re.fullmatch(r"[一-鿿]+", t2):
                    agg.setdefault(t2, []).append((name, "bracket", tx))

# 二次过滤 + 分类
near, unknown = [], []
for tok, occ in agg.items():
    if tok in G.KNOWN or G.contains_known(tok) or G.is_artifact(tok) or PROSE.search(tok):
        continue
    d, cn = closest(tok)
    first = occ[0]
    snip = first[2][max(0, first[2].find(tok) - 20): first[2].find(tok) + len(tok) + 20]
    if d == 1:
        near.append((tok, cn, len(occ), first[0], snip))
    else:
        unknown.append((tok, d, cn, len(occ), first[0], snip))

with open(OUT, "w", encoding="utf-8") as f:
    f.write(f"DOCX 扫描：{len(doc_files)} 份 | 候选去重 {len(agg)} | "
            f"近名(OCR嫌疑) {len(near)} | 未知 {len(unknown)}\n")
    if open_fail:
        f.write("\n!! 打开失败: " + " ; ".join(open_fail) + "\n")
    f.write("\n===== 近名（编辑距离1，疑似 OCR 错误，优先核查）=====\n")
    for tok, cn, cnt, doc, snip in sorted(near, key=lambda x: -x[2]):
        f.write(f"· {tok} ≈ {cn}  出现{cnt}次  [{doc}]\n    …{snip}…\n")
    f.write("\n===== 未知（非近名，需人工/联网核查）=====\n")
    for tok, d, cn, cnt, doc, snip in sorted(unknown, key=lambda x: -x[3]):
        f.write(f"· {tok}  最近:{cn}(d{d})  出现{cnt}次  [{doc}]\n    …{snip}…\n")

print(f"done files={len(doc_files)} cands={len(agg)} near={len(near)} unknown={len(unknown)}")
