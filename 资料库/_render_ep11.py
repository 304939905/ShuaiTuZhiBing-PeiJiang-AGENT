# -*- coding: utf-8 -*-
"""渲染第十一期双报告 + 补录索引行"""
import importlib.util, io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = r"D:/Desktop/shandou/资料库"
JP = BASE + r"/zhenrong_frame_json/video_免费粉丝配将第十一期，继续配将。..._top_0_2.json"

# ---- 1. 精编版 ----
spec = importlib.util.spec_from_file_location("g1", BASE + "/gen_refined_report_zhenrong.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
op, row = m.render(JP)
print("精编:", op)

# ---- 2. 1秒版 ----
import subprocess
r = subprocess.run([sys.executable, BASE + "/gen_frame_report_1s_zhenrong.py", JP],
                   capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=BASE)
print("1s rc:", r.returncode)
print((r.stdout or "")[-400:])
if r.returncode != 0:
    print("STDERR:", (r.stderr or "")[-600:])

# ---- 3. 索引行去重追加 ----
IDX = BASE + "/zhenrong_index_rows.json"
rows = json.load(open(IDX, encoding="utf-8"))
if not any(x.get("title") == row.get("title") for x in rows):
    rows.append(row)
    json.dump(rows, open(IDX, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("索引行追加:", row.get("title"), "共", len(rows), "行")
else:
    print("索引行已存在，跳过")
