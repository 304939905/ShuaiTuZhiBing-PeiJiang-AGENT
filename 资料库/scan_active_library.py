# -*- coding: utf-8 -*-
"""对当前活跃报告库(报告库/)全量扫描疑似错词/无法理解词。
核心思路：抽取报告中被「」引号/稀有后缀/语境标记的 2-6 字 token，
与官方白名单(武将298+战法650+宝物114+词条+内政307)比对：
  A) 无任何近邻(编辑距离>2) -> "查无此词"候选（黑话/误听/错名）
  B) 有近邻(距离<=2)      -> "疑似误写"候选
同时输出所有 token 跨文件出现次数，供抽检。
用法: python scan_active_library.py
输出: 资料库/_active_scan_unknown.json / _active_scan_miswrite.json / _active_scan_all_tokens.json
"""
import sys, re, json, os
from collections import Counter, defaultdict
from docx import Document

BASE = "D:/Desktop/shandou/资料库"
ROOT = "D:/Desktop/shandou/报告库"
SUB = ["旧56项目", "开荒", "赛季"]
LAYERS = ["精编", "逐帧1秒版"]

def load_names(fn, key=None):
    d = json.load(open(f"{BASE}/{fn}", encoding="utf-8"))
    if isinstance(d, list):
        return set(d)
    return set(d.get(key, [])) if key else set(d.get("names", []))

HERO = load_names("official_hero_names.json")
JIN = load_names("official_jineng_names_ext.json")
GEAR = load_names("official_gear_names.json")
BAOWU = set(json.load(open(f"{BASE}/official_baowu_names.json", encoding="utf-8")))
POLICY = load_names("official_policy_names.json")

# 宝物词条(非宝物名)
gear_raw = json.load(open(f"{BASE}/gear_id.json", encoding="utf-8"))
CITIAO = set()
for e in gear_raw:
    for f in ("skillName", "policyName"):
        for p in re.split(r"[；;、/]", str(e.get(f) or "")):
            p = p.strip()
            if p:
                CITIAO.add(p)
CITIAO |= set("""骁锐 英勇 至策 筹算 天资 颖悟 仁心 机敏 坚忍 艮止 灵动 惑言 亢厉 熟虑 破敌 破甲
奔袭 陷阵 强击 驱火 固阵 不移 善谋 鬼谋 疾行 千钧 迸发 无畏 齐射 射马 长兵 先导
掩日 止戈 备武 威风 天威 神锋 众谋 利兵 久战 百战 攻其 反计 不攻 避其 一夫 单骑
浑水 当阳 河内 枭雄 及锋 戒备 济世 归心 妙算 先知 护主 稳固 强韧 明智 武略 王道
铁壁 守备 列阵 勇毅 迂回 地利 清毅 亢力 眩惑 识破 取衡 安居 安贞 强固 再战 奇袭
盛气 睚眦 矜节 破浪 破障 穿杨 繁荣 英才 课增 谋断 豪纵 迅猛 逐胜 避险 采石 阵舞
抖擞 慑心 炎势 燮理 明镜 机先 丰收 鸠佑 劲弩 勇猛 金吾 飞将 愈战 击势 御战 运用 恃强 淬锋""".split())

