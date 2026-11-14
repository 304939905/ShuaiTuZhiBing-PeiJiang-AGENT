# -*- coding: utf-8 -*-
"""修复第十一期 JSON：①大乔 traits 强韧→筹算（游飘法系池约束裁决）②补 summary.corrections ③清理 desc 定向复核叙述"""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

P = r"D:/Desktop/shandou/资料库/zhenrong_frame_json/video_免费粉丝配将第十一期，继续配将。..._top_0_2.json"
d = json.load(open(P, encoding="utf-8"))
txt = open(P, encoding="utf-8").read()

# ---- 1. 大乔 traits 强韧→筹算 ----
for t in d["entities"]["teams"]:
    for p in t["positions"]:
        if p["hero"] == "大乔":
            assert p["traits"] == ["强韧"], p["traits"]
            p["traits"] = ["筹算"]

# ---- 2. visual_only / desc / limitations 中强韧→筹算 ----
def rep(s, old, new, expect):
    c = s.count(old)
    assert c == expect, (old, c, expect)
    return s.replace(old, new)

n0 = txt.count("「游飘」+「强韧」")
assert n0 == 1, n0
txt = txt.replace("宝物「游飘」+「强韧」+兵种「文韬/列阵」", "宝物「游飘」+「筹算」+兵种「文韬/列阵」")

n1 = txt.count("大乔宝物「游飘」+词条「强韧」（定向复核确认）")
assert n1 == 1, n1
txt = txt.replace(
    "大乔宝物「游飘」+词条「强韧」（定向复核确认）；硬字幕「所以第三队出垒石」",
    "大乔宝物「游飘」+词条「筹算」；硬字幕「所以第三队出垒石」",
)

# limitations 两条重写
old_lim1 = "大乔宝物名 recon 多帧读作「海飘/海凰/海飙/穷罗/秀舞海枫」等（均不在宝物白名单），01:10 与 01:14 定向复核两度读出「游飘」（白名单 FOUND，且第二队木鹿大王同持游飘、账号多件稀世宝物可并存），判定为「游飘」；其宝物词条各帧读作 穿杨/秀翎/筹算/齐纨/秀媛/秀舞 等（均 MISSING），01:10 定向复核读「强韧」（白名单 FOUND），按「强韧」记录，仍存不确定性。"
new_lim1 = "大乔宝物名 recon 多帧读作「海飘/海凰/海飙」等（均不在宝物白名单），01:10 与 01:14 定向复核两度读出「游飘」（白名单收录，误读映射表已有「游飘←海啸」同族记录，第二队木鹿大王同持游飘、账号多件稀世宝物可并存），判定为「游飘」；其宝物词条各帧读作 穿杨/秀翎/筹算 等，最终经锻造词条池约束裁决为「筹算」——「强韧」不在游飘可锻池（游飘为纯法系池：灵动/天资/颖悟/驱火/炫惑/筹算；强韧属大将/斩马刀等物理防御系），而「筹算」恰在游飘法系池且大乔为法系适配（术语库点名大乔适配游飘、首选筹算），批量判读 01:14/01:18 两度读出「筹算」。"
assert txt.count(old_lim1) == 1
txt = txt.replace(old_lim1, new_lim1)

old_lim2 = "宝物「强韧」词条及部分硬字幕判定（垒石/撸铁/庞司荀）为多帧互证 + 白名单核验的推断结论"
new_lim2 = "宝物「筹算」词条及部分硬字幕判定（垒石/撸铁/庞司荀）为多帧互证 + 白名单与锻造池核验的推断结论"
assert txt.count(old_lim2) == 1
txt = txt.replace(old_lim2, new_lim2)

