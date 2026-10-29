#!/usr/bin/env python3
"""Insert the experiment into Dafny's existing CachingTest harness.

The upstream checkout is disposable. The source under tests/dafny is the
canonical experiment definition in this repository.
"""
from pathlib import Path
import sys

source = Path(sys.argv[1])
method = Path(__file__).resolve().parent.parent / "tests/dafny/SameFileCachingMethod.txt"
content = source.read_text(encoding="utf-8-sig")
anchor = "  [Fact]\n  public async Task ChangedImportAffectsExport() {"
addition = method.read_text(encoding="utf-8")
if "SameFileIndependentModuleEdit" in content:
    raise SystemExit("Experiment already installed; refusing duplicate insertion")
if anchor not in content:
    raise SystemExit("Upstream test insertion point not found")
source.write_text(content.replace(anchor, addition + "\n" + anchor, 1), encoding="utf-8")
print(f"Inserted {method.name} into {source}")
