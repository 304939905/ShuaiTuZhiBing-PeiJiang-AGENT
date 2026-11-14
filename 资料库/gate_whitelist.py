# -*- coding: utf-8 -*-
"""
白名单闸门（gate_whitelist.py）
================================
子智能体产出 逐帧判读 JSON 之后、渲染 docx 之前，强制跑本脚本：

  对 JSON 里「该写实体名的位置」（阵容描述 desc / summary.visual_only /
  comparison.new）做本地官方白名单核验。凡是不在白名单、且不是已知黑话/
  兵种特性/宝物词条/常见散文词的 token，判定为「OCR/幻觉编造」，
  默认只报告；加 --apply 时把位置槽/队伍三元里捕获到的编造名直接改写为
  「无法识别（OCR存疑）」，从根本上阻断"编一个像真的词"漏进报告。

用法：
  python gate_whitelist.py 资料库/hzh_frame_json/某视频.json [--apply] [--report out.txt]
  python gate_whitelist.py --all            # 扫全部 *frame_json/*.json
  python gate_whitelist.py --all --apply    # 扫全部并就地改写

白名单规模：武将428 / 战法1127(完整库) / 宝物114（与 VERIFY_REPORT 一致，战法改用 official_jineng_names_full.json 全量）。
"""
import json, os, re, sys, glob

BASE = r"D:\Desktop\shandou\资料库"

def lj(p):
    with open(os.path.join(BASE, p), encoding="utf-8") as f:
        return json.load(f)

# ---------- 白名单 ----------
hero = set(lj("official_hero_names.json")["names"]) | set(h["name"] for h in lj("hero.json"))
ext = lj("official_jineng_names_ext.json")
full = lj("official_jineng_names_full.json")
skilldb = lj("official_skill_db.json")
skill = set(full["names"]) | set(ext["names"]) | set(lj("official_jineng_names.json")["names"]) | \
        set(s.get("name", "") for s in lj("jineng_list.json")) | set(skilldb["skills"].keys())
# 武将自带战法（藏在 hero_extra.json 的 methodName* 字段，jineng_list 不含）
for h in lj("hero_extra.json"):
    if isinstance(h, dict):
        for k in ("methodName", "methodName1", "methodName2", "methodName3"):
            v = h.get(k)
            if isinstance(v, str) and v.strip():
                skill.add(v.strip())
gear = set(g["name"] for g in lj("gear_id.json")
           if isinstance(g, dict) and "name" in g) | set(lj("official_gear_names.json")["names"])
affix = set(g.get("skillName", "") for g in lj("gear_id.json")
            if isinstance(g, dict) and g.get("skillName"))

# 已知合法但不在白名单（黑话/简称/兵种特性/宝物词条/队名/术语）——不标记
SLANG = set(("木鹿 斩龙 关兴张苞 张苞 汉董卓 八旗铺路队 列阵文韬 出奇疾汗 水镜 "
             "利刃 文韬 禁卫 怯战 挫锐 无畏 列阵 近战 固阵 勇毅 守备 披甲 长枪 长柄 "
             "重步 直射 散射 弩弓 死士 长弓 扰后 出奇 齐射 奔袭 倏忽 玄襄 铁意 铁壁 "
             "护主 据守 灵动 戎马 疾行 迂回 殿后 侧击 死战 擅兵 反击 连战 枪阵 剑盾 "
             "斧钺 火辎 火攻 水攻 风系 毒系 伏击 举盾 犹豫 混乱 暴走 围困 援护 挑衅 "
             "先手 洞察 分兵 战必 断金 陷阵 骁锐 天资 筹算 英勇 坚忍 夺魄 破敌 掩日 "
             "竹林七贤 竹林七贤队 魏智 小魏骑 碰瓷 凌统 萌新玩家 曹仁 郭嘉 荀彧 "
             "平民 平民玩家 白板 白板号 月卡党 零氪 低氪 低充值").split())
KNOWN = hero | skill | gear | affix | SLANG

# 自举合法语料：从已人工闭环的报告中学习"真实但不在官方白名单"的词
# （如部分自带战法/队名/地理UI词/玩家名），避免闸门对干净报告误报。
# 运行：python gate_whitelist.py --learn <已闭环报告 json...>
EXTRA = set()
_extra_path = os.path.join(BASE, "gate_extra_known.json")
if os.path.exists(_extra_path):
    try:
        EXTRA = set(lj("gate_extra_known.json"))
    except Exception:
        EXTRA = set()
