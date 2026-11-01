#!/usr/bin/env python3
"""Install AIR/SATLIB large case-study fixture in pinned Dafny integration test."""
from pathlib import Path
import sys
dest=Path(sys.argv[1])
root=Path(__file__).resolve().parent.parent
fixture=(root/"tests/air/satlib_case_study.dfy").read_text()
method=(root/"tests/air/ResearchAirSatlibCaseStudy.txt").read_text()
mixed=(root/"tests/air/ResearchAirMixedEdits.txt").read_text()
assert "AIR_SATLIB_EMBEDDED_FIXTURE" in method and "AIR_SATLIB_EMBEDDED_FIXTURE" in mixed
mixed=mixed.replace("AIR_SATLIB_EMBEDDED_FIXTURE", '@"'+fixture.replace('"','""')+'"')
method=method.replace("AIR_SATLIB_EMBEDDED_FIXTURE", '@"'+fixture.replace('"','""')+'"')
body=dest.read_text(encoding="utf-8-sig")
anchor="  [Fact]\n  public async Task ChangedImportAffectsExport() {"
assert anchor in body and "ResearchAirSatlibCaseStudy" not in body
dest.write_text(body.replace(anchor, method+"\n"+mixed+"\n"+anchor,1),encoding="utf-8")
print(f"Installed real AIR/SATLIB case study: {fixture.count(chr(10))} lines")
