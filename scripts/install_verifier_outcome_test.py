#!/usr/bin/env python3
from pathlib import Path
import sys
target=Path(sys.argv[1])
source=Path(__file__).resolve().parent.parent / "tests/dafny/ResearchVerificationOutcomeMethod.txt"
body=target.read_text(encoding="utf-8-sig")
anchor="  [Fact]\n  public async Task ParentModuleProjectFileVerification() {"
assert anchor in body
assert "ResearchVerificationOutcomeTrace" not in body
# VerificationStatusTest already uses models, Range, Xunit, IO and System.
extra=(Path(__file__).resolve().parent.parent / "tests/dafny/ResearchControlledModeMethod.txt").read_text()
target.write_text(body.replace(anchor,source.read_text()+"\n"+extra+"\n"+anchor,1))
print("Installed verifier outcome test")
