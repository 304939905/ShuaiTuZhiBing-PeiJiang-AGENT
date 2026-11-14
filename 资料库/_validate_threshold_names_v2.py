#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cross-validate threshold_db skill names against comprehensive official lists."""
import json, os

BASE = r"D:/Desktop/shandou/资料库"

with open(os.path.join(BASE, "threshold_db.json"), "r", encoding="utf-8") as f:
    db = json.load(f)

# Build comprehensive skill name set
def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

names = set()

# official_skill_db.json: keys are names
skill_db = load_json(os.path.join(BASE, "official_skill_db.json"))
names.update(skill_db.keys())

# skill.json: list of objects with name
skill_json = load_json(os.path.join(BASE, "skill.json"))
for s in skill_json:
    names.add(s.get("name"))

# skill_extra.json: list of objects with name
skill_extra = load_json(os.path.join(BASE, "skill_extra.json"))
for s in skill_extra:
    names.add(s.get("name"))

# official_jineng_names_ext.json
ext = load_json(os.path.join(BASE, "official_jineng_names_ext.json"))
names.update(ext.get("names", []))

# supplement
sup = load_json(os.path.join(BASE, "official_jineng_supplement.json"))
names.update(sup.get("skills", []))

# Filter empty
names = {n for n in names if n}

# Collect skill names from threshold_db
skills = set()
for cat in db["categories"]:
    for entry in cat["entries"]:
        name = entry["skill"]
        base_name = name.split("（")[0]
        skills.add(base_name)

missing = sorted(skills - names)
in_db = sorted(skills & names)

print(f"Total unique skills in threshold_db: {len(skills)}")
print(f"In comprehensive official db: {len(in_db)}")
print(f"Missing: {len(missing)}")
print("")
print("=== In official db ===")
for s in in_db:
    print(f"  ✓ {s}")
print("")
print("=== Missing from all official sources (need verification) ===")
for s in missing:
    print(f"  ? {s}")
