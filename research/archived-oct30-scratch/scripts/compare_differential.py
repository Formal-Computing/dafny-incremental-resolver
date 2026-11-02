#!/usr/bin/env python3
"""Diff only post-resolution diagnostics for persistent baselines and fresh oracle."""
import argparse, json, pathlib, sys
p = argparse.ArgumentParser()
p.add_argument("results", type=pathlib.Path)
p.add_argument("--output", type=pathlib.Path, default=None)
args = p.parse_args()
scenarios = ["independent", "dependency", "shadowing", "roster", "error-recovery"]
modes = ["original", "baseline", "experimental", "fresh"]
rows = []
for scenario in scenarios:
    files = {m: args.results / f"{m}-{scenario}.json" for m in modes}
    missing = [m for m,f in files.items() if not f.is_file()]
    if missing:
        rows.append({"scenario":scenario,"result":"MISSING","missing":missing})
        continue
    traces = {m: json.loads(f.read_text(encoding="utf-8"))["trace"] for m,f in files.items()}
    # All modes must see byte-identical input revisions. No normalization of source.
    if len({json.dumps([rev["source"] for rev in t]) for t in traces.values()}) != 1:
        rows.append({"scenario":scenario,"result":"INPUT_MISMATCH"})
        continue
    for revision in range(len(traces["fresh"])):
        oracle = traces["fresh"][revision]["diagnostics"]
        for mode in ["original", "baseline", "experimental"]:
            got = traces[mode][revision]["diagnostics"]
            rows.append({"scenario":scenario,"revision":revision,"mode":mode,
              "result":"PASS" if got == oracle else "DIFFERENCE",
              "expected":oracle if got != oracle else None,
              "actual":got if got != oracle else None})
        if traces["original"][revision]["diagnostics"] != traces["baseline"][revision]["diagnostics"]:
            rows.append({"scenario":scenario,"revision":revision,"mode":"baseline-integrity","result":"DIFFERENCE"})
report = {"schema":"research-differential-v1","cases":rows}
result_json = json.dumps(report, ensure_ascii=False, indent=2)
if args.output:
    args.output.write_text(result_json,encoding="utf-8")
else:
    print(result_json)
tot = sum(r["result"] == "PASS" for r in rows)
bad = [r for r in rows if r["result"] != "PASS"]
print(f"DIFFERENTIAL: {tot} matches, {len(bad)} differences/missing", file=sys.stderr)
if bad:
    for r in bad: print(f"FAIL: {r['scenario']} {r.get('revision')} {r.get('mode')} {r['result']}", file=sys.stderr)
sys.exit(bool(bad))
