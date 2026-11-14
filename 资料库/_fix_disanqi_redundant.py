# -*- coding: utf-8 -*-
"""第十三期 JSON 冗余清理：UP主→作者 / 去作者&粉丝ID / 去养号进度 / 精简画面要点。
按 RULES/03 冗余红线补充（2026-08-22 用户反馈）执行。改母本 JSON，不改 docx。
"""
import json, shutil, os, sys

SRC = r"D:\Desktop\shandou\资料库\zhenrong_frame_json\video_来人配将，免费粉丝配将第十三期 ..._top_0_3.json"
BAK = SRC + ".bak_redundant"

def apply(s: str) -> str:
    if not isinstance(s, str):
        return s
    r = s
    # 1) 称呼作者：UP主/UP 主 -> 作者
    r = r.replace("UP 主", "作者").replace("UP主", "作者")
    # 2) 养号进度 & 月卡零氪 -> 平民/平民账号（先处理带前缀的，避免双重叠加）
    r = r.replace("S 赛季月卡从 0 养号", "S 赛季平民账号")
    r = r.replace("作者「北冥」按月卡从 0 养号的粉丝「真秋色浓」账号情况", "作者根据粉丝的账号情况")
    r = r.replace("按月卡从 0 养号账号缺口反向定制", "按账号缺口反向定制")
    r = r.replace("月卡从0养号的代表", "平民账号的代表")
    r = r.replace("月卡从0养号", "平民")
    r = r.replace("月卡从 0 养号", "平民")
    r = r.replace("月卡零氪号", "平民账号")
    # 3) 作者/粉丝 ID 删除
    r = r.replace("作者账号 ID「止戈丨青仙」+ ", "")
    r = r.replace("作者自己号", "作者账号")
    r = r.replace("截图粉丝 chat（真秋色浓）", "截图粉丝 chat")
    r = r.replace("部队阵容配置底框「真秋色浓 部队一」", "粉丝账号部队阵容配置底框「部队一」")
    r = r.replace("真秋色浓 部队一", "粉丝账号部队一")
    r = r.replace("比上期「北斗丨疯踏」账号", "比上期粉丝账号")
    # 3a) corrections[18] 粉丝ID清理
    r = r.replace("把粉丝「真秋色浓」误写为", "把粉丝留言误写为")
    r = r.replace("显示「真秋色浓 你好呀主播」", "显示「你好呀主播」")
    r = r.replace("粉丝署名「真秋色浓」", "粉丝署名")
    r = r.replace("（与配将底框 00:08-00:19「真秋色浓 部队一」一致）", "（与配将底框的粉丝账号一致）")
    # 4) 聊天界面长块（visual_only[1] 与 timeline line77 两个变体）
    block_a = ("00:04–00:07 聊天界面 + 右侧地图 split screen：作者聊天 ID「长史」"
               "+ 好友列表（真秋色浓/武悼丨鹤归/缘起丨黑夜/天凉丨坡不语/雨丨平淡/白菜对我笑/好友 99/100）"
               "+ 右侧武将列表（司马师/张飞/吕蒙/马超/马岱）；中部 chat 记录显示粉丝「真秋色浓」留言"
               "「你好呀主播」+ 表情 + 「沙场点兵，智平天下！提供部队搭配建议，助'吾'之力」+ 粉丝署名。"
               "硬字幕「每个人的武将卡池都不一样」，作者主张按账号武将池定制。")
    r = r.replace(block_a, "00:04–00:07 聊天界面：作者主张按账号武将池定制（硬字幕「每个人的武将卡池都不一样」）。")
    block_b = ("聊天界面 + 右侧地图 split screen：作者 ID「长史」"
               "+ 好友列表（真秋色浓/武悼丨鹤归/缘起丨黑夜/天凉丨坡不语/雨丨平淡/白菜对我笑/好友 99/100）"
               "+ 右侧武将列表；中部 chat 记录显示粉丝「真秋色浓」留言"
               "「你好呀主播」+ 表情 + 「沙场点兵，智平天下！提供部队搭配建议，助'吾'之力」+ 粉丝署名。"
               "硬字幕「每个人的武将卡池都不一样」，作者主张按账号武将池定制。")
    r = r.replace(block_b, "聊天界面：作者主张按账号武将池定制（硬字幕「每个人的武将卡池都不一样」）。")
    return r

def walk(o):
    if isinstance(o, dict):
        return {k: walk(v) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(v) for v in o]
    if isinstance(o, str):
        return apply(o)
    return o

def main():
    if not os.path.exists(BAK):
        shutil.copy2(SRC, BAK)
        print("backup ->", BAK)
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    data = walk(data)
    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # 校验
    with open(SRC, encoding="utf-8") as f:
        json.load(f)
    print("OK: JSON 合法，已写回")

if __name__ == "__main__":
    main()
