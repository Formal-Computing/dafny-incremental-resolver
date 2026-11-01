#!/usr/bin/env python3
"""Compare named module reuse across the curated mixed edit cases."""
import json, sys
from pathlib import Path
root=Path(sys.argv[1])
modes=("original","fresh","patched-baseline","experimental")
data={m:json.loads((root/(m+"-air-mixed.json")).read_text()) for m in modes}
names=[x["edit"] for x in data["original"]["samples"]]
assert len(names)==5
assert all([x["edit"] for x in data[m]["samples"]]==names for m in modes)
lines=["# AIR SATLIB mixed-edit experiment","",
       "Five controlled modifications to a 298-clause Dafny program. Cache results are observations, not proofs of safe reuse.",
       "",
       "| Edit | Original hits/misses | Experimental hits/misses | Named module effect in experimental |",
       "|---|---:|---:|---|"]
summary={"edits":[],"modes":{},"notes":["Original and experimental are different process runs, not paired CPU samples.","The parser cache stays enabled in fresh mode.","Synchronous profiler figures use current-thread allocations and inclusive regions, not exclusive CPU time."]}
for m in modes:
    summary["modes"][m]=[{"edit":s["edit"],"elapsedMs":s["milliseconds"],"hits":s["resolutionHits"],"misses":s["resolutionMisses"],"trackedModules":s["trackedModules"],
        "resolverProfileEvents":len(s.get("profile",[]))} for s in data[m]["samples"]]
for i,edit in enumerate(names):
    orig=data["original"]["samples"][i]; exp=data["experimental"]["samples"][i]
    exp_mods=exp["trackedModules"]
    effects=", ".join(x["name"]+":"+("HIT" if x["hit"] else "MISS" if x["miss"] else "n/a") for x in exp_mods)
    lines.append("| "+edit+" | "+str(orig["resolutionHits"])+"/"+str(orig["resolutionMisses"])+
            " | "+str(exp["resolutionHits"])+"/"+str(exp["resolutionMisses"])+
            " | "+effects+" |")
    summary["edits"].append({"edit":edit,"original":dict(hits=orig["resolutionHits"],misses=orig["resolutionMisses"]),"experimental":dict(hits=exp["resolutionHits"],misses=exp["resolutionMisses"]), "trackedExperimental":exp_mods})
lines+=["",
"Interpretation: provider-value edits should invalidate AirUF50 and its dependent AIR_Inspector, but allow unrelated AirAIM50 reuse. Independent suffix-length edits should leave earlier module positions unchanged. A prefix insertion shifts earlier module coordinates and should fail closed. Actual behavior must be checked above.",
"",
"Test data: original AIR SATLIB CNFs, not representative hand-written Dafny. Resolver-only CPU and peak RSS are not measured."]
(root/"air-mixed-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
(root/"air-mixed-report.md").write_text("\n".join(lines)+"\n")
print("\n".join(lines[:12]))
