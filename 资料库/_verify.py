# -*- coding: utf-8 -*-
import json, re, os

BASE = os.path.dirname(os.path.abspath(__file__))

def load(p):
    return json.load(open(os.path.join(BASE, p), encoding="utf-8"))

# ---------- whitelists ----------
HERO = set(load("official_hero_names.json")["names"])
for h in load("hero.json"):
    if isinstance(h, dict) and h.get("name"):
        HERO.add(h["name"])

JINENG = set(load("official_jineng_names_ext.json")["names"])
for j in load("jineng_list.json"):
    if isinstance(j, dict) and j.get("name"):
        JINENG.add(j["name"])
he = load("hero_extra.json") if os.path.exists(os.path.join(BASE, "hero_extra.json")) else []
for h in he:
    if isinstance(h, dict):
        for k in ("methodName", "methodName1", "methodName2"):
            v = h.get(k)
            if isinstance(v, str) and v.strip():
                JINENG.add(v.strip())

GEAR = set(load("official_gear_names.json")["names"])
GW = set()
for g in load("gear_id.json"):
    if isinstance(g, dict):
        if g.get("name"):
            GEAR.add(g["name"])
        if g.get("skillName"):
            for w in re.split("[；、，,]", g["skillName"]):
                w = w.strip()
                if w:
                    GW.add(w)

ALL = HERO | JINENG | GEAR | GW
NAMES_SORTED = sorted(ALL, key=len, reverse=True)

# generic game/UI/term stopwords (not entity names)
STOP = set("""中军 大营 前锋 战报 队伍 画面 显示 确认 展示 武将 战法 宝物 词条 锻造 立绘 阵容 面板 结算
克制 攻城 驻守 调动 探路 留守 分兵 爆兵 行军 开荒 压秒 卡免 主战法 兵种 配速 红度 满红 战法位
要塞 关卡 分城 同盟 资源 武勋 士气 土气 坐标 迁城 出征 守军 伤兵 体力 兵力 胜利 失败 平局 战斗 回合
空位 详情 列表 页面 界面 数据 数值 效果 机制 技能 主动 指挥 追击 被动 防御 攻击 谋略 速度 属性 距离
发动 概率 加成 减伤 增伤 恢复 治疗 伤害 策略 物理 普攻 规避 缴械 混乱 犹豫 挑衅 恐慌 动摇 风暴 燃烧
眩晕 怯战 前锋位 中军位 大营位 音近 误识 误听 质量 转写 片段 段落 语音 字幕 硬字幕 口语 方言 表述
叙述 描述 说明 解释 提及 标注 注释 补充 预告 结构 层次 阶段 迭代 反复 变化 过程 情况 状态 条件 标准
形式 类型 来源 依据 参考 对照 对比 差异 一致 冲突 矛盾 错误 修正 核实 确认 证明 显示 表明 呈现 出现
获取 获得 达成 累计 递进 递增 提升 提高 降低 下降 增加 减少 展示 罗列 列举 记录 统计 详情 概览 总览
未 无 不 非 否 未展示 未解释 未给出 未提供 未展开 未收录 未确认 无法 难以 不能 不可 没法 没法辨认
作者 玩家 同盟 敌方 我方 友方 对方 己方 本方 蓝方 红方 左方 右方 上方 下方 前方 后方 多方 单 双
主队 副队 一队 二队 三队 四队 五队 六队 七队 八队 满编 残兵 完整 部分 全部 整体 局部 具体 精确 明确
真实 实际 可能 疑似 大约 大概 约 近 余 整 全 各 每 该 此 这 那 某 另 其 同 异 第 初 终 末 首 尾
体系 流派 玩法 思路 方案 配置 组合 搭配 定位 角色 核心 关键 主力 输出 辅助 控场 肉盾 坦克 爆发 续航
以及 及其 之中 之内 之外 之间 以上 以下 以前 以后 以内 以外 之前 之后 之际 之世 之变 之勉 之鉴 之利
为文鸯 与荀彧 于同一支 董卓击败 典韦负于 击败夏侯惇 负于典韦 负于夏侯惇 负于曹彰 兵种选择 含每名武将
含宝物 含可选 含敌方 含友盟 含多支 含多方 含低级 含完整 含三 含二 选新郑 选木鹿 选择木鹿 心战为上
马谡阵亡 马谡的 马谡带 马妹 马炎 马云禄 云禄 禄 禄队 禄带 祝融 融体系 融夫人 甘宁 宁带 宁队 文鸯 鸯带
张辽 辽带 曹纯 纯带 张绣 绣带 司马炎 司马懿 司马队 庞统 刘备 备带 曹操 操带 操队 吕蒙 蒙带 周瑜 陆逊
程昱 昱带 孙坚 孙权 孙策 孙尚香 黄盖 盖刀 关银屏 关妹 关兴 张机 机带 貂蝉 蔡文姬 甄洛 洛 何太后 太后
董卓 卓带 朱儁 儁 魏延 延 姜维 维 戏志才 志才 王业 业 乐进 进 吴夫人 夫人 刘禅 禅 郭嘉 嘉 郭图 图
黄忠 忠 陆抗 抗 王朗 朗带 郝昭 昭 戏 张奂 奂 冯媛 媛 卫瑠 瑠 刘徽 徽 辛宪英 宪英 刘伶 伶 冯绲 绲
阮籍 籍 嵇康 康 于吉 吉 蔡邕 邕 张苞 苞 卫瓘 瓘 荀彧 彧 张飞 飞 张昭 昭 于禁 禁 高顺 顺 兀突骨 骨
木鹿大王 鹿 大乔 小乔 乔 灵帝 帝 魏智 智 蜀智 智 天帝 帝 凤年 年 王异 异 严颜 颜 甄洛 洛 马超 超
马谡 谡 曹操 操 刘备 备 司马 马 关羽 羽 关 张 赵 黄 魏 蜀 吴 汉 晋 群 吕 孙 甘 太 小 大 三 四 五 六 七 八 九 十
""".split())

