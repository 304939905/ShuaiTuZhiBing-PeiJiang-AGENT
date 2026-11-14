#!/usr/bin/env python
# -*- coding: utf-8 -*-
from hero_version_resolver import resolve_label


def check(name, skill, expected, visual_evidence=None):
    actual = resolve_label(name, skill, visual_evidence=visual_evidence)
    assert actual == expected, (name, skill, actual, expected)


check("甘宁", "轻侠妄为", "吴-弓-4星")
check("甘宁", "侵掠如火", "版本待核实")
check("甘宁", "侵掠如火", "吴-步-5星", {
    "country": "吴", "star": 5, "variant": "normal", "source_frame": "frame_000071.jpg"
})
check("甘宁", "侵掠如火", "吴-步-5星(SP)", {
    "country": "吴", "star": 5, "variant": "SP", "source_frame": "frame_000071.jpg"
})
check("孙权", "九锡黄龙", "版本待核实")
check("孙权", "自擅江表", "版本待核实")
check("荀彧", "驱虎吞狼", "版本待核实")
check("荀彧", "举贤决机", "版本待核实")
check("姜维", "列营守险", "版本待核实")
check("姜维", "列营守险", "蜀-弓-5星(SP)", {
    "country": "蜀", "star": 5, "variant": "SP", "arms": "弓", "source_frame": "frame_000071.jpg"
})
assert resolve_label("甘宁") == "版本待核实"
assert resolve_label("木鹿大王") == "版本待核实"
assert resolve_label("卫瓘") == "版本待核实"
assert resolve_label("典韦", "舍身卫主") == "版本待核实"
assert resolve_label("孙权", visual_evidence={
    "country": "吴", "star": 5, "variant": "normal", "source_frame": "frame_000071.jpg"
}) == "吴-弓-5星"
assert resolve_label("孙权", visual_evidence={
    "country": "吴", "star": 5, "variant": "XP", "source_frame": "frame_000071.jpg"
}) == "吴-弓-5星(XP)"
assert resolve_label("孙权", visual_evidence={
    "country": "吴", "star": 5, "variant": "SP", "source_frame": "frame_000071.jpg"
}) == "吴-弓-5星(SP)"
assert resolve_label("孙权", visual_evidence={"country": "吴", "star": 5, "variant": "XP"}) == "版本待核实"
assert resolve_label("孙权", explicit_label="吴-弓-5星") == "版本待核实"
print("hero_version_resolver: PASS")
