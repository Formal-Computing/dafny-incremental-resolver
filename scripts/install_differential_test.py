#!/usr/bin/env python3
from pathlib import Path
import sys
dest=Path(sys.argv[1])
text=dest.read_text(encoding="utf-8-sig")
text="using OmniSharp.Extensions.LanguageServer.Protocol.Document;\n" + text
base=Path(__file__).resolve().parent.parent
method=(base/"tests/dafny/ResearchDifferentialMethod.txt").read_text()
# Embed checksum-pinned AIR/SATLIB Dafny corpus into the differential test,
# rather than only measuring cache-hit traces on the larger program.
fixture=(base/"tests/air/satlib_case_study.dfy").read_text()
assert method.count("AIR_STRESS_FIXTURE") >= 2
method=method.replace("AIR_STRESS_FIXTURE", '@"'+fixture.replace('"','""')+'"')
fixture662=(base/"tests/air/satlib_stress_662.dfy").read_text()
assert method.count("AIR_STRESS_662_FIXTURE") >= 2
method=method.replace("AIR_STRESS_662_FIXTURE", '@"'+fixture662.replace('"','""')+'"')
method += "\n" + (base/"tests/dafny/ResearchBenchmarkMethod.txt").read_text()
method += "\n" + (base/"tests/dafny/ResearchImmutableExportSummaryMethod.txt").read_text()
method += "\n" + (base/"tests/dafny/ResearchNonemptyFallbackMethod.txt").read_text()
method += "\n" + (base/"tests/dafny/ResearchAuditCollisionMethod.txt").read_text()
method += "\n" + (base/"tests/dafny/ResearchIssue18NegativeAliasMethod.txt").read_text()
anchor="  [Fact]\n  public async Task ChangedImportAffectsExport() {"
assert "ResearchDifferentialTrace" not in text
assert anchor in text
dest.write_text(text.replace(anchor,method+"\n"+anchor,1),encoding="utf-8")
print("Installed differential methods")
