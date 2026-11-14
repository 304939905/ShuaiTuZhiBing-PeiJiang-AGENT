# -*- coding: utf-8 -*-
"""R1-2：将无证据的“硬性机制互斥”降为作者的配队取舍。"""
from pathlib import Path
from docx import Document


ROOT = Path(r"D:/Desktop/shandou")
SOURCE = ROOT / "报告库/旧56项目/逐帧1秒版/孙权完全不适配张机 ，来看看有哪些常见误区_逐帧深度学习报告_1秒版.docx"

REPLACEMENTS = {
    "本视频论证「孙权是鬼吕最佳队友，但孙权和张机完全不该放在一起」这一核心观点：鬼吕怕法伤爆头，双减挡不住现版本高增伤，只有孙权的规避（直接不挨打）才能从根本上免疫策略伤害；张机的「让你挨打不疼」与孙权的「不让你挨打」机制互斥，正确搭配是战磐 + 控制 + 自发恢复型辅助，成品为鬼吕 + 甄洛 + 孙权的「战磐小流氓」。": "本视频表达作者观点：孙权是鬼吕的优先队友；在作者的配队取舍中，孙权与张机同时投入时功能重叠、性价比不高。作者用「孙权放战法 / 张机回血」的拟人化画面说明这一取舍，并推荐鬼吕 + 甄洛 + 孙权的「战磐小流氓」。孙权的规避与张机的减伤、恢复可以分别由官方描述支持，但不能据此推出两者存在硬性机制互斥。",
    "01:35 孙权 vs 张机对话气泡图：左侧孙权说「哥们儿，我放战法了」；右侧张机说「大哥，我能回血有！」——用拟人化方式直观展示两者机制冲突。此为纯画面创意表达，音频仅旁白叙述。": "01:35 孙权 vs 张机对话气泡图：画面以「孙权放战法」和「张机回血」作拟人化表达，呈现作者对两者配队取舍的看法。此为纯画面创意表达，不能单独证明存在硬性机制互斥。",
    "01:20–01:59　核心误区：孙权 + 张机互斥（动画对话论证）": "01:20–01:59　作者的配队取舍：孙权 + 张机（动画对话表达）",
    "01:35 | 孙权 vs 张机拟人化对话气泡图：孙权「哥们儿，我放战法了」vs 张机「大哥，我能回血有！」——机制冲突可视化。": "01:35 | 孙权 vs 张机拟人化对话气泡图：以两句对话表达作者对两者配队取舍的看法；不能单独据此认定硬性机制互斥。",
    "机制冲突拟人化：01:35/01:55帧孙权vs张机对话气泡图以创意方式将抽象的机制互斥转化为直观的「一个放战法一个想回血」的矛盾场景。": "作者取舍的拟人化表达：01:35/01:55帧孙权 vs 张机对话气泡图以创意方式呈现「一个放战法、一个想回血」；它支持作者认为投入重叠的配队判断，不能单独证明硬性机制互斥。",
}


def replace_paragraph(paragraph, replacement: str) -> None:
    if paragraph.runs:
        paragraph.runs[0].text = replacement
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(replacement)


def main() -> None:
    doc = Document(SOURCE)
    found = set()
    for paragraph in doc.paragraphs:
        old = paragraph.text
        if old in REPLACEMENTS:
            replace_paragraph(paragraph, REPLACEMENTS[old])
            found.add(old)
    missing = set(REPLACEMENTS) - found
    if missing:
        escaped = [item.encode("unicode_escape").decode() for item in missing]
        raise RuntimeError(f"未找到待替换段落：{len(missing)} 条：{escaped}")
    doc.save(SOURCE)
    print(f"PATCHED={len(found)}")


if __name__ == "__main__":
    main()
