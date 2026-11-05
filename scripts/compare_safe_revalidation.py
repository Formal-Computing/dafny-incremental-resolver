#!/usr/bin/env python3
"""Compare safe audited fresh-resolution against independent fresh semantic oracle."""
import json
from pathlib import Path
import sys

SCENARIOS = ("independent", "dependency", "shadowing", "roster", "recovery",
             "negative", "fault_probe", "stress_graph", "stress_scope", "air_semantic")
VERIFIER_SCENARIOS = ("assertion-toggle", "dependency-proof", "independent-proof")
MODES = ("fresh-semantic", "safe-audit")

def validate(directory):
    results=[]
    count_verifier=0
    count_diagnostics=0
    count_semantic=0
    # Imported normalization must be identical to the previous semantic
    # stress analysis, while keeping asynchronous verification progress separate.
    from compare_differential import stable_semantic, QUERIED
    for category, scenarios, kind, expected_counts in (
        ("verification", VERIFIER_SCENARIOS, "verification",
         {x: 4 for x in VERIFIER_SCENARIOS}),
        ("semantic", SCENARIOS, "semantic",
         {"independent":4,"dependency":4,"shadowing":3,"roster":3,
          "recovery":4,"negative":4,"fault_probe":3,
          "stress_graph":24,"stress_scope":18,"air_semantic":8}),
    ):
        for scenario in scenarios:
            traces={}
            for mode in MODES:
                filename=(f"{mode}-verification-{scenario}.json" if category=="verification"
                          else f"{mode}-{scenario}.json")
                path=directory/filename
                if not path.exists():
                    results.append((scenario, mode, "MISSING"))
                    continue
                data=json.loads(path.read_text())
                if data.get("mode")!=mode or data.get("scenario")!=scenario:
                    results.append((scenario,mode,"INVALID_METADATA"))
                    continue
                traces[mode]=data["records"]
            if len(traces)!=2:continue
            a,b=(traces[x] for x in MODES)
            if len(a)!=len(b) or len(a)!=expected_counts[scenario]:
                results.append((scenario,"both","COUNT_MISMATCH"))
                continue
            for i,(x,y) in enumerate(zip(a,b)):
                if x.get("source") != y.get("source") or x.get("revision")!=y.get("revision"):
                    results.append((scenario,i,"SOURCE_MISMATCH"))
                    continue
                if category=="verification":
                    if not x["verification"] or not y["verification"]:
                        results.append((scenario,i,"MISSING_VERIFICATION"))
                    elif any(v["outcome"] not in ("Correct","Error")
                         for v in x["verification"]+y["verification"]):
                        results.append((scenario,i,"NOT_TERMINAL"))
                    elif x["verification"]!=y["verification"]:
                        results.append((scenario,i,"VERIFIER_DIFFERENCE"))
                    else:count_verifier+=1
                else:
                    if x.get("diagnostics") != y.get("diagnostics"):
                        results.append((scenario,i,"DIAGNOSTIC_DIFFERENCE"))
                    else:count_diagnostics+=1
                    if scenario in QUERIED and (x.get("semantic") is None or y.get("semantic") is None):
                        results.append((scenario,i,"MISSING_SELECTED_QUERY"))
                    elif x.get("semantic") is not None or y.get("semantic") is not None:
                        if stable_semantic(x.get("semantic")) != stable_semantic(y.get("semantic")):
                            results.append((scenario,i,"SEMANTIC_DIFFERENCE"))
                        else:count_semantic+=1
    output={"schema":"dafny-controlled-reattachment-v1",
            "verifier_revision_pairs":count_verifier,
            "diagnostic_revision_pairs":count_diagnostics,
            "selected_semantic_revision_pairs":count_semantic,
            "errors":[{"scenario":e[0],"position":e[1],"error":e[2]} for e in results],
            "limitation":"Candidate audit may be incomplete; results are always freshly resolved, no cache speedup and no proof of an optimizing reattachment implementation."}
    (directory/"safe-revalidation-report.json").write_text(json.dumps(output,indent=2))
    print("Fresh vs safe audit:",count_verifier,"verifier pairs,",
          count_diagnostics,"diagnostic pairs,",count_semantic,"selected semantic pairs",
          "errors",len(results))
    for e in results[:20]:print("FAIL",*e)
    return not results and (count_verifier,count_diagnostics,count_semantic)==(12,75,64)

if __name__ == "__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: compare_safe_revalidation.py <trace-folder>")
    if not validate(Path(sys.argv[1])):sys.exit(1)
