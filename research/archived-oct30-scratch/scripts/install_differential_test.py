#!/usr/bin/env python3
"""Install the differential research test into pinned upstream CachingTest."""
from pathlib import Path
import sys

source = Path(sys.argv[1])
addition = (Path(__file__).resolve().parent.parent / "tests/dafny/ResearchDifferentialMethod.txt").read_text(encoding="utf-8")
content = source.read_text(encoding="utf-8-sig")
anchor = "  [Fact]\n  public async Task ChangedImportAffectsExport() {"
if "ResearchDifferentialTrace" in content:
    raise SystemExit("Differential test already inserted")
assert anchor in content, "Pinned upstream anchor changed"
source.write_text(content.replace(anchor, addition + "\n" + anchor, 1), encoding="utf-8")
print("Installed differential tracing methods")
