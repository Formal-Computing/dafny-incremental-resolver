#!/usr/bin/env python3
"""Fail closed for selected diagnostics and navigation across handwritten edits."""
from pathlib import Path
import json,re,sys
root=Path(sys.argv[1])
modes=("original","patched-baseline","experimental","fresh")
traces={}
for mode in modes:
 p=root/f"{mode}-handwritten.json"
 assert p.is_file(), f"missing {p}"
 traces[mode]=json.loads(p.read_text())["samples"]
 assert len(traces[mode])==5
base=traces["fresh"]
stages=["open","independent-edit","provider-contract-broken",
        "provider-contract-restored","prefix-origin-shift"]
assert [s["stage"] for s in base]==stages
comparisons=0
volatile_hover_differences=0
def stable_hover(hover):
 assert isinstance(hover,str) and hover
 blocks=re.findall(r"```dafny\s*(.*?)```",hover,re.S)
 assert len(blocks)==1, "missing/ambiguous stable Dafny signature"
 prefix=hover.split("```dafny",1)[0]
 assert ("Verification not started yet" in prefix or "Still verifying..." in prefix
         or ("Success:" in prefix and "Resource usage:" in prefix)
         or "Error:" in prefix), "unrecognized hover prefix"
 return blocks[0].strip()
for m in modes:
 t=traces[m]
 assert [s["stage"] for s in t]==stages
 for i in range(5):
  assert t[i]["source"]==base[i]["source"],(m,i,"source mismatch")
  if m=="fresh":continue
  for field in ("diagnostics",):
   comparisons+=1
   assert t[i][field]==base[i][field],(m,i,field,"diverged from fresh resolver")
  comparisons+=1
  assert t[i]["semantic"]["definitions"]==base[i]["semantic"]["definitions"],(m,i,"definitions mismatch")
  comparisons+=1
  if t[i]["semantic"]["hover"]!=base[i]["semantic"]["hover"]:
   volatile_hover_differences+=1
  assert stable_hover(t[i]["semantic"]["hover"])==stable_hover(base[i]["semantic"]["hover"]),(m,i,"hover type signature mismatch")
report={"kind":"handwritten-proof-bearing-differential-v1",
        "revisions":5,"comparisons":comparisons,
        "volatile_verifier_hover_status_differences":volatile_hover_differences,
        "observedFreshDiagnosticCounts":[len(s["diagnostics"]) for s in base],
        "modes":{m:{"hits":sum(x["hits"] for x in v[1:]),"misses":sum(x["misses"] for x in v[1:])} for m,v in traces.items()},
        "note":"Diagnostics/hover/definition agreement is not a general verification-soundness proof; separate CLI proof obligations are recorded."}
(root/"handwritten-differential-report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