# single-char faction/era stopwords
STOP |= set("魏蜀吴汉晋群蛮羌胡匈鲜卑氏羯賨板楯夷戎狄貊倭夫余高句丽乌桓丘力居屠各落部帐栅垒寨关渡津桥道山路水河江湖海原野林谷岭岩石城墙门楼台寺庙宫殿阁亭轩斋庵庐坞壁屯田仓库坊市街巷铺店馆驿站渡口港湾澳渚洲岛礁滩沙漠荒芜废墟遗迹址冢墓碑铭刻石经卷书简册图谱录记志传说话语言文字符号数字点线面体形色光影声音乐歌舞戏剧画像雕塑像偶俑器物具工具械甲胄盔盾剑刀枪矛戟斧钺弓弩箭矢弹炮车马舟船舰辇舆轿骑乘驾驭驯牧猎渔农商学兵民官吏将帅王侯君臣后妃嫔姬妾奴隶婢仆徒众卒兵丁壮勇士侠盗贼寇匪奸佞忠良贤能智勇仁义礼信廉耻孝悌忠恕温良恭俭让谦和平安宁静逸闲雅俗朴拙巧妙灵慧愚钝狂傲骄奢淫逸贪婪嗔痴恨怨怒悲喜乐哀惧惊疑惑迷觉悟醒梦幻虚实真假善恶美丑好坏优劣强弱盛衰兴亡存亡生死老幼少长男女父母子女兄弟姐妹夫妻儿孙曾玄祖宗族姓氏名讳字号谥庙号年号代纪元朔历法术道德儒释道佛仙神鬼妖魔怪灵精兽禽虫鱼草木花果谷蔬粮食酒茶药毒香脂粉黛妆饰服衣冠带履鞋袜巾帽佩环珠玉金银铜铁锡铅汞石玉宝藏玩器皿盘碗杯壶瓶罐盒匣箱笼篮筐篓桶盆缸锅灶鼎钟鼓磬琴瑟笛箫笙竽埙锣钹铃铙铎角笳号旗旌旄麾幢盖伞扇杖节符印玺章券契约盟誓诰敕诏令旨檄书札牍简策典籍经史子集诗词歌赋文章碑铭颂赞箴规谏诫训诰命论说辩议疏奏表启笺帖札记杂录琐闻逸事旧闻新闻消息情报谍报塘报邸报报纸刊物杂志书籍丛书全集选集辑录编纂校勘注疏解释译述评论批点圈阅题跋序引例言后记附录补遗勘误校记索引目录提要摘要概论导言绪论本论结论余论附论补论补记补注补遗补正校补增补删补订补修补考证辨伪辑佚钩沉索隐发微阐幽表微显隐探赜得珠探骊含英咀华披沙拣金去伪存真由表及里去粗取精由浅入深温故知新举一反三触类旁通融会贯通豁然贯通顿开茅塞恍然大悟猛然醒悟幡然悔悟大彻大悟如梦初醒拨云见日重见天日守得云开见月明柳暗花明又一村山重水复疑无路峰回路转豁然开朗开云见日云开雾散烟消云散雨过天晴风平浪静波澜不惊泰然处之安之若素处变不惊临危不惧镇定自若从容不迫稳如泰山坚如磐石不动如山岿然不动纹丝不动屹立不倒傲然挺立昂首挺胸昂首阔步趾高气扬耀武扬威张牙舞爪盛气凌人咄咄逼人气势汹汹汹涌澎湃波涛汹涌惊涛骇浪狂风巨浪疾风骤雨暴风骤雨风雨交加风雨飘摇风雨如晦风雨同舟风雨兼程风雨无阻风雨苍黄风云变幻风云际会风云人物风云之志风云之气风云之变风云突变风云变色风云叱咤风云激荡风起云涌风起云飞风起云蒸风起云布风起云兴风起云合风起云集风起云翔风起云扬")

