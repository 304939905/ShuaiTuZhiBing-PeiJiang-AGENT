"""Rebase accepted report paths, preserving every other index field and DOCX."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "资料库" / "reports_index_rows.json"
AUDIT = Path(__file__).resolve().parent
BEFORE = AUDIT / "reports_index_rows_路径修复前.json"
PROOF = AUDIT / "主索引路径迁移验收.json"

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

original_bytes = INDEX.read_bytes()
old_rows = json.loads(original_bytes.decode("utf-8-sig"))
assert len(old_rows) == 67, "Unexpected index size; stop instead of modifying records."
assert len({r["rel"] for r in old_rows}) == 67, "Duplicate relative report paths."
new_rows = []
proof_rows = []
root_resolved = ROOT.resolve()
for row in old_rows:
    report = (ROOT / row["rel"]).resolve()
    assert report.is_relative_to(root_resolved), f"Report outside workspace: {row['no']}"
    assert report.is_file(), f"Report missing: {row['no']}"
    actual_hash = sha256(report)
    assert actual_hash == row["content_sha256"], f"Report hash changed: {row['no']}"
    new_row = dict(row)
    new_row["out"] = report.as_posix()
    assert {k:v for k,v in row.items() if k != "out"} == {k:v for k,v in new_row.items() if k != "out"}
    new_rows.append(new_row)
    proof_rows.append({"no":row["no"],"rel":row["rel"],"old_out":row["out"],"new_out":new_row["out"],"content_sha256":actual_hash})
if BEFORE.exists():
    assert BEFORE.read_bytes() == original_bytes, "Before snapshot already exists and differs; do not overwrite history."
else:
    BEFORE.write_bytes(original_bytes)
INDEX.write_text(json.dumps(new_rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
checked_rows=json.loads(INDEX.read_text(encoding="utf-8"))
assert len(checked_rows)==len(old_rows)
for old,current in zip(old_rows,checked_rows):
    assert {k:v for k,v in old.items() if k != "out"} == {k:v for k,v in current.items() if k != "out"}
    assert Path(current["out"]).is_file()
    assert sha256(Path(current["out"]))==old["content_sha256"]
proof={"date":"2026-10-04","scope":"Only out rebased; relative path, content, order, dates and acceptance fields preserved","before_index_sha256":hashlib.sha256(original_bytes).hexdigest(),"after_index_sha256":sha256(INDEX),"rows":67,"all_out_readable":True,"all_other_fields_equal":True,"all_report_sha256_unchanged":True,"records":proof_rows}
PROOF.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PASS: 67 paths rebased; all other index fields and report hashes unchanged.")