# 常见词/非标准名/体系黑话(排除误报)
KNOWN_OK = set("""我们 他们 这个 那个 什么 就是 可以 因为 所以 如果 但是 而且 并且 或者 然后 之后 之前
上面 下面 里面 外面 前后 为首 称为 叫做 名为 即 叫 是 为 一名 称 做 写作 误写 标注 显示 展开
确认 给出 可见 栏 模型 与 和 及 下 中 上 内 外 后 前 首 全 完 新 旧 完整 具体 选择 方案 类型 自带
效果 数值 价格 材料 流通 交易 商队 商店 毕业 库存 最优 普通 右侧 左侧 正名 二次 现有 术语 库 打通
恢复 减 限制 门槛 专 援护 下达 专题 条件下 称与 称为 称写作 称存疑 跟 都 改名 佩戴 详情页 交易场
证据 既有 介绍 面板 界面 系统 名称 词条 打造 仓库 详情 锻造 强化 进阶 列表 信息 配置 画面 才能 方面
即为 分别 代表 推荐 携带 这些 那些 这里 那里 进行 通过 由于 因此 所以 这种 那种 这样 那样 一些 一样
如何 怎么 怎样 哪些 所谓 组合 体系 搭配 配置 可选 位置 三个 两个 一个 多个 各种 各自 同时 其中 此外
另外 总之 核心 辅助 主要 重要 常见 常用 经典 主流 强势 弱势 优点 缺点 特点 机制 思路 玩法 攻略 视频
作者 本期 北冥 抖音 游戏 率土 玩家 账号 平民 新手 老玩家 大佬 实战 测试 验证 结论 说明 解释 分析 总结
建议 注意 提醒 强调 补充 提示 举例 例如 比如 其实 实际上 换句话说 也就是 输出 输入 进入 出现 展示 弹出
给出 列出 标记 表明 证明 对应 适用 适配 适合 使用 图片 画面 截图 字幕 台词 旁白 语音 转写 原文 引用
内容 信息 数据 表格 图例 卡包 武将 战法 宝物 队伍 阵容 体系 开荒 赛季 征服 试师 玉符 内政 资源 木铁石粮
民心 势力 城池 土地 地块 行军 战报 战斗 兵种 属性 攻击 防御 谋略 速度 攻城 基础 增长率 阈值 公式 计算
成长 满红 白板 高红 低红 红度 满级 等级 星级 品质 稀有 典藏 传说 史诗 普通 进阶 强化 锻造 词条 材料
排行榜 首冲 充值 月卡 周卡 特惠 礼包 招募 卡池 保底 心愿 换将 拆解 学习 研究 打造 佩戴 携带 装备
武器 防具 饰品 坐骑 兵书 阵型 站位 大营 中军 前锋 主将 副将 联动 搭档 伙伴 配合 克制 被克 天敌
必胜 必败 稳赢 稳输 优势 劣势 高端 低端 顶配 平民 豹子头 零氪 微氪 重氪 白嫖 氪金 欧皇 非酋
""".split())

KNOWN_OK |= HERO | JIN | GEAR | BAOWU | POLICY | CITIAO
KNOWN_OK |= {"关妹", "焚决", "神赏", "神兵天降", "赏罚分明", "率土", "抖音", "北冥", "UP主", "up主"}

PROSE = set("""我们 他们 这个 那个 什么 就是 可以 因为 所以 如果 但是 而且 并且 或者 然后 之后 之前
上面 下面 里面 外面 前后 为首 称为 叫做 名为 即 叫 是 为 一名 称 做 写作 误写 标注 显示 展开
确认 给出 可见 栏 模型 与 和 及 下 中 上 内 外 后 前 首 全 完 新 旧 完整 具体 选择 方案 类型 自带
效果 数值 价格 材料 流通 交易 商队 商店 毕业 库存 最优 普通 右侧 左侧 正名 二次 现有 术语 库 打通
恢复 减 限制 门槛 专 援护 下达 专题 条件下 称与 称为 称写作 称存疑 跟 都 改名 佩戴 详情页 交易场
证据 既有 介绍 面板 界面 系统 名称 词条 打造 仓库 详情 锻造 强化 进阶 列表 信息 配置 画面 才能 方面
即为 分别 代表 推荐 携带 这些 那些 这里 那里 进行 通过 由于 因此 所以 这种 那种 这样 那样 一些 一样
如何 怎么 怎样 哪些 所谓 组合 体系 搭配 配置 可选 位置 三个 两个 一个 多个 各种 各自 同时 其中 此外
另外 总之 核心 辅助 主要 重要 常见 常用 经典 主流 强势 弱势 优点 缺点 特点 机制 思路 玩法 攻略 视频
作者 本期 北冥 抖音 游戏 率土 玩家 账号 平民 新手 老玩家 大佬 实战 测试 验证 结论 说明 解释 分析 总结
建议 注意 提醒 强调 补充 提示 举例 例如 比如 其实 实际上 换句话说 也就是 输出 输入 进入 出现 展示 弹出
给出 列出 标记 表明 证明 对应 适用 适配 适合 使用 图片 画面 截图 字幕 台词 旁白 语音 转写 原文 引用
""".split())

