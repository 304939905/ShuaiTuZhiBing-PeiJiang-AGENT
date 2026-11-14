#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""旧批精编来源声明的回归测试。"""

from gen_refined_report import _inference_source_notice, _source_items, _source_urls


local = _source_items([
    "音频转写：D:/Desktop/shandou/抖音_transcripts/example.json",
    "画面证据：D:/Desktop/shandou/抖音_frames_dense_1s/example/ 共 10 帧",
])
assert len(local) == 2
assert _source_urls(local) == []
notice = _inference_source_notice(local)
assert "不宣称已完成外部网站核验" in notice
assert "网易大神" not in notice

direct = _source_items("外部参考：https://ds.163.com/article/example")
assert _source_urls(direct) == ["https://ds.163.com/article/example"]
assert "实际列出的可复现直链" in _inference_source_notice(direct)

assert _source_items(None) == []
assert "不宣称已完成外部网站核验" in _inference_source_notice([])

print("gen_refined_report source rules: PASS")
