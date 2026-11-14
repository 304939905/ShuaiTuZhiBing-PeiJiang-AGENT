# -*- coding: utf-8 -*-
"""统一发布前校验门禁 (QC Gate)  v2
合并 5 类检查：
  A 文件完整性   —— 51 完整版 + 51 一秒版齐全、可打开、无损坏            (BLOCKING)
  B 已知修复回归 —— 前几轮已清零的错名必须不再以"断言/结论"形态出现      (BLOCKING)
  C 武将/战法    —— 高信噪比"断言型"名称反查官方合并白名单(960)，非白名单即红单
  D 宝物/词条    —— 官方宝物库(114) + 词条库 反查疑似误名
  E 待核实清单   —— 名词概念.md 附录B 未结案项命中定位
判定：gate_ok = A 通过 且 B 回归=0。C/D/E 为顾问级红单，不阻断交付。

关键方法论（v2 升级）：
  引用型 vs 断言型 区分。
    引用型 —— 「既有报告写作「壁瑞」」「误识为「捋出关西」」「（姊妹篇《以逸待劳》）」
             错名是被"引用/对照"的旧名，合法，不算回归。
    断言型 —— 「实为「X」」「画面确认为「X」」「正名为「X」」修正结论本身，
             必须落在官方白名单；否则是高危"把错的改成另一个错的"。
  B 回归只统计"非引用"形态；C 只统计"断言型"非白名单名。
用法: python qc_gate.py            (两套都扫)
      python qc_gate.py full|1s    (只扫一套)
"""
import sys, glob, re, os, json
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

BASE = "D:/Desktop/shandou/资料库"
REP = "D:/Desktop/shandou/学习汇报"
ONLY = sys.argv[1] if len(sys.argv) > 1 else "both"

# ---------------- 白名单（合并：扩展战法650 ∪ 内政政策307 ∪ 确认真实战法3） ----------------
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
CITIAO = citiao | KNOWN_CITIAO
NONSTD = CITIAO | {"关妹", "焚决", "神赏", "神兵天降", "赏罚分明"}

PROSE = set("""我们 他们 这个 那个 什么 就是 可以 因为 所以 如果 但是 而且 并且 或者 然后
之后 之前 上面 下面 里面 外面 前后 为首 称为 叫做 名为 即 叫 是 为 一名 称 做 写作 误写
标注 显示 展开 确认 给出 可见 栏 模型 与 和 及 下 中 上 内 外 后 前 首 全 完 新 旧 完整
具体 选择 方案 类型 自带 效果 数值 价格 材料 流通 交易 商队 商店 毕业 库存 最优 普通 右侧
左侧 正名 二次 现有 术语 库 打通 恢复 减 限制 门槛 专 援护 下达 专题 条件下 称与 称为 称写作
称存疑 跟 都 改名 佩戴 详情页 交易场 证据 既有 介绍 面板 界面 系统 名称 词条 打造 仓库 详情
锻造 强化 进阶 列表 信息 配置 画面 才能 方面 即为 分别 分别代表 代表 推荐 携带 这些 那些 这里
那里 以及 进行 通过 由于 因此 这种 那种 这样 那样 一些 一样 如何 怎么 怎样 哪些 所谓
组合 体系 搭配 可选 位置 三个 两个 一个 多个 各种 各自 同时 其中 此外 另外 总之
核心 辅助 主要 重要 常见 常用 经典 主流 强势 弱势 优点 缺点 特点 机制 思路 玩法 攻略 视频
作者 本期 北冥 抖音 游戏 率土 玩家 账号 平民 新手 老玩家 大佬 实战 测试 验证 结论
说明 解释 分析 总结 建议 注意 提醒 强调 补充 提示 举例 例如 比如 其实 实际上 换句话说 也就是
输出 输入 进入 出现 展示 弹出 列出 标记 表明 证明 对应 适用 适配 适合 使用
""".split())

