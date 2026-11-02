#!/usr/bin/env python3
"""Install seven separate, checksum-recorded SATLIB LSP tests into pinned CachingTest.cs."""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
dest = Path(sys.argv[1])
text = dest.read_text(encoding="utf-8-sig")
anchor = "  [Fact]\n  public async Task ChangedImportAffectsExport() {"
assert anchor in text and "ResearchSatlibMatrix(" not in text
method = (root / "tests/air/ResearchSatlibMatrix.txt").read_text()
manifest = json.loads((root / "tests/air/corpus/manifest.json").read_text())
rows = []
for case in manifest["cases"]:
    name = case["id"]
    src = (root / "tests/air/corpus" / (name + ".dfy")).read_text()
    import hashlib
    assert hashlib.sha256(src.encode()).hexdigest() == case["sha256_dafny"]
    rows.append('      "' + name + '" => @"' + src.replace('"', '""') + '",')
assert method.count("SATLIB_MATRIX_SWITCH") == 1
method = method.replace("SATLIB_MATRIX_SWITCH", "\n".join(rows))
dest.write_text(text.replace(anchor, method + "\n" + anchor, 1), encoding="utf-8")
print(f"Installed {len(rows)} SATLIB document scenarios")
