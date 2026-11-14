# -*- coding: utf-8 -*-
import json, os, re, glob

BASE = r"D:\Desktop\shandou"
RES = os.path.join(BASE, "资料库")

# ---------- 加载白名单 ----------
def load_names(path):
    if not os.path.exists(path):
        return set()
    d = json.load(open(path, encoding="utf-8"))
    s = set()
    rows = d if isinstance(d, list) else (d.get("data") or d.get("list") or [])
    if isinstance(d, dict) and not rows:
        # maybe {name:value}
        for k, v in d.items():
            if isinstance(v, str):
                s.add(k); s.add(v)
        return s
    for x in rows:
        if isinstance(x, str):
            s.add(x)
        elif isinstance(x, dict):
            for k in ("name", "hero", "jineng", "skill", "gear", "title", "realname"):
                if k in x and isinstance(x[k], str):
                    s.add(x[k]); break
    return s

hero = load_names(os.path.join(RES, "official_hero_names.json"))
jineng = load_names(os.path.join(RES, "official_jineng_names_ext.json"))
gear = load_names(os.path.join(RES, "official_gear_names.json"))
gear_base = load_names(os.path.join(RES, "official_gear_names.json"))
allnames = hero | jineng | gear

print("白名单规模 武将=%d 战法=%d 宝物=%d 合并=%d" % (len(hero), len(jineng), len(gear), len(allnames)))

# ---------- 历史已知错误 token（OCR/音译误识） ----------
BAD = ["勞駮", "機勢", "大桐琴", "母儀逐夢", "鶴翼", "遊歌天亮", "臻級真剛",
       "鴉鳴靈動", "仿傑熱淬", "傑熱淬", "張遼", "劉徽", "穩侯襲為", "稳侯袭为"]

# ---------- 常见非专有名词豁免 ----------
EXCLUDE = set("""率土之滨 抖音 玩家 视频 作者 本期 实战 战报 阵容 配置 伤害 兵力 触发 发动 回合
大营 中军 前锋 主将 副将 队伍 体系 组合 称号 属性 谋略 攻击 防御 速度 战法 宝物 词条
自带 学习 可学 通用 专属 赛季 征服 试师 开荒 战斗 结算 胜利 失败 进攻 防守 输出 控制 辅助
核心 关键 重要 常见 推荐 最强 神队 平民 新手 萌新 四星 五星 三星 满红 白板 觉醒 进阶 强化
锻造 打造 骁锐 天资 英勇 稳固 灵动 熟虑 真刚 元戎 钜黍 大将 别鸣 游飘 彤素 大柯斧 词条
加伤 减伤 增伤 奶量 爆发 续航 坦度 容错 节奏 上限 下限 版本 环境 主流 冷门 黑科技 碰瓷
豹文刀 魏智 蜀之智 吴步 群骑 晋骑 法刀 菜刀 流氓 网红 钢板 嘟嘟 鬼吕 衡轭 形兵 双减
百业争鸣 北伐兴汉 旗本八骑 竹林七贤 宁元刀 母仪浮梦 焰焚箕轸 轻侠妄为 其疾如风 威震遁逃
乘胜追击 盛气横凌 击势 枭雄 虎豹督军 攻其不备 长兵方阵 声东击西 乘间击隙 避锐治气 合纵连横
百战无怯 反计之策 神赏 攻其 十面 一夫 浑水 妖术 战必 断金 磐阵 无心 桃园 三军 知己 红颜
措手不及 掎角之势 穷追猛打 钝兵挫锐 危崖困军 鸟云山兵 鹤翼 单骑 孙膑 始计 浑水摸鱼
""".split())

# ---------- 繁体字集合（报告自身不应残留） ----------
TRAD = set("萬與於麼隊戰時職將軍國號後對從處點進關開試師勝該當無總網頁說話實戰員單為個這義張強當頁開擊滅殺統裝載歷現環圖種類經許類點對導專轉輕錢銀銅鐵馬驗證識讀產條約統個師軍頁試張華飛雲遠門島醜專傳僅餘兩來")

CJK = lambda s: "".join(ch for ch in s if "\u4e00" <= ch <= "\u9fff")

# ---------- 提取候选名 ----------
hero_pat = re.compile(r"(?:大营|中军|前锋|主将|副将|武将)?\s*([\u4e00-\u9fff]{2,4})(?:\s*[、+，,]|\s*[（(]|\s*队|\s*体系|\s*组合)")
skill_pat = re.compile(r"([\u4e00-\u9fff]{2,6})(?:\s*[+＋]|\s*S\d?|\s*A\b|\s*B\b|\s*C\d?|\s*级|\s*[（(]|\s*【)")
gear_pat = re.compile(r"([\u4e00-\u9fff]{2,4})(?:\s*宝物|\s*·\s*词条|\s*词条)")

