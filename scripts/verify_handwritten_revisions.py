#!/usr/bin/env python3
"""Test full Dafny proof obligations at five controlled revisions using a fresh CLI."""
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
source=Path(__file__).resolve().parents[1]/"tests/handwritten/VerifiedAlgorithms.dfy"
dafny=sys.argv[1]
text=source.read_text()
assert "function Offset(x: int): int { x + 1 }" in text
assert "RevisionTag(): int { 10 }" in text
suffix=text.replace("RevisionTag(): int { 10 }","RevisionTag(): int { 11 }")
broken=suffix.replace("Offset(x: int): int { x + 1 }","Offset(x: int): int { x + 2 }")
cases=[("original",text,12,0),("unrelated-edit",suffix,12,0),
       ("changed-provider",broken,10,2),("recovered-provider",suffix,12,0),
       ("prefix-position-shift","// Shift before modules\n"+suffix,12,0)]
rows=[]
with tempfile.TemporaryDirectory(prefix="dafny-verified-") as temp:
 for stage,contents,expected_ok,expected_error in cases:
  path=Path(temp)/(stage+".dfy")
  path.write_text(contents)
  result=subprocess.run([dafny,"verify",str(path)],capture_output=True,text=True)
  output=result.stdout+"\n"+result.stderr
  match=re.search(r"Dafny program verifier finished with (\d+) verified, (\d+) errors",output)
  if not match:
   raise RuntimeError(f"{stage}: cannot parse verifier output: {output}")
  good,bad=map(int,match.groups())
  assert (good,bad)==(expected_ok,expected_error),(stage,good,bad)
  assert (result.returncode==0)==(bad==0),stage
  rows.append({"stage":stage,"verified":good,"errors":bad,"cli_exit":result.returncode,
               "sha256_dafny":hashlib.sha256(contents.encode()).hexdigest()})
  print(f"{stage}: {good} verified, {bad} errors; expected")
out=Path(sys.argv[2]) if len(sys.argv)>2 else Path("handwritten-verification.json")
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps({"schema":"handwritten-proof-obligation-v1",
                           "source":"tests/handwritten/VerifiedAlgorithms.dfy",
                           "notes":"Fresh CLI verification per revision, not cached LSP verification",
                           "cases":rows},indent=2)+"\n")
print("Saved",out)
