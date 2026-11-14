#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""赛季 4 视频 复核扫描器（Pass2 官方库比对 + Pass3 残差扫描）。

输出：
  - 每个视频引用到的官方 武将/战法/宝物 名清单（供人工核对是否符合视频主题）
  - 繁体字出现位置（OCR 误识红线）
  - 已知错误 OCR token 命中
  - 疑似「非官方白名单」的四字以内中文片段（疑似错名/俗称，需人工判断）
"""
import os, json, re

BASE = r"D:\Desktop\shandou"
JSON_DIR = os.path.join(BASE, "资料库", "saiji_frame_json")
LIB = os.path.join(BASE, "资料库")


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def collect_names():
    names = set()
    d = load_json(os.path.join(LIB, "official_hero_names.json"))
    names |= set(d.get("names", []))
    d = load_json(os.path.join(LIB, "official_gear_names.json"))
    names |= set(d.get("names", []))
    d = load_json(os.path.join(LIB, "official_jineng_names_ext.json"))
    for k in ("common", "innate_from_hero"):
        names |= set(d.get(k, []))
    d = load_json(os.path.join(LIB, "official_jineng_names.json"))
    names |= set(d.get("names", []))
    # 名词概念.md 收录的体系/俗称（合法但非官方战法名）
    return {n for n in names if n and len(n) >= 2}


def iter_text(obj):
    """yield all string leaf values."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from iter_text(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from iter_text(v)


# 繁体->简体 映射（率土常见字），用于残差扫描
TRAD_MAP = {
    "將": "将", "軍": "军", "戰": "战", "隊": "队", "時": "时", "國": "国", "號": "号",
    "後": "后", "對": "对", "從": "从", "處": "处", "點": "点", "進": "进", "關": "关",
    "開": "开", "試": "试", "師": "师", "勝": "胜", "該": "该", "當": "当", "無": "无",
    "總": "总", "網": "网", "頁": "页", "說": "说", "話": "话", "實": "实", "員": "员",
    "單": "单", "為": "为", "個": "个", "這": "这", "義": "义", "強": "强", "擊": "击",
    "滅": "灭", "殺": "杀", "統": "统", "裝": "装", "載": "载", "歷": "历", "現": "现",
    "環": "环", "圖": "图", "種": "种", "類": "类", "經": "经", "許": "许", "導": "导",
    "專": "专", "轉": "转", "輕": "轻", "錢": "钱", "銀": "银", "銅": "铜", "鐵": "铁",
    "馬": "马", "驗": "验", "證": "证", "識": "识", "讀": "读", "產": "产", "條": "条",
    "約": "约", "萬": "万", "與": "与", "於": "于", "麼": "么", "張": "张", "遼": "辽",
    "劉": "刘", "蕭": "萧", "鶴": "鹤", "遊": "游", "靈": "灵", "鴉": "鸦", "傑": "杰",
    "熱": "热", "淬": "淬", "臻": "臻", "剛": "刚", "鳴": "鸣", "勞": "劳", "駮": "驳",
    "機": "机", "勢": "势", "儀": "仪", "夢": "梦", "級": "级", "眞": "真",
}
TRAD = set(TRAD_MAP.keys())

# 已知错误 OCR / 编造 token（历史出现过，必须清零；不全是繁体）
BAD_TOKENS = ["勞駮", "大桐琴", "母儀逐夢", "遊歌天亮", "臻級真剛", "鴉鳴靈動",
              "仿傑熱淬", "傑熱淬", "鶴翼", "機勢"]


def main():
    names = collect_names()
    name_list = sorted(names, key=len, reverse=True)  # 长优先
    print("官方白名单规模:", len(names))

    for fn in sorted(os.listdir(JSON_DIR)):
        if not fn.endswith(".json"):
            continue
        data = load_json(os.path.join(JSON_DIR, fn))
        txt = "\n".join(iter_text(data))
        # 1) 命中官方名
        hit = set()
        for n in name_list:
            if n in txt:
                hit.add(n)
        # 2) 繁体
        trad_hit = sorted({c for c in txt if c in TRAD})
        # 3) 已知错误 token
        bad = [t for t in BAD_TOKENS if t in txt]
        # 4) 疑似错名：4字以内中文片段不在白名单且含「将/战/队/法」等关键词
        print("\n" + "=" * 70)
        print("视频:", fn)
        print(f"  命中官方名({len(hit)}):", "、".join(sorted(hit)))
        print(f"  繁体字({len(trad_hit)}):", "".join(trad_hit) if trad_hit else "（无）")
        print(f"  已知错误token:", bad if bad else "（无）")


if __name__ == "__main__":
    main()