# 语境片段里可能出现的高频普通中文词（非专名），ctx 源单独过滤
COMMON_CJK = set("""战法 武将 宝物 词条 阵容 队伍 体系 开荒 赛季 征服 试师 玉符 内政 资源 木铁 石粮 民心 势力
城池 土地 地块 行军 战报 战斗 兵种 属性 攻击 防御 谋略 速度 攻城 基础 增长率 阈值 公式 计算 成长
满红 白板 高红 低红 红度 满级 等级 星级 品质 稀有 典藏 传说 史诗 进阶 强化 锻造 材料 排行 首冲
充值 月卡 周卡 特惠 礼包 招募 卡池 保底 心愿 换将 拆解 学习 研究 佩戴 携带 装备 武器 防具 饰品
坐骑 兵书 阵型 站位 大营 中军 前锋 主将 副将 联动 搭档 伙伴 配合 克制 被克 天敌 必胜 必败 稳赢
稳输 优势 劣势 高端 低端 顶配 零氪 微氪 重氪 白嫖 氪金 欧皇 非酋 标签 版本 标题 报告 深度学习
精修 精编 视频 核心 结论 字幕 文字 提示 证据 索引 溯源 附录 章节 要点 摘要 内容 范围 详解 案例 方法
误区 确认 卡池 心愿 武将 详情 面板 实测 配置 搭配 组合 体系 开荒 战报 战法 效果 数值 属性 兵种 秒版 末溯 一节 音频 来了 改留 细节 提高 不再 看懂 好吗 控制 指挥 输出 输入 战法篇 魏晋篇 出奇 散射
伤害 兵力 恢复 减伤 增伤 触发 发动 概率 几率 持续 回合 距离 类型 品级 等级 星级 红度 满红 白板
战法图标 战法实测 指挥战法 主动战法 被动战法 追击战法 拆解战法 保护战法 核心武将 核心结论 视频核心
战法配置 战法位 个战法位 发动率 有效距离 带时间锚 归为对 心结论 全率土最 率土最 重磅来袭 最强搭配
一个战法 信息点 卡包 招募 心愿 武将找回 视频标题 视频编号 时长 满级 进阶 强化 锻造 词条 材料
""".split())

# 位置组合词：大营/中军/前锋/主将/副将 + 武将名（去掉前缀后是白名单则放行）
POSITION = ["大营", "中军", "前锋", "主将", "副将"]
# 已知昵称/体系名（非官方名但合法，勿误报）
KNOWN_ALIAS = {"马妹", "鬼吕", "嘟嘟", "菜刀", "法刀", "网红", "钢板", "流氓", "魏智", "蜀智",
               "群骑", "弓兵", "步兵", "骑兵", "神赏", "焚决", "关妹", "斩龙", "核弹", "木鹿",
               "螃蟹", "枭雄", "衡轭", "双减", "形兵", "始计", "法正", "张机", "灵帝", "太后"}

QUOTE = re.compile(r"[「『]([\u4e00-\u9fff]{2,6})[」』]")
RARE = re.compile(r"([\u4e00-\u9fff]{2,6})[（(](?:S级|A级|B级|C级|XP|指挥|主动|追击|被动|增益|减伤)[^）)]{0,14}[)）]")
CTX_MARK = re.compile(r"(?:战法|携带|带|学习|拆解|搭配|配置|武将|核心|阵容|大营|中军|前锋|主将|副将|联动|搭档|伙伴|XP|S级|A级|B级|S2|宝物|词条)")

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
        if abs(len(w) - len(tok)) > 2:
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

def scan_file(f):
    text = doc_text(f)
    toks = []  # (tok, ctx, src)
    for m in QUOTE.finditer(text):
        tok = m.group(1)
        s = max(0, m.start() - 15); e = min(len(text), m.end() + 15)
        toks.append((tok, text[s:e].replace("\n", " "), "quote"))
    for m in RARE.finditer(text):
        tok = m.group(1)
        s = max(0, m.start() - 15); e = min(len(text), m.end() + 15)
        toks.append((tok, text[s:e].replace("\n", " "), "rare"))
    for mm in CTX_MARK.finditer(text):
        s = max(0, mm.start() - 2); e = min(len(text), mm.end() + 12)
        seg = text[s:e].replace("\n", " ")
        for tm in re.finditer(r"([\u4e00-\u9fff]{2,6})", seg):
            tok = tm.group(1)
            dj, bj = min_ed(tok, JIN); dh, bh = min_ed(tok, HERO)
            dg, bg = min_ed(tok, GEAR)
            if min(dj, dh, dg) <= 3:
                toks.append((tok, seg, "ctx"))
    return toks

