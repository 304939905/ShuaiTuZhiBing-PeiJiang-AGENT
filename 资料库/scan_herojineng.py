# -*- coding: utf-8 -*-
"""以官方 武将/战法 白名单为铁律，抽取报告中"被断言为武将/战法名"的 token，
   凡不在白名单、且编辑距离<=阈值到某白名单名的，列为疑似 OCR/音译误识。
   用法: python scan_herojineng.py [1s|full]"""
import sys, glob, re, os, json
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

BASE = "D:/Desktop/shandou/资料库"
REP = "D:/Desktop/shandou/学习汇报"
VER = sys.argv[1] if len(sys.argv) > 1 else "1s"

hero = set(json.load(open(BASE + "/official_hero_names.json", encoding="utf-8"))["names"])
jin = set(json.load(open(BASE + "/official_jineng_names_ext.json", encoding="utf-8"))["names"])
gear = set(json.load(open(BASE + "/official_gear_names.json", encoding="utf-8"))["names"])

# 宝物词条 + 已知非标准名，排除（它们不是武将/战法名）
gear_raw = json.load(open(BASE + "/gear_id.json", encoding="utf-8"))
citiao = set()
for e in gear_raw:
    for f in ("skillName", "policyName"):
        for p in re.split(r"[；;、/]", str(e.get(f) or "")):
            p = p.strip()
            if p:
                citiao.add(p)
KNOWN_CITIAO = set("""骁锐 英勇 至策 筹算 天资 颖悟 仁心 机敏 坚忍 艮止 灵动 惑言 亢厉 熟虑 破敌 破甲
奔袭 陷阵 强击 驱火 固阵 不移 善谋 鬼谋 疾行 千钧 迸发 无畏 齐射 射马 长兵 先导
掩日 止戈 备武 威风 天威 神锋 众谋 利兵 久战 百战 攻其 反计 不攻 避其 一夫 单骑
浑水 当阳 河内 枭雄 及锋 戒备 济世 归心 妙算 先知 护主 稳固 强韧 明智 武略 王道
铁壁 守备 列阵 勇毅 迂回 地利 清毅 亢力 眩惑 识破 取衡 安居 安贞 强固 再战 奇袭
盛气 睚眦 矜节 破浪 破障 穿杨 繁荣 英才 课增 谋断 豪纵 迅猛 逐胜 避险 采石 阵舞
抖擞 慑心 炎势 燮理 明镜 机先 丰收 鸠佑 劲弩 勇猛""".split())
NONSTD = citiao | KNOWN_CITIAO | {"关妹", "焚决", "神赏", "神兵天降", "赏罚分明"}

PROSE = set("""我们 他们 这个 那个 什么 就是 可以 因为 所以 如果 但是 而且 并且 或者 然后
之后 之前 上面 下面 里面 外面 前后 为首 称为 叫做 名为 即 叫 是 为 一名 称 做 写作 误写
标注 显示 展开 确认 给出 可见 栏 模型 与 和 及 下 中 上 内 外 后 前 首 全 完 新 旧 完整
具体 选择 方案 类型 自带 效果 数值 价格 材料 流通 交易 商队 商店 毕业 库存 最优 普通 右侧
左侧 正名 二次 现有 术语 库 打通 恢复 减 限制 门槛 专 援护 下达 专题 条件下 称与 称为 称写作
称存疑 跟 都 改名 佩戴 详情页 交易场 证据 既有 介绍 面板 界面 系统 名称 词条 打造 仓库 详情
锻造 强化 进阶 列表 信息 配置 画面 才能 方面 即为 分别 分别代表 代表 推荐 携带 这些 那些 这里
那里 以及 以及 进行 通过 由于 因此 所以 这种 那种 这样 那样 一些 一样 如何 怎么 怎样 哪些 所谓
组合 体系 搭配 配置 可选 位置 三个 两个 一个 多个 各种 各自 分别 同时 分别 其中 此外 另外 总之
核心 辅助 主要 重要 常见 常见 常用 经典 主流 强势 弱势 优点 缺点 特点 机制 思路 玩法 攻略 视频
作者 本期 本期 本期 本期 北冥 抖音 游戏 率土 玩家 账号 平民 新手 老玩家 大佬 实战 测试 验证 结论
说明 解释 分析 总结 建议 注意 提醒 强调 补充 提示 举例 例如 比如 比如 其实 实际上 换句话说 也就是
输出 输入 进入 出现 展示 弹出 给出 列出 标注 标记 显示 表明 证明 确认 对应 适用 适配 适合 搭配 使用
""".split())

def ed(a, b):
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]; dp[0] = i
        for j in range(1, n + 1):
            cur = dp[j]
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + cost)
            prev = cur
    return dp[n]

