# -*- coding: utf-8 -*-
"""批量视觉侦察驱动：对指定帧列表逐帧调用 vision_glm.py，结果增量写入输出文件。
支持断点续跑（输出文件中已有的帧自动跳过）。
用法:
  PYTHONPATH=<site-packages> python vision_recon_driver.py <帧目录> <输出md> <帧名1,帧名2,...>
"""
import os, subprocess, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = r"D:/Desktop/shandou/资料库"
PY = r"C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
VGLM = os.path.join(BASE, "vision_glm.py")

QUESTION = ("这是什么界面？如有硬字幕/大字标题请完整逐字转录。如果是阵容卡/编队界面：列出部队编号、"
            "武将名、每个武将的战法名、宝物名以及宝物名正上方紧邻的小字词条、宝物下方的兵种词条；"
            "无则说无。只写画面可见的字面内容，不确定的标注[存疑]，禁止推测补全。")

def main():
    frames_dir, out_path, names_csv = sys.argv[1], sys.argv[2], sys.argv[3]
    names = [n.strip() for n in names_csv.split(",") if n.strip()]
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path, encoding="utf-8"):
            line = line.strip()
            if line.startswith("## "):
                done.add(line[3:].strip())
    env = dict(os.environ)
    env["PYTHONPATH"] = r"D:/WorkBuddyData/python-env/shandou/Lib/site-packages"
    with open(out_path, "a", encoding="utf-8") as out:
        for i, name in enumerate(names):
            if name in done:
                print(f"[{i+1}/{len(names)}] {name} 已完成，跳过", flush=True)
                continue
            img = os.path.join(frames_dir, name)
            if not os.path.exists(img):
                out.write(f"## {name}\n[帧文件不存在]\n\n"); out.flush()
                continue
            print(f"[{i+1}/{len(names)}] 判读 {name} ...", flush=True)
            try:
                r = subprocess.run([PY, VGLM, img, QUESTION],
                                   capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=300, cwd=BASE, env=env)
                body = (r.stdout or "").strip()
                if not body:
                    body = "[视觉模型无输出] stderr: " + (r.stderr or "")[:300]
            except Exception as e:
                body = f"[调用异常] {e!r}"
            out.write(f"## {name}\n{body}\n\n")
            out.flush()
            print(f"    -> {len(body)} 字符", flush=True)
    print("ALL DONE", flush=True)

if __name__ == "__main__":
    main()
