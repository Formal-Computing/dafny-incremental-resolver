#!/usr/bin/env python3
"""Fail-closed comparison for per-revision SATLIB LSP diagnostics and semantic requests.

Produces human-readable and JSON summaries only after all 28 four-mode traces exist.
"""
import json
from pathlib import Path
import sys

repo = Path(__file__).resolve().parents[1]
root = Path(sys.argv[1])
manifest = json.loads((repo / "tests/air/corpus/manifest.json").read_text())
cases = manifest["cases"]
modes = ("original", "patched-baseline", "experimental", "fresh")
failures = []
report = {"schema": "satlib-semantic-differential-v1", "n_documents": len(cases),
          "n_revisions_per_document": 4, "cases": [], "comparisons": 0,
          "semantic_comparisons": 0, "diagnostic_comparisons": 0, "failures": failures}
for case in cases:
    id = case["id"]
    traces = {}
    for mode in modes:
        filename = root / f"{mode}-matrix-{id}.json"
        if not filename.is_file():
            failures.append(f"missing {filename.name}")
            continue
        doc = json.loads(filename.read_text())
        trace = doc["samples"]
        if len(trace) != 4:
            failures.append(f"{filename.name}: expected four revisions")
            continue
        traces[mode] = trace
    if len(traces) != 4:
        continue
    stages = [x["stage"] for x in traces["fresh"]]
    if stages != ["open", "suffix-value-edit", "provider-value-edit", "prefix-origin-shift"]:
        failures.append(f"{id}: wrong stages {stages}")
    fresh = traces["fresh"]
    entry = {"id": id, "clauses": case["clauses"], "sat_class": case["expected_sat_class"],
             "modes": {}, "stage_comparisons": []}
    for mode in modes:
        t = traces[mode]
        entry["modes"][mode] = {"hits": sum(x["hits"] for x in t[1:]),
                                 "misses": sum(x["misses"] for x in t[1:]),
                                 "stages": [{"stage": x["stage"], "hits": x["hits"],
                                             "misses": x["misses"], "tracked": x["tracked"]} for x in t[1:]]}
        for i in range(4):
            if t[i]["source"] != fresh[i]["source"]:
                failures.append(f"{id}: input differs at revision {i} for {mode}")
            if mode == "fresh": continue
            for kind in ("diagnostics", "semantic"):
                report["comparisons"] += 1
                report[kind[:-1] + "_comparisons" if kind=="diagnostics" else "semantic_comparisons"] += 1
                if t[i][kind] != fresh[i][kind]:
                    failures.append(f"{id}: {kind} mismatch for {mode}, revision {i}")
    report["cases"].append(entry)
out = root / "satlib-matrix-report.json"
out.write_text(json.dumps(report, indent=2) + "\n")
lines = ["# SATLIB multi-document LSP differential experiment", "",
         f"Documents: {len(cases)}; original clauses: {sum(x['clauses'] for x in cases)}; "
         f"revisions per document: 4; four resolver modes.", "",
         "| Instance | Clauses | Original (hits/misses) | Experimental (hits/misses) |",
         "|---|---:|---:|---:|"]
for c in report["cases"]:
    o = c["modes"]["original"]; e = c["modes"]["experimental"]
    lines.append(f"| {c['id']} | {c['clauses']} | {o['hits']}/{o['misses']} | {e['hits']}/{e['misses']} |")
lines += ["", f"Independent comparisons: {report['comparisons']}, errors: {len(failures)}.",
          "Each comparison is a mode/revision/observable-kind pair, not an independent program.",
          "Fresh semantic resolution still retains the parser cache.",
          "These are transformed CNF documents, *not* SAT-solver runs or evidence of end-to-end verifier soundness."]
if failures: lines += ["", "## Mismatches", ""] + [f"- {f}" for f in failures]
(root / "satlib-matrix-report.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
if failures: sys.exit(1)
