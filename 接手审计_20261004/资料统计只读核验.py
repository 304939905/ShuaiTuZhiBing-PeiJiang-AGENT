"""Read local project metadata; write only this handover snapshot. No network."""
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "资料库"
OUT = Path(__file__).with_name("资料统计快照.json")

def load(name):
    return json.loads((LIB / name).read_text(encoding="utf-8"))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def local_path(old):
    normalized = str(old).replace("\\", "/")
    prefix = "D:/Desktop/shandou/"
    return ROOT / normalized[len(prefix):] if normalized.startswith(prefix) else ROOT / normalized

result = {"checked_at": datetime.now(timezone(timedelta(hours=8))).isoformat(), "workspace": str(ROOT), "client_audit_date": "2026-10-04"}
files = [p for p in ROOT.rglob("*") if p.is_file()]
result["workspace_snapshot"] = {"files": len(files), "bytes": sum(p.stat().st_size for p in files), "docx_in_report_library": len(list((ROOT / "报告库").rglob("*.docx")))}
result["schema"] = {}
for name in ["hero.json", "hero_extra.json", "skill.json", "skill_extra.json", "jineng_list.json", "gear_id.json", "official_skill_db.json", "official_merged_whitelist.json", "aa_rate_supplement.json"]:
    data = load(name)
    result["schema"][name] = {"type": "array" if isinstance(data, list) else "object", "count": len(data), "top_fields": sorted(data[0] if isinstance(data, list) and data else data), "sha256": digest(LIB / name), "file_modified": datetime.fromtimestamp((LIB / name).stat().st_mtime, timezone(timedelta(hours=8))).isoformat()}
    if isinstance(data, dict):
        result["schema"][name]["collection_counts"] = {k: len(v) for k,v in data.items() if isinstance(v,(list,dict))}
whitelist = load("official_merged_whitelist.json")
result["whitelist"] = {k: {"count": len(whitelist[k]), "flat_string_array": isinstance(whitelist[k],list) and all(isinstance(v,str) for v in whitelist[k]), "unique_count": len(set(whitelist[k]))} for k in ["heroes","skills","gears","forge_traits","unit_traits"]}
heroes = {str(h["hero_id"]): h for h in load("hero.json")}
quality_chain = Counter()
quality_unmatched = []
for extra in load("hero_extra.json"):
    hero = heroes.get(str(extra["id"]))
    if hero and str(hero["skill_init"]) == str(extra["methodId"]):
        quality_chain[f'{extra["quality"]} => {hero["quality"]}'] += 1
    else:
        quality_unmatched.append({"id": extra["id"], "name": extra["name"], "methodId":extra["methodId"]})
result["hero_quality_exact_id_and_method"] = {"counts": dict(quality_chain), "unmatched": quality_unmatched}
result["hero_raw_quality_counts"] = dict(Counter(str(h["quality"]) for h in heroes.values()))
skills = load("official_skill_db.json")["skills"]
result["skill_acquisition"] = {
    "season_tags": dict(Counter(s.get("season_tag","missing") for s in skills.values())),
    "acquisition_stage_status": dict(Counter(s.get("acquisition_stage_status","missing") for s in skills.values())),
    "provisional_by_obtain_method":dict(Counter(s.get("obtain_method","missing") for s in skills.values() if s.get("acquisition_stage_status")=="provisional_default")),
    "missing_stage_count":sum(not s.get("acquisition_stage") for s in skills.values()),
    "blank_desc_count":sum(not s.get("desc") for s in skills.values()),
    "blank_type_count":sum(not s.get("type") for s in skills.values()),
    "full_records": len(skills),
    "samples": {name: {k:s.get(k) for k in ["id","season_code","season_tag","obtain_method","acquisition_stage","acquisition_stage_status"]} for name,s in skills.items() if name in {"衡轭","令无空悬","形兵之极","磐阵善守"}}
}
aa = load("aa_rate_supplement.json")
result["aa_supplement"] = {"meta": aa["meta"], "coverage": aa["coverage"], "source_file_exists": (ROOT / aa["meta"]["source"]).exists()}
rows = load("reports_index_rows.json")
report_results=[]
for row in rows:
    actual = ROOT / row["rel"]
    report_results.append({"no": row["no"], "rel": row["rel"], "indexed_out_exists": Path(row["out"]).exists(), "local_rel_exists": actual.is_file(), "sha256_matches": actual.is_file() and digest(actual) == row.get("content_sha256"), "source_retirement_ready": row.get("source_retirement_ready"), "reliability_grade": row.get("reliability_grade"), "p0_audit_status": row.get("p0_audit_status"), "cross_acceptance_status": row.get("cross_acceptance_status"), "light_audit_status":row.get("light_audit_status")})
result["reports"] = {"rows":len(rows), "unique_rel":len({r["rel"] for r in rows}), "current_rel_exists":sum(r["local_rel_exists"] for r in report_results), "indexed_out_exists":sum(r["indexed_out_exists"] for r in report_results), "current_sha256_matches":sum(r["sha256_matches"] for r in report_results), "source_retirement_ready_counts":dict(Counter(str(r["source_retirement_ready"]) for r in report_results)), "reliability_grade_counts":dict(Counter(r["reliability_grade"] for r in report_results)), "nonindexed_docx":[p.relative_to(ROOT).as_posix() for p in (ROOT/"报告库").rglob("*.docx") if p.relative_to(ROOT).as_posix() not in {r["rel"] for r in rows}], "records":report_results}
strategy = LIB / "策略知识库"
result["strategy_library"] = {"directory_exists":strategy.is_dir(),"file_count":sum(p.is_file() for p in strategy.rglob("*"))}
chain = load("evidence_chain.json")
chain_counts = defaultdict(Counter)
for record in chain["records"]:
    for field in ["report","frames_dir","video","transcript","contact_sheet_dir","alt_reports"]:
        values = record.get(field)
        values = values if isinstance(values,list) else [values] if values else []
        for value in values:
            chain_counts[field]["recorded"] += 1
            chain_counts[field]["old_absolute_exists"] += Path(value).exists()
            chain_counts[field]["rebased_local_exists"] += local_path(value).exists()
result["evidence_chain"] = {"stored_stats":chain["stats"], "current_path_counts":{k:dict(v) for k,v in chain_counts.items()}, "role":"historical source index generated before source retirement; rebasing cannot restore retired assets"}
audits = {}
for p in (LIB/"audit_work").glob("20260913*/*.json"):
    data=json.loads(p.read_text(encoding="utf-8-sig"))
    audits[p.relative_to(ROOT).as_posix()]={"type":"array" if isinstance(data,list) else "object", "count":len(data), "top_fields":sorted(data[0] if isinstance(data,list) and data else data)}
result["historical_audit_json_schema"] = audits
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:v for k,v in result.items() if k not in {"schema","historical_audit_json_schema"} and k!="reports"},ensure_ascii=False,indent=2))
print(json.dumps({"reports":{k:v for k,v in result["reports"].items() if k!="records"},"saved":str(OUT)},ensure_ascii=False,indent=2))
