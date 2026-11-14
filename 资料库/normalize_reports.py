import os, json, glob, re
REPORTS = "D:/Desktop/shandou/资料库/reports_json"

def norm(data):
    shots = data.get("screenshots", [])
    mapping = {}
    for i, s in enumerate(shots):
        old = s.get("id")
        new = f"图{i+1}"
        if old != new:
            s["id"] = new
            if old is not None:
                mapping[old] = new
    if not mapping:
        return False
    for sec in data.get("knowledge", []):
        for pt in sec.get("points", []):
            if pt.get("shot") in mapping:
                pt["shot"] = mapping[pt["shot"]]
    for e in data.get("evidence_index", []):
        if e.get("screenshot") in mapping:
            e["screenshot"] = mapping[e["screenshot"]]
    return True

def main():
    changed = 0
    for jp in sorted(glob.glob(os.path.join(REPORTS, "*.json"))):
        with open(jp, encoding="utf-8") as f:
            data = json.load(f)
        if norm(data):
            with open(jp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            changed += 1
            print("NORMALIZED", os.path.basename(jp))
    print("DONE changed=", changed)

if __name__ == "__main__":
    main()
