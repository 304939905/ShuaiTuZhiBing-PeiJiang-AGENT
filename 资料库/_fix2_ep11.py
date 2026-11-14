# -*- coding: utf-8 -*-
"""清理 timeline desc 中的定向复核叙述（基线对齐），重渲双报告"""
import json, io, sys, importlib.util, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = r"D:/Desktop/shandou/资料库"
P = BASE + r"/zhenrong_frame_json/video_免费粉丝配将第十一期，继续配将。..._top_0_2.json"
d = json.load(open(P, encoding="utf-8"))

FIX = [
    ("本帧定向复核确认大营马岱宝物为「戚」+词条「破敌」。", "大营马岱宝物「戚」+词条「破敌」。"),
    ("本帧定向复核确认曹彰宝物为「彤素」+词条「英勇」。", "曹彰宝物「彤素」+词条「英勇」。"),
    ("（定向复核确认末三字「庞司荀」）", ""),
]
txt = open(P, encoding="utf-8").read()
for old, new in FIX:
    c = txt.count(old)
    assert c == 1, (old, c)
    txt = txt.replace(old, new)
open(P, "w", encoding="utf-8").write(txt)
d = json.load(open(P, encoding="utf-8"))

def walk(o):
    n = 0
    if isinstance(o, dict):
        for v in o.values(): n += walk(v)
    elif isinstance(o, list):
        for v in o: n += walk(v)
    elif isinstance(o, str) and "定向复核确认" in o and True:
        n += 1
    return n

# timeline desc 内必须为 0
tl = sum(1 for seg in d["timeline"] for f in seg.get("frames", []) if "定向复核确认" in f.get("desc", ""))
print("timeline desc 残留:", tl)
assert tl == 0

# ---- 重渲 ----
spec = importlib.util.spec_from_file_location("g1", BASE + "/gen_refined_report_zhenrong.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
op, row = m.render(P)
print("精编:", op)
r = subprocess.run([sys.executable, BASE + "/gen_frame_report_1s_zhenrong.py", P],
                   capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=BASE)
print("1s rc:", r.returncode, (r.stdout or "")[-200:])
assert r.returncode == 0

# ---- 终验 ----
from docx import Document
for tag, p in [("精编", op), ("1秒", r"D:/Desktop/shandou/报告库/阵容新批/逐帧1秒版/video_免费粉丝配将第十一期，继续配将。..._top_0_2_逐帧深度学习报告_1秒版.docx")]:
    dd = Document(p)
    tx = "\n".join(x.text for x in dd.paragraphs)
    for t in dd.tables:
        for rr in t.rows:
            for c in rr.cells: tx += "\n" + c.text
    bad = sum(tx.count(k) for k in ["UP主", "止戈丨青仙", "定向复核确认", "画面读作", "转写误作", "曹障"])
    print(tag, "字符:", len(tx), "表格:", len(dd.tables), "图:", len(dd.inline_shapes), "违规残留:", bad,
          "筹算:", tx.count("筹算"), "海凰(仅溯源):", tx.count("海凰"))
