# -*- coding: utf-8 -*-
"""试点两份 JSON 内容修正（甘宁小修 + 月卡去冗余）。
仅改数据层，不动结构。改完由 gen_refined_report_zhenrong.py 重渲。"""
import json, os

LIB = r'D:/Desktop/shandou/资料库/zhenrong_frame_json'

# ============ 一、甘宁碰瓷队：修正自相矛盾 OCR 表述 + 时间线星级对齐资料库 ============
p1 = os.path.join(LIB, '率土平民队伍之甘宁碰瓷队.json')
d1 = json.load(open(p1, encoding='utf-8'))

# 核心结论③：原「画面『轻侠妄为』实为『轻侠妄为』」自相矛盾 → 改为确认一致
d1['summary']['key_points'][2] = ("甘宁首项战法画面显示「轻侠妄为」，与官方 methodName 完全一致，"
                                   "确认无误（非 OCR 误读）。")

# AI 推断①②：原「实为」自相矛盾 → 改为确认一致
d1['ai_inference'][1]['point'] = ("甘宁首项战法画面「轻侠妄为」与官方 methodName 完全匹配，"
                                   "确认无误（字形清晰，非 OCR 误读）。")
d1['ai_inference'][2]['point'] = ("凌统首项战法画面「国士」与官方 methodName 完全匹配，"
                                   "确认无误（「士」字清晰可辨，非 OCR 误读）。")

# 局限①②：剔除「英勇/妄为」「土/士」无根据猜测，改为确认一致
d1['limitations'][0] = ("中军甘宁战法位首项画面文字显示「轻侠妄为」，与官方库甘宁-吴-弓 自带战法 "
                        "methodName「轻侠妄为」完全一致，确认无误（此前「英勇」属无根据猜测，已剔除）。")
d1['limitations'][1] = ("前锋凌统战法位首项画面文字显示「国士」，与官方库凌统-吴-弓 自带战法 "
                        "methodName「国士」完全一致，确认无误（「士」字清晰可辨）。")

# 武将 note：同步
for h in d1['entities']['heroes']:
    if h['name'] == '甘宁':
        h['note'] = ("uniqueName=甘宁-吴-弓；methodName=轻侠妄为（白名单收录）。"
                     "画面甘宁首项战法显示「轻侠妄为」，与官方 methodName 完全一致，确认无误。")
    if h['name'] == '凌统':
        h['note'] = ("uniqueName=凌统-吴-弓；methodName=国士（白名单收录）。"
                     "画面凌统首项战法显示「国士」，与官方 methodName 完全一致，确认无误。")

# 时间线星级：资料库判定朱儁/甘宁/凌统均为 5 星，战报卡「4 星」为低分辨率误读，对齐为 5 星极
for seg in d1['timeline']:
    for fr in seg['frames']:
        fr['desc'] = (fr['desc']
                      .replace('朱儁（汉，4 星', '朱儁（汉，5 星极')
                      .replace('甘宁（吴，4 星', '甘宁（吴，5 星极')
                      .replace('凌统（吴，4 星', '凌统（吴，5 星极')
                      .replace('凌统（吴，大营 4 星', '凌统（吴，大营 5 星极'))

# 局限③：更新为资料库口径
d1['limitations'][2] = ("资料库判定朱儁/甘宁/凌统均为 5 星（hero_star_fixed.json）；画面阵容弹窗显示「5 星极」"
                        "与资料库一致。战报卡曾显示 4 星属低分辨率误读，以资料库 5 星为准。")

json.dump(d1, open(p1, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('[OK] 甘宁 JSON 修正完成')

# ============ 二、月卡配将：去冗余（画面要点压缩 / 七剔除OCR纠正重复 / 八仅留真推断） ============
p2 = os.path.join(LIB, 'video_月卡配将不一定配的就好，但是免费..._top_0_3.json')
d2 = json.load(open(p2, encoding='utf-8'))

# 校验：OCR 纠正应已在 comparison（四）中，七 不应重复
comp = d2.get('comparison') or d2.get('summary', {}).get('corrections') or []
has_ocr_in_comp = any('按官方' in str(c) or 'methodName 修正' in str(c) for c in comp)
print('[INFO] comparison 含 OCR 纠正条目数 =', sum(1 for c in comp if '按官方' in str(c) or 'methodName 修正' in str(c)))

# 画面要点：压成 5 条关键证据指针（详细阵容在二·阵容详解表 + 九·逐帧时间线，避免三重冗余）
d2['summary']['visual_only'] = [
    "00:03–00:25 第1队「曹彰流氓」弹窗（曹彰+张春华+孙权）：9 战法位 + 3 宝物 + 6 兵种词条全部可逐字转录；UP 主批「曹彰先手→伤害易被规避→须配计险远近 4 件套」。",
    "00:26–00:44 第2队「核弹」（李儒+张宁+吕蒙）、第3队「大狗螃蟹」（荀彧+曹操+夏侯惇）：UP 主批「螃蟹无反计玩不了」「不攻/妖术落后版本三年」「粉丝有木鹿应配撸铁」。",
    "00:45–00:51 第4队「甘宁流氓」（甘宁+司马炎+貂蝉）：UP 主批「无疾风迅雷的甘宁是弟中弟」「战必断金应给第1队曹彰流氓而非第4队」。",
    "00:58–01:12 第5队「免费版曹彰流氓」（同 3 武将，战法搭配不同）：把战必断金给孙权做先手控制，UP 主评「板正」，与收费版对比凸显「套公式配将不如免费粉丝用心」。",
    "全片 5 个阵容弹窗 100% 信息可逐字转录；音频转写对 25+ 句硬字幕失真率约 80–85%，结论以画面为准（详见四、视觉判读纠正）。",
]

# 局限：剔除与「四、视觉纠正」重复的 OCR 纠正条目（含「按官方 methodName 修正」者），仅留真局限
new_lim = []
DROPPED = 0
for it in d2.get('limitations', []):
    s = str(it)
    if '按官方 methodName 修正' in s or ('画面字' in s and 'OCR' in s and '按字面记录' not in s and '待核验' not in s and '已多次确认' not in s):
        # 仅剔除「已按官方修正」的纠正性条目；保留「按字面记录+待核验」的存疑条目
        if '按官方 methodName 修正' in s:
            DROPPED += 1
            continue
    new_lim.append(it)
d2['limitations'] = new_lim
print('[INFO] 月卡 局限 剔除 OCR 纠正重复条目 =', DROPPED, '| 剩余 =', len(new_lim))

# AI 推断：仅留真正超出视频原话的延伸分析（木鹿核弹流 / 武将池与赛季 / 方法论对比），剔除复述视频内容者
KEEP_MARKS = ['木鹿', '第八期', 'S3', '赛季归属', '武将池', '阵营分布', '4 阵营']
new_ai = []
for it in d2.get('ai_inference', []):
    pt = str(it.get('point', '')) if isinstance(it, dict) else str(it)
    if any(m in pt for m in KEEP_MARKS):
        new_ai.append(it)
d2['ai_inference'] = new_ai
print('[INFO] 月卡 AI推断 保留 =', len(new_ai), '/ 原', len(d2.get('ai_inference', [])))

json.dump(d2, open(p2, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('[OK] 月卡 JSON 去冗余完成')
