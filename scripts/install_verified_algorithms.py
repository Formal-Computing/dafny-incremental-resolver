#!/usr/bin/env python3
"""Embed purpose-built Dafny program in the pinned LSP regression harness."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
dest=Path(sys.argv[1])
body=dest.read_text(encoding="utf-8-sig")
src=(root/"tests/handwritten/VerifiedAlgorithms.dfy").read_text()
method=(root/"tests/handwritten/ResearchVerifiedAlgorithms.txt").read_text()
assert method.count("HANDWRITTEN_EMBEDDED_FIXTURE")==1
method=method.replace("HANDWRITTEN_EMBEDDED_FIXTURE", '@"'+src.replace('"','""')+'"')
anchor="  [Fact]\n  public async Task ChangedImportAffectsExport() {"
assert anchor in body and "ResearchVerifiedAlgorithms(" not in body
dest.write_text(body.replace(anchor,method+"\n"+anchor,1),encoding="utf-8")
print("Installed proof-bearing Dafny LSP trace",src.count("\n"),"lines")
