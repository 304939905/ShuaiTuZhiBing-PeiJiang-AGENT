#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""来源可追溯性检查器的最小回归测试。"""

import json
import tempfile
from pathlib import Path

from docx import Document
from source_provenance_check import check_docx, check_json, validate_source_deletions


with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "sample.json"

    path.write_text(json.dumps({"sources": ["画面证据：frames/example"]}, ensure_ascii=False), encoding="utf-8")
    assert check_json(path) == []

    path.write_text(json.dumps({"sources": []}, ensure_ascii=False), encoding="utf-8")
    assert any(f["code"] == "SOURCE_EMPTY" for f in check_json(path))

    path.write_text(json.dumps({"sources": ["网易大神资料"], "source_deletions": [{"source": "旧链接"}]}, ensure_ascii=False), encoding="utf-8")
    codes = {f["code"] for f in check_json(path)}
    assert "EXTERNAL_NAME_NO_URL" in codes
    assert "SOURCE_DELETION_REASON" in codes

assert validate_source_deletions([{"source": "旧链接", "reason": "链接失效"}], Path("ok.json")) == []

with tempfile.TemporaryDirectory() as tmp:
    docx_path = Path(tmp) / "trace.docx"
    doc = Document()
    doc.add_paragraph("四、溯源索引（时间段 → 静帧路径）")
    doc.add_paragraph("[00:00-00:19] frames/example/frame_0000.jpg")
    doc.save(docx_path)
    assert not any(f["code"] == "REPORT_SOURCE_MISSING" for f in check_docx(docx_path))

print("source_provenance_check: PASS")
