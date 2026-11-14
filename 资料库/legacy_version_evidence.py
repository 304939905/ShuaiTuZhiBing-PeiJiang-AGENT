"""从旧版逐帧 JSON 的文字证据中，保守提取“武将+自带战法”锚点。

旧源没有 ``entities`` 时不改写它；本模块只提供映射兼容层。只有同一条
逐帧描述中武将名与该武将官方自带战法紧邻出现，才输出候选证据。
"""
from __future__ import annotations

from collections import defaultdict
import re
from typing import Iterable

from hero_version_resolver import ROWS_BY_NAME_SKILL


def _atoms(data: dict) -> Iterable[tuple[str, str]]:
    summary = data.get("summary") or {}
    if isinstance(summary, dict):
        for index, text in enumerate(summary.get("visual_only") or []):
            if isinstance(text, str):
                yield f"summary.visual_only[{index}]", text
    # 旧版逐帧报告的“frame_only_value”是由卡面逐格转写得到的汇总；
    # 它并非旁白，且会保留“武将（兵种/自带战法+…）”的完整槽位结构。
    for index, text in enumerate(data.get("frame_only_value") or []):
        if isinstance(text, str):
            yield f"frame_only_value[{index}]", text
    for section_index, section in enumerate(data.get("timeline") or []):
        if not isinstance(section, dict):
            continue
        for frame_index, frame in enumerate(section.get("frames") or []):
            if not isinstance(frame, dict):
                continue
            text = frame.get("desc")
            if isinstance(text, str):
                anchor = str(frame.get("file") or f"timeline[{section_index}].frames[{frame_index}]")
                yield anchor, text


