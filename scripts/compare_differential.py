#!/usr/bin/env python3
"""Fail closed if any required trace is missing or any observable differs."""
import json, pathlib, sys
root=pathlib.Path(sys.argv[1])
modes=("original","patched-baseline","experimental","fresh")
scenarios=("independent","dependency","shadowing","roster","recovery")
report=[]
for scenario in scenarios:
    traces={}
    for mode in modes:
        file=root/f"{mode}-{scenario}.json"
        if not file.exists():
            report.append({"scenario":scenario,"mode":mode,"status":"MISSING"})
        else:
            traces[mode]=json.loads(file.read_text())["records"]
    if len(traces)!=len(modes):
        continue
    expected_sources=[[r["source"] for r in t] for t in traces.values()]
    if any(x!=expected_sources[0] for x in expected_sources[1:]):
        report.append({"scenario":scenario,"status":"INPUT_MISMATCH"})
        continue
    for i, oracle in enumerate(traces["fresh"]):
        for mode in ("original","patched-baseline","experimental"):
            got=traces[mode][i]["diagnostics"]
            wanted=oracle["diagnostics"]
            report.append({"scenario":scenario,"revision":i,"mode":mode,
              "status":"MATCH" if got==wanted else "DIFFERENCE",
              "actual":got if got!=wanted else None,"oracle":wanted if got!=wanted else None})
        if traces["patched-baseline"][i]["diagnostics"]!=traces["original"][i]["diagnostics"]:
            report.append({"scenario":scenario,"revision":i,"mode":"baseline-equivalence","status":"DIFFERENCE"})
result={"schema":"dafny-differential-v1","comparison":report}
(root/"differential-report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
bad=[x for x in report if x["status"]!="MATCH"]
print("Differential comparisons:",len(report)-len(bad),"match,",len(bad),"fail/missing")
for x in bad: print("FAIL:",x["scenario"],x.get("revision"),x.get("mode"),x["status"])
sys.exit(1 if bad else 0)