BAOWU_PROSE = set("""介绍 面板 界面 系统 名称 词条 打造 仓库 详情 锻造 强化 进阶 列表 信息 配置 画面
才能 方面 即为 分别为 代表 名为 也 均 可 推荐 携带 写作 误写 标注 显示 展开 确认
给出 可见 栏 模型 与 和 及 下 中 上 内 外 后 前 首 全 完 新 旧 完整 具体 选择 方案
类型 自带 效果 数值 价格 材料 流通 交易 商队 商店 毕业 库存 最优 普通 右侧 左侧
正名 二次 现有 术语 库 打通 恢复 减 限制 门槛 曹操 专 障日 龙林 龙鳞 等大槺 修正 援护
下达 专题 条件下 称与 称为 称写作 称存疑 跟钜黍 都改名 佩戴 详情页 交易场 证据 既有""".split())

# ---------------- 待核实（名词概念.md 附录B 未结案） ----------------
OPEN_TERMS = {"胜负先征", "胜负先争"}

# ---------------- 已知修复回归项（必须 =0，且只统计"非引用"形态） ----------------
WRONG = ["重谋", "夹许", "三势", "河内", "顶足", "壁瑞", "几封讯类", "以逸待劳", "奉移艇",
         "极锋而适", "鸟云山兵", "当仰巧", "风生火烧", "操缠", "垒实迎虚", "唐童",
         "Boss", "成育", "雷石", "重整", "机势"]
# 注：豹文刀/豹文辽/苗刀 为玩家队伍黑话（曹纯+张辽+文鸯 等），非战法 OCR 误名，不入 WRONG，
#     且作为合法俗称加入 OK_OTHER（见下），避免误判。
# 精确误用形态：合法前缀需带正确后缀才放行
WRONG_STRICT = {
    "河内": r"河内(?!郡|之地|世泽)",   # 词条【河内】合法；战法「河内世泽」合法；其余河内=误用
    "三势": r"三势(?!阵)",             # 三势阵 合法
    "重整": r"重整(?!旗鼓|军备)",
}
EST_PATTERNS = ["是否程昱", "不程昱", "才程昱", "都程昱", "仍程昱", "同时程昱", "能否程昱",
                "稳定程昱", "规律程昱", "程昱的前提", "不能同时程昱", "保护组合程昱",
                "保护程昱", "前提下程昱"]

# ---------------- 引用/断言 区分工具 ----------------
# 核心：已知修复错名（WRONG）只在"作为修正结论被断言"时才算回归残留；
# 在差异说明/校正表里作为"被引用的旧名"出现（如「壁瑞」实为「避锐治气」、
# 音频中的「河内/三数」、仅描述为「…壁瑞…」）一律合法，不计回归。
# 判定：错名是否处在断言触发词（实为/确认为/画面显示为/应为/正名为/即/名为…）
# 之后 16 字内、且紧跟其（可选「」）出现 —— 即它是"被断言为正确的名称"。
ASSERT_T = re.compile(
    r"(?:实为|实际为|确认为|逐帧确认为|明确为|画面确认为|画面显示为|画面明确为|画面可读为|"
    r"应为|正确名称[为是]?|更正为|订正为|正名为|全名为|战法全名为|纠正为|即|名为|叫做|称为|叫)\s*[「『【]?"
)

def count_assertion(text, w, strict_re=None):
    """统计 w 在 text 中"作为修正结论被断言"的出现次数（真正的回归残留）。
    差异说明/校正表里作为旧名被引用（非断言目标）的不计入。"""
    if strict_re:
        matches = list(re.finditer(strict_re, text))
    else:
        matches = list(re.finditer(re.escape(w), text))
    n = 0
    for m in matches:
        # 仅当断言触发词紧邻 token（≤8 字内，含可选「」）才算"把错名断言为正确结论"。
        # 差异说明/校正表中作为旧名被引用（如「壁瑞」实为「避锐治气」、
        # "战法正确名称 音频版报告写作「垒实迎虚」" 的「正确名称」是节标题，隔得远）不计入。
        pre = text[max(0, m.start() - 8):m.start()]
        if ASSERT_T.search(pre):
            n += 1
    return n