results = defaultdict(Counter)   # tok -> {file: count}
ctx_samples = defaultdict(list)  # tok -> [ctx...]
file_count = defaultdict(set)

files = []
for sub in SUB:
    for layer in LAYERS:
        d = f"{ROOT}/{sub}/{layer}"
        if os.path.isdir(d):
            files += [f"{d}/{f}" for f in sorted(os.listdir(d)) if f.endswith(".docx")]
# 战法阈值报告
extra = ["战法阈值精简学习报告.docx"]
for f in extra:
    if os.path.exists(f"{ROOT}/{f}"):
        files.append(f"{ROOT}/{f}")

for f in files:
    try:
        toks = scan_file(f)
    except Exception as ex:
        print("ERR", f, ex, file=sys.stderr)
        continue
    fname = os.path.basename(f)[:30]
    for tok, ctx, src in toks:
        if len(tok) < 2 or tok in KNOWN_OK or tok in PROSE:
            continue
        # 位置组合词：大营X/中军X/前锋X → 去掉前缀后是白名单武将则放行
        if src == "ctx" or True:
            for pos in POSITION:
                if tok.startswith(pos):
                    core = tok[len(pos):]
                    if core in HERO or core in JIN or core in KNOWN_ALIAS:
                        break
                    if min_ed(core, HERO)[0] <= 1:
                        break
            else:
                pos = None
            if pos:
                continue
        # 昵称/体系名放行
        if tok in KNOWN_ALIAS:
            continue
        # 语境片段里的普通词再排除一轮（非专名高频中文）
        if src == "ctx" and tok in COMMON_CJK:
            continue
        results[tok][fname] += 1
        if len(ctx_samples[tok]) < 3:
            ctx_samples[tok].append(ctx)

# 分类
unknown = {}   # 无近邻
miswrite = {}  # 有近邻 ed<=2
for tok, cnt in results.items():
    dj, bj = min_ed(tok, JIN)
    dh, bh = min_ed(tok, HERO)
    dg, bg = min_ed(tok, GEAR)
    dmin = min(dj, dh, dg)
    if dmin <= 2:
        closest = bj if dj == dmin else (bh if dh == dmin else bg)
        miswrite[tok] = {"files": len(cnt), "occurrences": sum(cnt.values()),
                         "dist": dmin, "closest": closest,
                         "samples": ctx_samples[tok], "per_file": dict(cnt)}
    else:
        unknown[tok] = {"files": len(cnt), "occurrences": sum(cnt.values()),
                        "samples": ctx_samples[tok], "per_file": dict(cnt)}

# 排序输出
def sortby(d):
    return dict(sorted(d.items(), key=lambda kv: -kv[1]["occurrences"]))

unknown_s = sortby(unknown)
miswrite_s = sortby(miswrite)

json.dump(unknown_s, open(f"{BASE}/_active_scan_unknown.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(miswrite_s, open(f"{BASE}/_active_scan_miswrite.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print(f"扫描文件数: {len(files)}")
print(f"查无此词候选(无近邻): {len(unknown_s)} 个")
print(f"疑似误写候选(ed<=2): {len(miswrite_s)} 个")
print("\n=== 查无此词 TOP30 ===")
for tok, info in list(unknown_s.items())[:30]:
    print(f"  {tok} x{info['occurrences']} (files={info['files']}) | 例: {info['samples'][0][:60]}")
print("\n=== 疑似误写 TOP30 ===")
for tok, info in list(miswrite_s.items())[:30]:
    print(f"  {tok} -> {info['closest']} (d={info['dist']}) x{info['occurrences']} | 例: {info['samples'][0][:60]}")