KNOWN = KNOWN | EXTRA

# 散文/非实体停用词（比较段纠错举例、标题引语、常见功能词等），不标记
STOP = set(("平民 秘密 中文 四分之一 商飞 要塞 药赛 八旗 八级 徐华 数三项 "
            "千万别拆了 萌新玩家 玩魏智 并展示荀彧 曹仁小魏骑 徐庶宁元刀 凌统碰瓷 "
            "嵇康竹林七 张飞 徐晃 蜀三相 郭嘉 荀彧 曹仁 凌统 刘伶 阮籍 嵇康 "
            "宁元刀 甘宁 卫瓘 徐庶 朱儁 刘关张 小魏骑 魏骑 骑 都能 战队 队伍 "
            "车队 压秒 连捷 夷陵 决战 海棠 海棠中 诗CPU 小诗 天天涨停 河南 "
            "同盟 赛季 区服 势力值 坐标 瞭望塔 视野 集火 菜刀 物理刀 法刀 "
            "控制 击败 胜利 占领 战果 聊天记录 战术沟通 后手 空城 斩龙 替换 "
            "选项 剩余 阵容 核心队 指出 明确 确认 展示 显示 触发 利用 组织 "
            "打开 个人资料 盟友 曹操前锋 司马懿法 王异刀 张春华控 曹彰春华 "
            "敌方为 报确认 张绣胜 全歼程昱 同支 吕蒙队 文鸯与 司马懿法刀 "
            "都能 替换 黄盖刀 正始之变 知己知彼 侵掠如火 及锋而试 汜水关 "
            "皇裔流离 谋议宏图 全军突击 安抚军心 侵掠 火/及").split())

# ---------- 抽取模式（仅高信号实体位置，高精度） ----------
POS = r"(大营|中军|前锋|主将|副将|先锋|队长|搭档)"
NAME = r"[一-鿿]{2,4}"
pos_pat = re.compile(POS + r"[：: ]*(" + NAME + r")")
team_pat = re.compile(r"(" + NAME + r")[＋+]" + r"(" + NAME + r")"
                      r"(?:[＋+]" + r"(" + NAME + r"))?")
# 仅抓「括号内斜杠/顿号分隔」的战法/宝物清单（清单必用分隔符），避免抓散文
paren_pat = re.compile(r"[（(「]([^（）()「」]*[／/、][^（）()「」]*)[）)」]")


def contains_known(tok):
    # 功能词+名 复合（敌军吕布/敌方曹操/胜张辽/败于典韦/展示祝融/确认甘宁…）：
    # 只要 token 内含已知实体子串（>=2字），视为"真实体带修饰语"，跳过，不误报。
    if tok in KNOWN:
        return True
    for i in range(len(tok)):
        for j in range(i + 2, len(tok) + 1):
            if tok[i:j] in KNOWN:
                return True
    return False


def extract(text):
    out = []
    for m in pos_pat.finditer(text):
        t = m.group(2)
        if t and t not in STOP and not contains_known(t):
            out.append((t, "pos"))
    for m in team_pat.finditer(text):
        for g in m.groups():
            if g and g not in STOP and not contains_known(g):
                out.append((g, "team"))
    for m in paren_pat.finditer(text):
        for tok in re.split(r"[／/＋+\s、,，]", m.group(1)):
            tok = tok.strip()
            if 2 <= len(tok) <= 4 and re.fullmatch(NAME, tok) and tok not in STOP and not contains_known(tok):
                out.append((tok, "paren"))
    return out


# 仅在这些路径下抽取（高信号：当前声明的实体，而非旧报告纠错散文）
def in_scope(path):
    p = " > ".join(str(x) for x in path)
    if "visual_only" in p:
        return True
    if path and path[-1] == "desc":
        return True
    if "comparison" in p and p.rstrip().endswith("new"):
        return True
    return False


META = ("limit", "limitation", "note", "correction", "疑", "存疑", "ocr",
        "待确", "无法识别", "不确定", "未知")