# ---------------- C 断言型名称扫描（高信噪比） ----------------
# 断言触发词：其后紧跟的名称是"修正结论/画面确认结果"，必须正确
ASSERT = re.compile(
    r"(?:实为|实际为|确认为|逐帧确认为|明确为|画面确认为|画面显示为|画面明确为|画面可读为|应为|"
    r"正确名称[为是]?|更正为|订正为|正名为|全名为|战法全名为|纠正为)\s*"
    r"[「『【]([\u4e00-\u9fff]{2,7})[」』】]"
)
# 名称类别标记：断言对象须是 战法/武将/宝物/词条
KIND = re.compile(r"(?:战法|武将|宝物|词条|携带|自带|拆解|阵容|队伍|兵种|技能|S级|A级|B级|XP|指挥|主动|被动|追击)")
# 引用触发词：其后名称是被引用的错名，合法
QUOTE_MARK2 = re.compile(r"(?:既有报告|既有音频|音频转写|音频版|转写为|转写作|误写|误读|误作|误识为|写作|记为|"
                         r"称为|音译|近音|读音|无法确认|猜测|泛称|标注「?推断|旧版|原片|前作|上集|同系列|同款|"
                         r"对比|卡面佐证|姊妹|画面对比|早期|初版|草案|暂记|待核|亦作)")
# 非战法/武将的合法通用词（体系名、俗称、界面词），断言里出现属正常
OK_OTHER = set("""法刀 菜刀 钢板 螃蟹 核弹 核弹弓 斩龙 斩龙刀 流氓 小流氓 战磐 垒实 神赏 攻其 磐阵
豹文刀 豹文辽 苗刀 鬼吕 衡轭 枭雄 长弓 长枪 长兵 弓兵 骑兵 步兵 器械 盾兵 藤甲 藤甲兵 象兵
大营 中军 前锋 主将 副将 指挥 主动 被动 追击 突击 阵法 兵种 词条 宝物 战法 武将 队伍 体系
南蛮 蜀骑 魏骑 群骑 吴弓 混乱 暴走 眩晕 沙暴 焚烧 虚弱 计穷 犹豫 缴械 溃逃 震慑 妖术 空城
一级 二级 三级 满级 白板 红度 士气 玉符 内政 开荒 赛季 征服 流浪军 主公 战报 立绘 头像""".split())
# 队伍黑话（合法俗称，非战法 OCR 误名）：避免断言扫描误报
OK_OTHER |= {"豹文刀", "豹文辽", "苗刀"}

def scan_assert(text):
    """返回断言型、不在白名单内的名称命中（高信噪比红单）。"""
    out, seen = [], set()
    for m in ASSERT.finditer(text):
        tok = m.group(1)
        if tok in (hero | jin | gear | baowu | CITIAO) or tok in OK_OTHER:
            continue
        if len(tok) < 2:
            continue
        pre = text[max(0, m.start() - 8):m.start()]
        if QUOTE_MARK2.search(pre):
            continue
        near = text[max(0, m.start() - 25):m.end() + 25]
        if not KIND.search(near):
            continue
        if tok in seen:
            continue
        seen.add(tok)
        ctx = text[max(0, m.start() - 40):m.end() + 30].replace("\n", " ")
        out.append({"tok": tok, "trigger": m.group(0)[:6], "ctx": ctx})
    return out

# ---------------- 文档读取 ----------------
def doc_text(f):
    doc = Document(f)
    t = "\n".join(p.text for p in doc.paragraphs)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                t += "\n" + cell.text
    return t

def baowu_assertions(text):
    out = set()
    for p in (r"([\u4e00-\u9fff]{2,5})[（(]宝物[)）]",
              r"宝物[名叫做是为:：]?\s*[「『]?([\u4e00-\u9fff]{2,5})(?=[，。、）」\s])",
              r"(?:为|是|叫|即|：|:)\s*[「『]?([\u4e00-\u9fff]{2,5})宝物",
              r"(?:携带|带)[「『]?([\u4e00-\u9fff]{2,5})[」』]?宝物",
              r"([\u4e00-\u9fff]{2,5})宝物(?=[，。、）」\s])"):
        for m in re.finditer(p, text):
            out.add(m.group(1))
    return out