def decompose(tok):
    found = []
    t = tok
    for n in NAMES_SORTED:
        if n and n in t:
            found.append(n)
            t = t.replace(n, " ")
    chunks = re.findall(r"[一-鿿]{2,}", t)
    resid = [c for c in chunks if c not in STOP and len(c) >= 2]
    return resid, found

# ---------- parse _focus2.txt ----------
results = {}  # video -> {cat: [(orig, resid)]}
cur_video = None
cur_cat = None
with open(os.path.join(BASE, "_focus2.txt"), encoding="utf-8") as f:
    for line in f:
        line = line.rstrip("\n")
        if line.startswith("### "):
            cur_video = line[4:].strip()
            results.setdefault(cur_video, {})
            cur_cat = None
            continue
        m = re.match(r"\s*\[(\S+)\]非白名单:\s*(.*)", line)
        if m:
            cur_cat = m.group(1)
            lst = m.group(2)
            items = re.findall(r"'([^']*)'", lst)
            for it in items:
                resid, found = decompose(it)
                if resid:
                    results[cur_video].setdefault(cur_cat, []).append((it, resid, found))

# ---------- output ----------
out = []
total = 0
for vid, cats in results.items():
    any_resid = False
    lines = []
    for cat, items in cats.items():
        for orig, resid, found in items:
            r = " / ".join(resid)
            lines.append(f"    [{cat}] 原='{orig}' 残片='{r}' 命中库={found}")
            any_resid = True
            total += 1
    if any_resid:
        out.append(f"### {vid}")
        out.extend(lines)

with open(os.path.join(BASE, "_verify_residuals.txt"), "w", encoding="utf-8") as f:
    f.write(f"# 真正残片(剥离官方库名+通用术语后剩余) 共 {total} 条\n")
    f.write("\n".join(out))

print("RESIDUAL COUNT:", total)
print("\n".join(out[:120]))
