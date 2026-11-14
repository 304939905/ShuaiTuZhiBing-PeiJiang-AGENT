#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""重建 5 份抽样问题报告的截断母本；成品重渲留给第 3 项统一复核。"""
from __future__ import annotations

import json
from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "zhenrong_frame_json"

REBUILT = {
    "video_免费粉丝配将第九期，平民专业配将..._top_0_2.json": {
        "frames": ["00:22", "00:37", "00:53"],
        "points": [
            "作者为“战法储备较好、核心武将不足”的账号给出战磐、甄洛小流氓、黄盖法刀与木鹿螃蟹四套方案；这些名称和取舍均应理解为作者针对该账号的建议。",
            "第四队画面为华雄+木鹿大王+夏侯惇，硬字幕明确“其实这队我并不是很推荐”。报告保留该否定意见，不把其补写为未展示的强度或克制结论。",
            "姜维的弓/步版本未能由当前画面唯一锁定，成品中不作具体兵种断言；视频也未提供可比较四队的胜率或完整样本。",
        ],
    },
    "video_对自己队伍不确定的，发评论区大家..._top_0_3.json": {
        "frames": ["00:19", "01:20"],
        "points": [
            "作者复盘粉丝的王异法刀、鬼吕网红、曹彰流氓和大狗撸铁四队配置，再给出荀彧撸铁、吕布网红、曹彰典韦三套调整方向。",
            "01:20 画面可见荀彧+木鹿大王+曹操；各方案的优劣与替换理由均归属于作者讲解，不能仅凭队名或单帧延伸为通用结论。",
            "宝物与词条看不清的内容不补写；视频未给出战报、胜率或样本量，配队结论仍以报告局限节为边界。",
        ],
    },
    "video_来人配将，免费粉丝配将第十三期 ..._top_0_3.json": {
        "frames": ["00:20", "00:36", "00:48"],
        "points": [
            "作者针对武将少、战法残缺且无宝物的账号，给出神赏降级版、百战螃蟹和战磐体系三套替代配置；这是按该账号资源作出的配将建议。",
            "第一队画面可见李儒+张宁+朱儁，硬字幕为“现在零氪号不再卡神兵”；这只证明作者在视频中提出该资源判断，不外推为所有赛季和账号的获取结论。",
            "涉及带赛季标识战法的适配性继续保留在局限节；视频未展示可量化三队实战强度的战报样本。",
        ],
    },
    "video_来来来，上人配将，免费粉丝配将第..._top_0_1.json": {
        "frames": ["00:25", "00:45", "00:52"],
        "points": [
            "作者按粉丝 S 赛季资源缺口定制四队：祝融三马开荒、木鹿撸铁、司马懿神赏和刘备+司马炎+典韦物理坦克队。各队强度是作者建议，视频未提供战报样本。",
            "00:25 仅显示未展开筛选面板下的女将卡列表；可见小乔、步练师、大乔、貂蝉、卫子夫、王元姬等，不能据此写“四星库”“女将筛选”或任何筛选条件。",
            "视频展示的是武将池尚可但核心战法短缺时的配将取舍；看不清或未唯一锁定的武将版本、宝物和词条保持“版本待核实”或留在局限节。",
        ],
        "timeline_replacements": {
            "司马懿大卡 + 4 星女将库 + S 级战法 1/1 + 战法开卷红 0": "司马懿卡面 + 可见女将卡列表 + S 级战法 1/1 + 战法开卷红 0"
        },
    },
    "四星称号神队晋步，竹林七贤.json": {
        "frames": ["00:00", "00:18", "00:29"],
        "points": [
            "视频展示嵇康、阮籍、刘伶组成的竹林七贤步兵队，并分别给出重整旗鼓+增援、妖术+合流、擅兵不寡+利兵谋胜的配置。",
            "武将组合画面写明：竹林七贤在第 3 回合武将行动后进入规避状态，免疫接下来受到的 1 次伤害；该机制以画面和本地组合资料为依据。",
            "视频展示若干胜、平、败战报，但没有说明对手筛选、连续场次或统计口径；“可与5星主力一战”等强度判断仍归属于作者，不能量化为胜率。",
        ],
    },
}


def main() -> None:
    for filename, rebuilt in REBUILT.items():
        path = SOURCE / filename
        data = json.loads(path.read_text(encoding="utf-8"))
        summary = data.setdefault("summary", {})
        summary["key_points"] = rebuilt["points"]
        summary["refined_key_points"] = rebuilt["points"]
        summary["key_points_rebuild_20260825"] = {
            "method": "回看原视频秒帧、逐帧1秒报告和JSON时间轴；仅保留画面/硬字幕/作者判断。",
            "key_frames": rebuilt["frames"],
        }
        for item in data.get("timeline") or []:
            for old, new in rebuilt.get("timeline_replacements", {}).items():
                if item.get("title") == old:
                    item["title"] = new
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"UPDATED\t{filename}")


if __name__ == "__main__":
    main()