def min_ed(tok, wl):
    best = 99; bn = None
    for w in wl:
        if abs(len(w) - len(tok)) > 3:
            continue
        d = ed(tok, w)
        if d < best:
            best = d; bn = w
    return best, bn

def doc_text(f):
    doc = Document(f)
    t = "\n".join(p.text for p in doc.paragraphs)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                t += "\n" + cell.text
    return t

QUOTE = re.compile(r"[「『]([\u4e00-\u9fff]{2,6})[」』]")
RARE = re.compile(r"([\u4e00-\u9fff]{2,6})[（(](?:S级|A级|S2|XP|指挥|主动|追击|被动|增益)[^）)]{0,14}[)）]")
CTX_MARK = re.compile(r"(?:战法|携带|带|学习|拆解|搭配|配置|武将|核心|阵容|大营|中军|前锋|主将|副将|联动|搭档|伙伴|XP|S级|A级|S2)")

def scan_file(f):
    text = doc_text(f)
    out = []
    seen = set()
    def add(tok, kind, src, ctx, dist, closest):
        if not tok or tok in gear or tok in hero or tok in jin:
            return
        if tok in NONSTD or tok in PROSE:
            return
        key = (tok, kind, src)
        if key in seen:
            return
        seen.add(key)
        out.append({"tok": tok, "kind": kind, "src": src, "ctx": ctx[:40], "dist": dist, "closest": closest})
    # 1) quoted
    for m in QUOTE.finditer(text):
        tok = m.group(1)
        s = max(0, m.start() - 15); e = min(len(text), m.end() + 15)
        ctx = text[s:e].replace("\n", " ")
        dj, bj = min_ed(tok, jin); dh, bh = min_ed(tok, hero)
        if dj <= 3 or dh <= 3:
            kind = "战法" if dj <= dh else "武将"
            add(tok, kind, "quote", ctx, dj if kind == "战法" else dh, bj if kind == "战法" else bh)
    # 2) rarity-suffixed
    for m in RARE.finditer(text):
        tok = m.group(1)
        s = max(0, m.start() - 15); e = min(len(text), m.end() + 15)
        ctx = text[s:e].replace("\n", " ")
        dj, bj = min_ed(tok, jin)
        if dj <= 3:
            add(tok, "战法", "rare", ctx, dj, bj)
    # 3) context-marked plain
    for mm in CTX_MARK.finditer(text):
        s = max(0, mm.start() - 2); e = min(len(text), mm.end() + 12)
        seg = text[s:e]
        for tm in re.finditer(r"([\u4e00-\u9fff]{2,6})", seg):
            tok = tm.group(1)
            dj, bj = min_ed(tok, jin); dh, bh = min_ed(tok, hero)
            if dj <= 3 or dh <= 3:
                kind = "战法" if dj <= dh else "武将"
                add(tok, kind, "ctx", seg.replace("\n", " "), dj if kind == "战法" else dh, bj if kind == "战法" else bh)
    return out

if VER == "1s":
    patt = REP + "/*_逐帧深度学习报告_1秒版.docx"
else:
    patt = REP + "/*_完整学习报告.docx"

results = {}
for f in sorted(glob.glob(patt)):
    name = os.path.basename(f)
    res = scan_file(f)
    if res:
        results[name] = res

# 汇总
allt = {}
for name, res in results.items():
    for r in res:
        k = (r["tok"], r["kind"])
        allt.setdefault(k, {"count": 0, "files": set(), "closest": r["closest"], "dist": r["dist"], "ctx": r["ctx"]})
        allt[k]["count"] += 1
        allt[k]["files"].add(name)

print(f"版本={VER}  扫描文件={len(glob.glob(patt))}  命中文件={len(results)}  候选token种类={len(allt)}")
print("\n=== 高置信（dist<=2）===")
for k, v in sorted(allt.items(), key=lambda x: (x[1]["dist"], -x[1]["count"])):
    if v["dist"] <= 2:
        print(f"  [{v['dist']}] {k[1]}「{k[0]}」→ 最近「{v['closest']}」 出现{v['count']}次 例:{v['ctx']}")
print("\n=== 低置信（dist=3，待人工）===")
for k, v in sorted(allt.items(), key=lambda x: (-x[1]["count"], x[1]["dist"])):
    if v["dist"] == 3:
        print(f"  [3] {k[1]}「{k[0]}」→ 最近「{v['closest']}」 出现{v['count']}次 例:{v['ctx']}")

json.dump(results, open(BASE + f"/scan_herojineng_{VER}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\n[完成] 写出 scan_herojineng_{VER}.json")
