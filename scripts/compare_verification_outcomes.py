#!/usr/bin/env python3
"""Compare completed Dafny verifier outcomes. Never infer them from hover."""
import json
from pathlib import Path
import sys

MODES = ("original", "fresh", "fresh-semantic", "patched-baseline", "experimental")
SCENARIOS = ("assertion-toggle", "dependency-proof", "independent-proof")

def compare(directory):
    comparisons = []
    for scenario in SCENARIOS:
        traces = {}
        for mode in MODES:
            path = directory / f"{mode}-verification-{scenario}.json"
            if not path.exists():
                comparisons.append({"scenario": scenario, "mode": mode, "status": "MISSING"})
                continue
            data = json.loads(path.read_text())
            if data.get("mode") != mode or data.get("scenario") != scenario:
                comparisons.append({"scenario": scenario, "mode": mode, "status": "BAD_METADATA"})
                continue
            traces[mode] = data["records"]
        if len(traces) != len(MODES):
            continue
        lens = [len(x) for x in traces.values()]
        if lens != [4] * len(MODES):
            comparisons.append({"scenario": scenario, "status": "WRONG_REVISION_COUNT", "lens": lens})
            continue
        for i in range(4):
            reference = traces["fresh-semantic"][i]
            if any(r[i]["source"] != reference["source"] or r[i]["revision"] != i
                   for r in traces.values()):
                comparisons.append({"scenario":scenario,"revision":i,"status":"SOURCE_MISMATCH"})
                continue
            for mode in MODES:
                got = traces[mode][i]["verification"]
                expected = reference["verification"]
                # Do NOT remove, reorder, or normalize Correct/Error statuses.
                if not expected or not got or any(
                    x["outcome"] not in ("Correct", "Error") for x in got):
                    status = "NOT_COMPLETED"
                else:
                    status = "MATCH" if got == expected else "DIFFERENCE"
                comparisons.append({"scenario":scenario,"revision":i,"mode":mode,
                                    "status":status,**({"got":got,"expected":expected}
                                       if status != "MATCH" else {})})
    bad = [x for x in comparisons if x["status"] != "MATCH"]
    report = {"schema":"dafny-verifier-outcomes-v1", "comparisons":comparisons,
              "matches":len(comparisons)-len(bad), "failures":len(bad)}
    (directory/"verification-report.json").write_text(json.dumps(report,indent=2))
    print("Completed verifier outcome comparisons:",report["matches"],
          "matches,",report["failures"],"failures")
    for failure in bad[:15]:
        print("FAIL",failure["scenario"],failure.get("revision"),failure.get("mode"),failure["status"])
    return not bad and len(comparisons) == len(SCENARIOS)*4*len(MODES)

def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        for scenario in SCENARIOS:
            for mode in MODES:
                d={"mode":mode,"scenario":scenario,"records":[
                    {"revision":i,"source":f"source_{i}",
                     "verification":[{"from":[0,0],"to":[0,5],
                                      "outcome":"Error" if i==1 else "Correct"}]}
                    for i in range(4)]}
                (root/f"{mode}-verification-{scenario}.json").write_text(json.dumps(d))
        assert compare(root)
        f=root/"experimental-verification-assertion-toggle.json"
        data=json.loads(f.read_text())
        data["records"][1]["verification"][0]["outcome"]="Correct"
        f.write_text(json.dumps(data))
        assert not compare(root), "Must detect unsound verifier success"
        f.unlink()
        assert not compare(root), "Must fail on incomplete mode"
    print("Verifier outcome comparator self-tests passed")

if __name__ == "__main__":
    if len(sys.argv)==2 and sys.argv[1]=="--selftest":
        selftest()
    elif len(sys.argv)==2:
        if not compare(Path(sys.argv[1])):
            sys.exit(1)
    else:
        raise SystemExit("usage: compare_verification_outcomes.py --selftest | <results>")
