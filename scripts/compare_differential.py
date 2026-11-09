#!/usr/bin/env python3
"""Strict differential oracle: two fresh paths and three persistent-cache modes.

This compares selected observable snapshots only. It does not prove type or
verification equivalence for unobserved locations.
"""
import json
import pathlib
import re
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
NEGATIVE_DIAGNOSTIC_COUNTS = (1, 0, 1, 0)
NEGATIVE_SEMANTIC_PRESENT = (False, True, False, True)

def stable_hover(value):
    """Compare language/type markup, not asynchronous verification progress.

    Retain every Dafny code block verbatim (ignoring surrounding blank lines).
    If no Dafny code blocks exist, compare the complete hover string. We do NOT
    claim equivalence of proof/verifier outcomes from this normalized value.
    """
    if value is None or not isinstance(value, str):
        return value
    blocks = re.findall(r"```dafny\s*\n([\s\S]*?)```", value)
    if blocks:
        return {"dafny-signatures": [block.strip() for block in blocks]}
    return {"exact-hover": value}


def stable_semantic(value):
    if not isinstance(value, dict):
        return value
    return {**value, "hover": stable_hover(value.get("hover"))}


def compare(root: pathlib.Path, scenarios=SCENARIOS):
    report = []
    counts = {}
    volatile_hover_differences = []
    def record(scenario, revision, mode, field, got, wanted):
        # A pair of absent optional semantic queries carries no evidence.
        # Do not inflate match counts by treating None == None as a test.
        if field == "semantic" and got is None and wanted is None:
            return
        if field == "semantic" and isinstance(got, dict) and isinstance(wanted, dict):
            if got.get("hover") != wanted.get("hover") and stable_hover(got.get("hover")) == stable_hover(wanted.get("hover")):
                volatile_hover_differences.append({
                    "scenario": scenario, "revision": revision, "mode": mode,
                    "classification": "same Dafny signature; verification-progress hover differs"
                })
            got = stable_semantic(got)
            wanted = stable_semantic(wanted)
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
        if scenario == "negative" and next(iter(sizes.values())) != 4:
            report.append({"scenario": scenario, "status": "WRONG_NEGATIVE_REVISION_COUNT",
                           "expected": 4, "actual": next(iter(sizes.values()))})
            continue
        for index, wanted in enumerate(traces["fresh-semantic"]):
            if scenario == "negative":
                # This trace is deliberately missing -> resolved -> missing ->
                # resolved. Check the independent oracle itself against the
                # expected state, so matching stale traces cannot pass.
                diagnostic_count = len(wanted.get("diagnostics", []))
                expected_count = NEGATIVE_DIAGNOSTIC_COUNTS[index]
                if diagnostic_count != expected_count:
                    report.append({"scenario": scenario, "revision": index,
                                   "status": "UNEXPECTED_NEGATIVE_DIAGNOSTIC_COUNT",
                                   "expected": expected_count, "actual": diagnostic_count})
                if index in (0, 2) and diagnostic_count == 1:
                    diagnostic = wanted["diagnostics"][0]
                    if (not diagnostic.get("message") or not diagnostic.get("severity") or
                            not diagnostic.get("code") or not diagnostic.get("source") or
                            diagnostic.get("from") is None or diagnostic.get("to") is None):
                        report.append({"scenario": scenario, "revision": index,
                                       "status": "INCOMPLETE_NEGATIVE_DIAGNOSTIC"})
                semantic_present = wanted.get("semantic") is not None
                expected_semantic = NEGATIVE_SEMANTIC_PRESENT[index]
                if semantic_present != expected_semantic:
                    report.append({"scenario": scenario, "revision": index,
                                   "status": "UNEXPECTED_NEGATIVE_SEMANTIC_PRESENCE",
                                   "expected": expected_semantic, "actual": semantic_present})
                if expected_semantic and semantic_present:
                    semantic = wanted["semantic"]
                    if (not semantic.get("definitions") or
                            not isinstance(semantic.get("hover"), str) or
                            not re.search(r"\bfunction\s+Missing\s*\(\s*\)\s*:\s*int\b",
                                          semantic["hover"])):
                        report.append({"scenario": scenario, "revision": index,
                                       "status": "INCOMPLETE_NEGATIVE_SEMANTIC_ORACLE"})
            if scenario == "negative" and index == 2 and len(wanted.get("diagnostics", [])) == 1:
                if wanted["diagnostics"] != traces["fresh-semantic"][0].get("diagnostics"):
                    report.append({"scenario": scenario, "revision": index,
                                   "status": "UNSTABLE_NEGATIVE_DIAGNOSTIC"})
            no_cache = traces["fresh"][index]
            for field in ("diagnostics", "semantic"):
                if field not in wanted or field not in no_cache:
                    report.append({"scenario": scenario, "revision": index,
                                   "status": "MISSING_OBSERVABLE", "observable": field})
                    continue
                record(scenario, index, "fresh-vs-fresh-semantic",
                       field, no_cache[field], wanted[field])
            if (scenario in QUERIED and wanted.get("semantic") is None and
                    not (scenario == "negative" and
                         not NEGATIVE_SEMANTIC_PRESENT[index])):
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
        if scenario == "negative":
            # A pair of absent queries is noninformative; reject the trace even
            # when all implementations and fresh oracles agree on None.
            informative = sum(
                1 for records in traces.values()
                for record_value in records
                if record_value.get("semantic") is not None
            )
            if informative != len(MODES) * sum(NEGATIVE_SEMANTIC_PRESENT):
                report.append({"scenario": scenario,
                               "status": "NONINFORMATIVE_NEGATIVE_SEMANTIC_COMPARISON",
                               "expected_present_observations": len(MODES) * sum(NEGATIVE_SEMANTIC_PRESENT),
                               "actual_present_observations": informative})
    return {"schema": "dafny-differential-v3",
            "scenarios": counts,
            "comparison": report,
            "volatileVerificationHoverCount": len(volatile_hover_differences),
            "volatileVerificationHovers": volatile_hover_differences,
            "normalization": "Exact diagnostics and definition targets; all fenced Dafny signature/type blocks when present, otherwise exact hover. Dynamic verification progress is reported separately, not asserted equivalent."}


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
    print("Verification-progress hover differences (not semantic results):",
          data["volatileVerificationHoverCount"])
    for x in bad[:25]:
        print("FAIL:", x.get("scenario"), x.get("revision"),
              x.get("mode"), x.get("observable"), x["status"])
    if len(bad) > 25:
        print("... remaining failures:", len(bad) - 25)
    return 1 if bad or len(data["scenarios"]) != len(scenarios) else 0


if __name__ == "__main__":
    sys.exit(main())
