import os
old = "D:/Desktop/攻其篇精编报告_最终修正版_2026-08-19.docx"
if os.path.exists(old):
    os.remove(old)
    print("已删除旧版")
else:
    print("旧版不存在")
# 列出剩余
import glob
for f in glob.glob("D:/Desktop/攻其篇*"):
    print("保留:", os.path.basename(f), os.path.getsize(f), "bytes")
