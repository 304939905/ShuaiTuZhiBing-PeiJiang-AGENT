#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cross-validate threshold_db skill names against official lists."""
import json, os

BASE = r"D:/Desktop/shandou/资料库"

with open(os.path.join(BASE, "threshold_db.json"), "r", encoding="utf-8") as f:
    db = json.load(f)

with open(os.path.join(BASE, "official_jineng_names.json"), "r", encoding="utf-8") as f:
    general = set(json.load(f)["names"])

with open(os.path.join(BASE, "official_jineng_names_ext.json"), "r", encoding="utf-8") as f:
    ext = set(json.load(f)["names"])

# Collect skill names from threshold_db
skills = set()
for cat in db["categories"]:
    for entry in cat["entries"]:
        name = entry["skill"]
        # Strip growth suffix
        base_name = name.split("（")[0]
        skills.add(base_name)

missing_general = sorted(skills - general)
missing_ext = sorted(skills - ext)
in_general = sorted(skills & general)
in_ext = sorted(skills & ext)

print(f"Total unique skills in threshold_db: {len(skills)}")
print(f"In official general list: {len(in_general)}")
print(f"In official extended list: {len(in_ext)}")
print(f"Missing from general: {len(missing_general)}")
print(f"Missing from extended: {len(missing_ext)}")
print("")
print("=== Missing from extended (likely OCR/transcription errors or unofficial names) ===")
for s in missing_ext:
    print(f"  - {s}")
print("")
print("=== In extended but not general (hero自带战法) ===")
for s in sorted(in_ext - general):
    print(f"  - {s}")