def collect_text(o):
    if isinstance(o, str):
        return o
    if isinstance(o, list):
        return " ".join(collect_text(x) for x in o)
    if isinstance(o, dict):
        return " ".join(collect_text(v) for v in o.values())
    return str(o)

def check_one(p, frames_root):
    d = json.load(open(p, encoding="utf-8"))
    title = d.get("video_title", os.path.basename(p))
    out = {"title": title, "file": os.path.basename(p)}
    # 结构
    need = {"video_title","video_id","frames_dir","duration_s","frame_count","sheet_count",
            "resolution","report_date","summary","timeline","comparison","frame_only_value",
            "limitations","glossary","sources"}
    miss = need - set(d.keys())
    out["struct_miss"] = sorted(miss)
    # 帧引用
    fd = d.get("frames_dir", "")
    fdir = os.path.join(frames_root, fd) if fd else ""
    missing_frames = []
    nframes = 0
    for seg in d.get("timeline", []):
        for fr in seg.get("frames", []):
            nframes += 1
            fn = fr.get("file", "")
            if fdir and not os.path.exists(os.path.join(fdir, fn)):
                missing_frames.append(fn)
    out["frames_ref"] = nframes
    out["frames_missing"] = missing_frames
    # 文本
    text = collect_text(d)
    # 繁体
    trad_hits = []
    for ch in set(text):
        if ch in TRAD:
            idx = text.find(ch)
            trad_hits.append((ch, text[max(0,idx-12):idx+12]))
    out["trad"] = trad_hits
    # 历史黑名单
    bad_hits = [b for b in BAD if b in text]
    out["bad"] = bad_hits
    # 候选名 vs 白名单
    cands = set()
    for pat in (hero_pat, skill_pat, gear_pat):
        for m in pat.finditer(text):
            cands.add(m.group(1))
    unknown = set()
    for c in cands:
        if c in EXCLUDE:
            continue
        if c in allnames:
            continue
        # 去除前后标点噪音
        unknown.add(c)
    out["unknown_names"] = sorted(unknown)
    return out

LOGF = open(os.path.join(RES, "FINAL_AUDIT_RAW.txt"), "w", encoding="utf-8")
print("白名单规模 武将=%d 战法=%d 宝物=%d 合并=%d" % (len(hero), len(jineng), len(gear), len(allnames)))

jobs = [
    ("海之呼唤", os.path.join(RES, "hzh_frame_json"), os.path.join(BASE, "海之呼唤_frames_dense_1s")),
    ("赛季", os.path.join(RES, "saiji_frame_json"), os.path.join(BASE, "赛季_frames_dense_1s")),
]

allout = []
for label, jdir, froot in jobs:
    print("\n########## %s (%d json) ##########" % (label, len(glob.glob(jdir+"/*.json"))))
    for p in sorted(glob.glob(jdir + "/*.json")):
        try:
            r = check_one(p, froot)
        except Exception as e:
            print("[ERROR] %s : %s" % (os.path.basename(p), e)); continue
        allout.append(r)
        flag = []
        if r["struct_miss"]: flag.append("结构缺:%s" % r["struct_miss"])
        if r["frames_missing"]: flag.append("缺帧%d:%s" % (len(r["frames_missing"]), r["frames_missing"][:3]))
        if r["trad"]: flag.append("繁体%d" % len(r["trad"]))
        if r["bad"]: flag.append("黑名单:%s" % r["bad"])
        if r["unknown_names"]: flag.append("非白名单候选%d:%s" % (len(r["unknown_names"]), r["unknown_names"][:8]))
        if not flag:
            print("  [OK] %s" % r["title"][:24])
        else:
            print("  [!] %s | %s" % (r["title"][:22], " | ".join(flag)))

# 详细输出非白名单候选/繁体/缺帧 到文件
LOGF.write("===== 详细疑点 =====\n\n")
for r in allout:
    problems = r["struct_miss"] or r["frames_missing"] or r["trad"] or r["bad"] or r["unknown_names"]
    if not problems:
        continue
    LOGF.write("### %s\n" % r["title"])
    if r["struct_miss"]:
        LOGF.write("  结构缺失: %s\n" % r["struct_miss"])
    if r["frames_missing"]:
        LOGF.write("  缺帧(%d): %s\n" % (len(r["frames_missing"]), r["frames_missing"]))
    if r["trad"]:
        for ch, ctx in r["trad"]:
            LOGF.write("  繁体'%s' :: %s\n" % (ch, ctx.replace("\n"," ")))
    if r["bad"]:
        LOGF.write("  黑名单命中: %s\n" % r["bad"])
    if r["unknown_names"]:
        LOGF.write("  非白名单候选名: %s\n" % r["unknown_names"])
    LOGF.write("\n")

LOGF.close()
print("\n完成，详细写入 FINAL_AUDIT_RAW.txt")