# 边界伪影：team/pos 抽取常把相邻功能词粘连进来（"支黄盖"→去首字=黄盖∈白名单）。
# 若 token 去掉首/尾一字后命中白名单，判定为伪影跳过。
def is_artifact(tok):
    if len(tok) >= 3:
        if tok[1:] in KNOWN or tok[:-1] in KNOWN:
            return True
        if len(tok) >= 4 and tok[1:-1] in KNOWN:
            return True
    return False


def is_meta(parts):
    return any(isinstance(p, str) and any(k in p for k in META) for p in parts)


def walk(o, path, res):
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, path + [k], res)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, path + [f"[{i}]"], res)
    elif isinstance(o, str):
        if not in_scope(path):
            return
        for tok, kind in extract(o):
            res.append((tok, kind, " > ".join(str(p) for p in path[-3:]),
                        o[max(0, o.find(tok) - 25):o.find(tok) + len(tok) + 25]))


def gate_one(fp, do_apply):
    with open(fp, encoding="utf-8") as f:
        raw = f.read()
    d = json.loads(raw)
    res = []
    walk(d, [], res)
    flagged = {}
    for tok, kind, path, snip in res:
        if tok in KNOWN:
            continue
        if is_artifact(tok):
            continue
        scope = "META" if is_meta(path.split(" > ")) else "BODY"
        flagged.setdefault(tok, []).append((kind, path, snip, scope))
    body_flags = {t: v for t, v in flagged.items() if any(x[3] == "BODY" for x in v)}
    if not body_flags:
        return fp, [], flagged
    applied = []
    if do_apply:
        new_raw = raw
        for tok in body_flags:
            kinds = set(x[0] for x in body_flags[tok] if x[3] == "BODY")
            if kinds & {"pos", "team"}:
                new_raw = new_raw.replace(tok, "无法识别（OCR存疑）")
                applied.append(tok)
        if new_raw != raw:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(new_raw)
    return fp, applied, flagged


def main():
    args = sys.argv[1:]
    do_apply = "--apply" in args
    do_all = "--all" in args
    do_learn = "--learn" in args
    args = [a for a in args if a not in ("--apply", "--all", "--learn")]
    if do_all:
        files = sorted(glob.glob(os.path.join(BASE, "*frame_json", "*.json")))
    else:
        files = args
    # 去 --report 参数
    rep_path = None
    if "--report" in args:
        i = args.index("--report")
        rep_path = args[i + 1] if i + 1 < len(args) else None
        args = args[:i]
        files = args
    if not files:
        print("用法: python gate_whitelist.py <json...> [--apply] | --all [--apply] [--learn] [--report x.txt]")
        return
    rep = []
    total_flag = 0
    total_apply = 0
    learn_set = set()
    for fp in files:
        fp, applied, flagged = gate_one(fp, do_apply)
        body = {t: v for t, v in flagged.items() if any(x[3] == "BODY" for x in v)}
        if do_learn:
            learn_set |= set(body.keys())
        if not body:
            rep.append(f"  ✅ {os.path.basename(fp)}  全绿（无编造实体）")
            continue
        total_flag += len(body)
        total_apply += len(applied)
        rep.append(f"  ⚠️  {os.path.basename(fp)}  编造实体 {len(body)} 个"
                   + (f"  已改写 {len(applied)} 个" if applied else ""))
        for tok, occ in body.items():
            kinds = "/".join(sorted(set(x[0] for x in occ)))
            rep.append(f"      · {tok}  [{kinds}]  出现 {len(occ)} 次")
            for kind, path, snip, scope in occ[:2]:
                rep.append(f"          {path}: …{snip}…")
    rep.insert(0, f"白名单闸门：武将{len(hero)}/战法{len(skill)}/宝物{len(gear)} | "
                  f"扫描 {len(files)} 文件 | 编造实体 {total_flag} | 改写 {total_apply}")
    out = "\n".join(rep)
    print(out)
    if rep_path:
        with open(rep_path, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"\n报告已写 {rep_path}")
    if do_learn and learn_set:
        with open(_extra_path, "w", encoding="utf-8") as f:
            json.dump(sorted(learn_set), f, ensure_ascii=False, indent=1)
        print(f"\n--learn：已自举 {len(learn_set)} 个合法词到 {_extra_path}")


if __name__ == "__main__":
    main()