def check_regression(text):
    """B 回归：只统计非引用的错名形态（引用型旧名不计入）。"""
    res = {}
    for w in WRONG:
        if w in WRONG_STRICT:
            n = count_assertion(text, w, WRONG_STRICT[w])
        else:
            n = count_assertion(text, w)
        if n:
            res[w] = n
    hits = [p for p in EST_PATTERNS if p in text]
    if hits:
        res["establish_程昱"] = hits
    return res

# ---------------- 主流程 ----------------
SETS = []
if ONLY in ("both", "full"):
    SETS.append(("完整版", sorted(glob.glob(REP + "/*_完整学习报告.docx"))))
if ONLY in ("both", "1s"):
    SETS.append(("一秒版", sorted(glob.glob(REP + "/*_逐帧深度学习报告_1秒版.docx"))))

report = {}
gate_fail = []

for label, files in SETS:
    broken, regr, assert_hits, bao, cit, opent = [], {}, {}, {}, {}, {}
    for f in files:
        bn = os.path.basename(f)
        try:
            text = doc_text(f)
        except Exception as ex:
            broken.append([bn, str(ex)])
            continue
        rg = check_regression(text)
        if rg:
            regr[bn] = rg
        sa = scan_assert(text)
        if sa:
            assert_hits[bn] = sa
        sb = sorted(x for x in baowu_assertions(text)
                    if x not in baowu and x not in BAOWU_PROSE)
        if sb:
            bao[bn] = sb
        sc = sorted(x for x in set(re.findall(r"【([\u4e00-\u9fff]{2,5})】", text))
                    if x not in baowu and x not in CITIAO)
        if sc:
            cit[bn] = sc
        oh = [t for t in OPEN_TERMS if t in text]
        if oh:
            opent[bn] = oh

    ok_count = (len(files) == 51)
    if not ok_count:
        gate_fail.append(f"{label} 文件数 {len(files)}≠51")
    if broken:
        gate_fail.append(f"{label} 损坏 {len(broken)} 份")
    if regr:
        gate_fail.append(f"{label} 回归残留 {len(regr)} 份")

    report[label] = {"count": len(files), "broken": broken,
                     "regression_residual": regr, "assert_offlist": assert_hits,
                     "baowu_suspect": bao, "citiao_suspect": cit, "open_terms": opent}

    print("=" * 70)
    print(f"【{label}】文件 {len(files)}/51   损坏 {len(broken)}")
    print(f"  A 完整性            : {'✅' if ok_count and not broken else '❌'} " +
          (f"齐全 {len(files)}/51" if ok_count else f"数量异常 {len(files)}/51"))
    print(f"  B 已知修复回归残留 : {len(regr)} 份 " + ("❌ BLOCKING" if regr else "✅ =0（引用型旧名已排除）"))
    for k, v in list(regr.items())[:12]:
        print(f"      - {k}: {v}")
    print(f"  C 断言型非白名单红单: {sum(len(v) for v in assert_hits.values())} 条 / {len(assert_hits)} 份 (顾问级)")
    for bn, v in list(assert_hits.items())[:12]:
        for x in v:
            print(f"      「{x['tok']}」 ({x['trigger']})  {bn[:24]}  例:{x['ctx'][:46]}")
    print(f"  D 宝物名疑似 {sum(len(v) for v in bao.values())} 条 / 词条疑似 {sum(len(v) for v in cit.values())} 条")
    print(f"  E 待核实项命中     : {len(opent)} 份 {list(opent.items())[:3]}")

gate_ok = not gate_fail
report["gate_ok"] = gate_ok
report["gate_fail"] = gate_fail
report["whitelist"] = {"hero": len(hero), "jineng_full": len(jin),
                       "gear": len(gear), "baowu": len(baowu), "citiao": len(CITIAO)}

print("=" * 70)
if gate_ok:
    print(">>> 交付门槛: ✅ 通过（51+51 齐全 / 0 损坏 / 已知清零回归项=0）")
else:
    print(">>> 交付门槛: ❌ 未通过：" + "; ".join(gate_fail))
json.dump(report, open(BASE + "/qc_gate_report.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("[完成] 写出 qc_gate_report.json")
