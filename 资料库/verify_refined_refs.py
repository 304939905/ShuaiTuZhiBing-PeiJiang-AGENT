#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""核验精编全部帧引用: 是否已全量更新为新格式 + 新格式引用是否落地(文件存在) + 旧格式残留。"""
import re
from pathlib import Path
import docx

ROOT = Path("D:/Desktop/shandou/报告库")
OLD = re.compile(r"frame_\d{4}_\d{2}-\d{2}(?:\.jpg)?")
NEW = re.compile(r"frame_(\d{6})_(\d{2})h(\d{2})m(\d{2})s000ms\.jpg")

issues = []
tot = {"files": 0, "new_refs": 0, "old_residue": 0, "land_fail": 0, "no_index": 0}
for sub in ["旧56项目", "开荒", "海之呼唤", "赛季"]:
    d = ROOT / sub / "精编"
    if not d.exists():
        continue
    for f in sorted(d.glob("*.docx")):
        full = "\n".join(p.text for p in docx.Document(str(f)).paragraphs)
        tot["files"] += 1
        i = full.rfind("溯源索引")
        tail = full[i:] if i > 0 else ""
        body = full[:i] if i > 0 else full
        # 旧格式残留(全文)
        olds = OLD.findall(full)
        if olds:
            tot["old_residue"] += 1
            issues.append(f"旧格式残留 {len(olds)} 处: {sub}/{f.name[:30]}")
        # 新格式引用落地
        news = NEW.findall(tail)
        if not news:
            if "溯源索引" not in full:
                tot["no_index"] += 1
                issues.append(f"无溯源索引: {sub}/{f.name[:30]}")
            continue
        tot["new_refs"] += len(news)
        # 取首条 + 每条索引行的目录
        dm = re.search(r"源静帧目录[:：]\s*(.+)", full)
        dp = Path(dm.group(1).strip().rstrip("/")) if dm else None
        # 检查所有新引用(按索引行解析目录)
        lines = tail.split("\n")
        cur_dp = dp
        for ln in lines:
            mm = re.match(r"^\[\d\d:\d\d-\d\d:\d\d\]\s+(.+)", ln.strip())
            if mm:
                dm2 = re.search(r"(.+?)\s+frame_", mm.group(1))
                cur_dp = Path(dm2.group(1).strip().rstrip("/")) if dm2 else cur_dp
            for nm in NEW.findall(ln):
                idx, hh, mm_, ss = nm
                sec = int(hh) * 3600 + int(mm_) * 60 + int(ss)
                cand = cur_dp / f"frame_{idx}_{hh}h{mm_}m{ss}s000ms.jpg"
                if not cand.exists() and cur_dp:
                    # 开荒合并: 子目录
                    found = any((sd / cand.name).exists() for sd in cur_dp.iterdir() if sd.is_dir())
                    if not found:
                        tot["land_fail"] += 1
                        issues.append(f"引用不落地: {sub}/{f.name[:26]} {cand.name}")

print(f"精编文件: {tot['files']}")
print(f"新格式引用总数: {tot['new_refs']}")
print(f"旧格式残留文件: {tot['old_residue']}")
print(f"引用不落地: {tot['land_fail']}")
print(f"无溯源索引: {tot['no_index']}")
print(f"\n问题清单 {len(issues)} 条:")
for x in issues[:30]:
    print("  -", x)
