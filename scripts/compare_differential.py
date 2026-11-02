#!/usr/bin/env python3
"""Strict differential oracle: two fresh paths and three persistent-cache modes.

This compares selected observable snapshots only. It does not prove type or
verification equivalence for unobserved locations.
"""
import json
import pathlib
import sys

SCENARIOS = (
    "independent", "dependency", "shadowing", "roster", "recovery", "negative",
    "fault_probe", "stress_graph", "stress_scope", "air_semantic",
)
EXTENDED_SCENARIOS = SCENARIOS + ("air_semantic_662",)
MODES = ("original", "patched-baseline", "experimental", "fresh-semantic", "fresh")
CACHED = ("original", "patched-baseline", "experimental")
QUERIED = {
    "dependency", "shadowing", "negative", "fault_probe", "stress_graph",
    "stress_scope", "air_semantic",
}

def compare(root: pathlib.Path, scenarios=SCENARIOS):
    report = []
    counts = {}
    def record(scenario, revision, mode, field, got, wanted):
        match = got == wanted
        report.append({
            "scenario": scenario, "revision": revision, "mode": mode,
            "observable": field, "status": "MATCH" if match else "DIFFERENCE",
            **({ "actual": got, "oracle": wanted } if not match else {})
        })
    for scenario in scenarios:
        traces = {}
        for mode in MODES:
            path = root / f"{mode}-{scenario}.json"
            if not path.is_file():
                report.append({"scenario": scenario, "mode": mode, "status": "MISSING"})
                continue
            try:
                data = json.loads(path.read_text())
                if data.get("mode") != mode or data.get("scenario") != scenario:
                    raise ValueError("Mode/scenario metadata differs from file name")
                traces[mode] = data["records"]
            except (ValueError, KeyError, TypeError) as e:
                report.append({"scenario": scenario, "mode": mode,
                               "status": "INVALID", "reason": str(e)})
        if len(traces) != len(MODES):
            continue
        sizes = {mode: len(records) for mode, records in traces.items()}
        if len(set(sizes.values())) != 1 or next(iter(sizes.values())) == 0:
            report.append({"scenario": scenario, "status": "REVISION_COUNT_MISMATCH",
                           "sizes": sizes})
            continue
        sources = [[rev["source"] for rev in recs] for recs in traces.values()]
        if any(other != sources[0] for other in sources[1:]):
            report.append({"scenario": scenario, "status": "INPUT_MISMATCH"})
            continue
        counts[scenario] = next(iter(sizes.values()))
        for index, wanted in enumerate(traces["fresh-semantic"]):
            no_cache = traces["fresh"][index]
            for field in ("diagnostics", "semantic"):
                if field not in wanted or field not in no_cache:
                    report.append({"scenario": scenario, "revision": index,
                                   "status": "MISSING_OBSERVABLE", "observable": field})
                    continue
                record(scenario, index, "fresh-vs-fresh-semantic",
                       field, no_cache[field], wanted[field])
            if scenario in QUERIED and wanted.get("semantic") is None:
                report.append({"scenario": scenario, "revision": index,
                               "status": "MISSING_SEMANTIC_QUERY"})
            for mode in CACHED:
                for field in ("diagnostics", "semantic"):
                    if field not in wanted or field not in traces[mode][index]:
                        report.append({"scenario": scenario, "revision": index,
                                       "mode": mode, "observable": field,
                                       "status": "MISSING_OBSERVABLE"})
                        continue
                    record(scenario, index, mode, field,
                           traces[mode][index][field], wanted[field])
    return {"schema": "dafny-differential-v2",
            "scenarios": counts, "comparison": report}


def main():
    if len(sys.argv) not in (2, 4):
        raise SystemExit("usage: compare_differential.py <trace-dir> [--scenarios air_semantic_662]")
    root = pathlib.Path(sys.argv[1])
    if len(sys.argv) == 4:
        if sys.argv[2] != "--scenarios" or sys.argv[3] != "air_semantic_662":
            raise SystemExit("Only the independent 662-clause suite is supported as an override")
        scenarios = ("air_semantic_662",)
    else:
        scenarios = SCENARIOS
    data = compare(root, scenarios=scenarios)
    root.mkdir(parents=True, exist_ok=True)
    (root / "differential-report.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2))
    bad = [x for x in data["comparison"] if x["status"] != "MATCH"]
    print("Revisions by scenario:", data["scenarios"])
    print("Differential comparisons:", len(data["comparison"]) - len(bad),
          "match,", len(bad), "fail/missing")
    for x in bad[:25]:
        print("FAIL:", x.get("scenario"), x.get("revision"),
              x.get("mode"), x.get("observable"), x["status"])
    if len(bad) > 25:
        print("... remaining failures:", len(bad) - 25)
    return 1 if bad or len(data["scenarios"]) != len(scenarios) else 0


if __name__ == "__main__":
    sys.exit(main())