def extract_legacy_builtin_evidence(data: dict, max_gap: int = 28) -> dict[str, list[dict[str, str]]]:
    """返回可回溯的 ``{武将: [{builtin_skill, anchor}]}``。

    规则很窄：必须有“武将带战法”或“武将+战法书名号”的直接句式，且二者
    在同一条逐帧描述中的距离不超过 ``max_gap``。这避免把同一战报里不同
    武将的战法错误归属。
    """
    found: dict[str, list[dict[str, str]]] = defaultdict(list)
    skills_by_hero: dict[str, list[str]] = defaultdict(list)
    for hero, skill in ROWS_BY_NAME_SKILL:
        skills_by_hero[hero].append(skill)
    for anchor, text in _atoms(data):
        for hero, skills in skills_by_hero.items():
            # 大多数逐帧描述不含该武将；先做字符串筛选，避免为每个武将
            # 重复编译和执行正则，保证旧源批处理可低成本重跑。
            if hero not in text:
                continue
            # 长战法名优先，避免“奇佐鬼谋”同时误命中“鬼谋”。
            for skill in sorted(skills, key=len, reverse=True):
                # 仅接受明确归属语法；不能把同一战报内的远距离共现当作归属。
                quoted_pattern = re.compile(
                    re.escape(hero)
                    + rf"(?:（[^）]{{0,20}}）)?(?:带|自带|第[0０]战法位(?:为|是)?|战法位(?:为|是)?)?"
                    + rf"[ A-Sa-s0-9.]{{0,{max_gap}}}[「『]"
                    + re.escape(skill)
                    + r"[」』]"
                )
                # 旧逐帧摘要还常把完整阵容写成“荀彧（驱虎吞狼+…）”或
                # “荀彧：驱虎吞狼”。这两种格式中武将与首个战法紧邻，
                # 同样是可回溯的直接归属；不接受无分隔符的远距离共现。
                adjacent_pattern = re.compile(
                    re.escape(hero)
                    + r"\s*[（(：:]\s*"
                    + re.escape(skill)
                )
                # 战报/阵容转写常写作“曹操(前锋)：魏武之世…”。括号内仅为
                # 位置或等级等附注，冒号后的首个战法仍是明确归属。
                role_adjacent_pattern = re.compile(
                    re.escape(hero)
                    + r"\s*[（(][^）)]{0,24}[）)]\s*[：:]\s*"
                    + re.escape(skill)
                )
                # 逐帧描述对武将卡页的固定转写：
                # “关银屏武将界面，展示自带战法「巾帼战阵」”。
                card_caption_pattern = re.compile(
                    re.escape(hero)
                    + r"[^。！？!？]{0,32}?自带(?:[A-ZＳ]级)?战法[^。！？!？]{0,8}?[「『]"
                    + re.escape(skill)
                    + r"[」』]"
                )
                # 另一种卡面注释把战法写在前面：
                # “「衡轭」（木鹿大王自带S级战法位……）”。
                reverse_card_caption_pattern = re.compile(
                    r"[「『]"
                    + re.escape(skill)
                    + r"[」』][^。！？!？]{0,20}?[（(]"
                    + re.escape(hero)
                    + r"[^）)]{0,16}自带"
                )
                # 汇总型阵容转写的固定槽位语法：
                # “祝融夫人（蛮兵/火兽冲锋+先驱突击+三军齐出）”。斜杠后的
                # 第一个战法即自带位，不能把后两格当成自带战法。
                lineup_slot_pattern = re.compile(
                    re.escape(hero)
                    + r"\s*[（(][^）)]{0,24}/\s*"
                    + re.escape(skill)
                    + r"(?:\s*[+＋/）)])"
                )
                bare_owned_pattern = re.compile(
                    re.escape(hero)
                    + r"(?:带|自带|第[0０]战法位(?:为|是)?|战法位(?:为|是)?)"
                    + rf"[ A-Sa-s0-9.]{{0,12}}"
                    + re.escape(skill)
                )
                if not (
                    quoted_pattern.search(text)
                    or adjacent_pattern.search(text)
                    or role_adjacent_pattern.search(text)
                    or card_caption_pattern.search(text)
                    or reverse_card_caption_pattern.search(text)
                    or lineup_slot_pattern.search(text)
                    or bare_owned_pattern.search(text)
                ):
                    continue
                record = {"builtin_skill": skill, "anchor": anchor}
                if record not in found[hero]:
                    found[hero].append(record)

        # 部分旧逐帧摘要把阵容页完整转写为：
        # “甲（大营）+乙（中军）+丙（前锋），九战法为 A / B / C、D / E / F、G / H / I”。
        # 这里的武将顺序与三个三战法组一一对应，因此可以安全确认每组中
        # 出现的自带战法。只接受九战法、三人、三组三战法这个完整结构；
        # 不把普通的“同屏阵容 + 战法名”当作证据。
        formation = re.search(
            r"([^（+，。：:]{1,12})(?:（[^）]*）)?\s*\+\s*"
            r"([^（+，。：:]{1,12})(?:（[^）]*）)?\s*\+\s*"
            r"([^（+，。：:]{1,12})(?:（[^）]*）)?，九战法(?:为|含)"
            r"([^。！？!？]+)",
            text,
        )
        if formation:
            # 第一个武将前偶尔有“某某配队界面：”之类的说明。只取该段中
            # 最靠后的已知武将名；其余两个段也同样要求能解析到已知武将。
            def known_hero_at_tail(raw: str) -> str | None:
                matches = [(raw.rfind(name), name) for name in skills_by_hero if name in raw]
                return max(matches)[1] if matches else None

            heroes = [
                known_hero_at_tail(formation.group(1).strip()),
                known_hero_at_tail(formation.group(2).strip()),
                known_hero_at_tail(formation.group(3).strip()),
            ]
            groups = [group.strip() for group in formation.group(4).split("、")]
            if all(heroes) and len(groups) == 3:
                for hero, group in zip(heroes, groups):
                    # 必须正好是一个三战法组，才使用位置对应关系。
                    skills = [skill.strip() for skill in group.split("/")]
                    if len(skills) != 3:
                        continue
                    for builtin_skill in skills_by_hero.get(hero, []):
                        if builtin_skill in skills:
                            record = {"builtin_skill": builtin_skill, "anchor": anchor}
                            if record not in found[hero]:
                                found[hero].append(record)
    return dict(found)