# traits 数组值 + sources 审计记录（JSON 序列化层面）
n2 = txt.count('"强韧"')
assert n2 == 2, n2
txt = txt.replace('"强韧"', '"筹算"')
old_note = '"宝物名 recon 多变体，定向复核判定为游飘；词条「强韧」存一定不确定（见 limitations）"'
new_note = '"宝物名 recon 多变体，定向复核判定为游飘；词条经锻造池约束裁决为筹算（见 limitations）"'
assert txt.count(old_note) == 1
txt = txt.replace(old_note, new_note)

assert txt.count("强韧") == 2, txt.count("强韧")  # 仅剩 new_lim1 中两处说明性引用
open(P, "w", encoding="utf-8").write(txt)

# ---- 3. 补 summary.corrections（在 key_points 前插入）----
d = json.load(open(P, encoding="utf-8"))
CORR = [
    "音频转写把「曹彰」转写为「曹障」（53.6-62.0 段多处），硬字幕 00:54「曹彰是绝对的物理一哥」确认为曹彰（hero_extra 命中，大营战法位五兵之烈为画面多帧实读）。",
    "音频转写队伍名「法拉力轉碼速數其」为误读，硬字幕 00:42「一个是法拉利转马谡蜀骑」逐字确认（frame_000043，队伍为马岱+马谡+张绣蜀骑）。",
    "音频转写「樂盡斷小貓隊」为误读，硬字幕 00:41「一个是乐进转小猫队」确认（frame_000042）。",
    "音频转写「魂水給了路鐵白板馬帶」与批量判读「泽水给了鲁铁」均为误读，实为「浑水给了撸铁」「白板马岱直接带一手击势加强穿透力」（frame_000051/000052 硬字幕，木鹿大王浑水摸鱼战法位 frame_000055 佐证）。",
    "硬字幕批量判读「反计撞铁/反计增铁就是曹彰最顶配的阵容」中「撞铁/增铁」为「撸铁」误读（frame_000061/000062，队伍名反计撸铁，曹操反计之策战法位佐证）。",
    "音频转写「大張爐」为误读，frame_000073 阵容确认为「大张鲁」队（大乔+张机+鲁肃，张机金匮要略 hero_extra 命中）。",
    "大乔宝物名多帧读作「海飘/海凰/海飙」等均不在白名单，定向复核两度读「游飘」（白名单收录，误读映射表已有「游飘←海啸」同族记录）；其词条经锻造池约束裁决为「筹算」——「强韧」不在游飘可锻池（游飘纯法系池：灵动/天资/颖悟/驱火/炫惑/筹算），「筹算」在池且批量判读 01:14/01:18 两度读出。",
    "曹彰宝物名批量判读读「泥蒙[存疑]」（frame_000061），01:03 定向复核读「彤素」（白名单收录，词条「英勇」属彤素物理输出池），确认为彤素。",
    "马岱宝物名早期帧读「熙[存疑]」（frame_000044），00:39/00:47 定向复核两度读「戚」（白名单收录，词条「破敌」属戚可锻物理池），确认为戚。",
    "鲁肃宝物词条批量读「瑞锻/良止[存疑]/良业」，均不在词条池；「良止」为「艮止」形误（误读映射表已有「艮止←反正」记录），艮止在博浪可锻池（术语库：灵动/机敏/清毅/仁心/坚忍/艮止/惑言），确认为艮止。",
]
sm = d["summary"]
assert "corrections" not in sm
new_sm = {}
for k, v in sm.items():
    if k == "key_points":
        new_sm["corrections"] = CORR
    new_sm[k] = v
d["summary"] = new_sm

json.dump(d, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("修复完成：强韧→筹算 ×1、corrections ×%d、desc 清理 ×1、limitations 重写 ×2" % len(CORR))
d2 = json.load(open(P, encoding="utf-8"))
print("回读校验：17键=%d corrections=%d 大乔traits=%s" % (
    len(d2), len(d2["summary"]["corrections"]),
    [p["traits"] for t in d2["entities"]["teams"] for p in t["positions"] if p["hero"] == "大乔"]))
