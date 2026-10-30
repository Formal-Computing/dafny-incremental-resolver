#!/usr/bin/env python3
from pathlib import Path
import sys
dest=Path(sys.argv[1])
text=dest.read_text(encoding="utf-8-sig")
base=Path(__file__).resolve().parent.parent
method=(base/"tests/dafny/ResearchDifferentialMethod.txt").read_text() + "\n" + (base/"tests/dafny/ResearchBenchmarkMethod.txt").read_text()
anchor="  [Fact]\n  public async Task ChangedImportAffectsExport() {"
assert "ResearchDifferentialTrace" not in text
assert anchor in text
dest.write_text(text.replace(anchor,method+"\n"+anchor,1),encoding="utf-8")
print("Installed differential methods")
