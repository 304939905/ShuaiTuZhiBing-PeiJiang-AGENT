# -*- coding: utf-8 -*-
"""扫描 1秒版 中的纯杂质行，生成候选删除清单。
判定规则（保守，只标高置信）：
  类别 A 片尾广告/引导：玩转率土就看北冥 / 关注引导 / 点赞关注 / 三连 / 双击 / 关注UP
  类别 B 纯过渡/黑屏/水印：整行只有 黑屏/过渡/水印/logo 且无实质内容
  类别 C 粉丝ID/头像装饰：画面中出现粉丝 ID/头像水印，无游戏内容信息
  类别 D 下期预告：片尾"下期预告/下期带来"纯预告（不含实质内容）
排除：行内含 武将/战法/卡/队伍/阵容/资源/伤害/兵力/截图内容 等实质词 → 视为投稿内容保留
用法: python scan_pure_noise.py
输出: 资料库/_noise_candidates.json + 控制台汇总
"""
import sys, re, json, os
from collections import Counter, defaultdict
sys.path.insert(0, "D:/WorkBuddyData/python-env/shandou/Lib/site-packages")
from docx import Document

ROOT = "D:/Desktop/shandou/报告库"
SUB = ["旧56项目", "开荒", "海之呼唤", "赛季"]

# 高置信杂质特征（出现即疑似）
AD_TRAIL = ["玩转率土", "就看北冥", "关注引导", "点赞关注", "一键三连", "三连", "双击点赞",
            "关注UP", "关注 up", "订阅频道", "喜欢就", "别忘了关注", "记得关注", "多多关注",
            "多多点赞", "支持下", "支持一下", "点个关注", "点个赞"]
PURE_TRANS = ["纯黑屏", "黑屏过渡", "黑屏结束", "过渡帧", "过渡画面", "纯过渡", "黑屏，", "画面黑屏"]
WATERMARK = ["水印", "logo", "LOGO", "水印帧"]
FAN_DECOR = ["粉丝ID", "粉丝id", "头像为", "粉丝头像", "ID水印", "id水印"]
NEXT_EP = ["下期预告", "下期带来", "下期再见", "下期点评", "敬请期待", "预告：", "下期见"]

# 实质内容词（行内出现任一 → 不判为纯杂质）
CONTENT_WORDS = ["武将", "战法", "队伍", "阵容", "卡", "资源", "伤害", "兵力", "截图", "评论",
                 "战报", "属性", "效果", "触发", "发动", "兵种", "土地", "城池", "行军", "攻打",
                 "开荒", "赛季", "势力", "战斗", "面板", "数值", "技能", "普攻", "策略", "攻击",
                 "防御", "谋略", "速度", "体系", "搭配", "配将", "打法", "克制", "实战", "测试",
                 "评分", "点评", "分析", "讲解", "介绍", "对比", "总结", "阵容详情", "立绘"]
# 画面描述词（行内含这些词说明在描述画面内容，不是纯杂质）
SCENE_WORDS = ["画面", "镜头", "显示", "展示", "出现", "弹出", "可见", "字幕", "标题", "大字",
               "红字", "黄字", "白字", "界面", "详情页", "面板", "视频"]

def classify(line):
    """返回 (category, matched_pattern) 或 None。保守：只要行内有实质词就返回 None。"""
    l = line.strip()
    if not l or len(l) < 4:
        return None
    # 先看是否含实质内容 → 保留
    for w in CONTENT_WORDS:
        if w in l:
            return None
    for w in SCENE_WORDS:
        if w in l:
            return None
    # 时间锚行（00:00 或 [00:00] 开头）若含实质词已排除，剩余多为结构行
    for cat, pats in [("A广告引导", AD_TRAIL), ("B过渡黑屏", PURE_TRANS),
                      ("C水印logo", WATERMARK), ("D粉丝装饰", FAN_DECOR),
                      ("E下期预告", NEXT_EP)]:
        for p in pats:
            if p in l:
                return cat, p
    return None

results = defaultdict(list)  # file -> [{line, cat, pat, para_idx}]
total = Counter()
for sub in SUB:
    d = f"{ROOT}/{sub}/逐帧1秒版"
    if not os.path.isdir(d):
        continue
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".docx"):
            continue
        f = f"{d}/{fn}"
        try:
            doc = Document(f)
        except Exception as ex:
            print("ERR", f, ex, file=sys.stderr)
            continue
        for idx, p in enumerate(doc.paragraphs):
            r = classify(p.text)
            if r:
                cat, pat = r
                results[f"{sub}/{fn}"].append({
                    "idx": idx, "line": p.text.strip(), "cat": cat, "pat": pat})
                total[cat] += 1

json.dump(results, open("D:/Desktop/shandou/资料库/_noise_candidates.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("=== 杂质行统计 ===")
for k, v in total.most_common():
    print(f"  {k}: {v} 行")
nfiles = sum(1 for v in results.values() if v)
print(f"涉及文件: {nfiles} / 74")
print("\n=== 逐文件明细（前40条） ===")
cnt = 0
for fn, rows in sorted(results.items()):
    for r in rows:
        cnt += 1
        if cnt > 40:
            break
        print(f"[{r['cat']}] {fn[:36]} | {r['line'][:90]}")
    if cnt > 40:
        print("... 更多见 _noise_candidates.json")
        break
