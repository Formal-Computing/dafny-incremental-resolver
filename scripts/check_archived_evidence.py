#!/usr/bin/env python3
"""Read-only verification of archived AIR LSP experiment statistics.

This checks report consistency, not Dafny semantic correctness or speedup.
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "experiments" / "results"
RUNS = ("2026-11-01-profiler-41329209347", "2026-11-01-mixed-profile-41329569628")
EXPECTED = {"patched-baseline": (4, 32), "experimental": (28, 8)}

def read_json(path: Path):
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))

def check(condition, reason):
    if not condition:
        raise AssertionError(reason)

for folder in RUNS:
    root = RESULTS / folder
    print(f"RUN {folder}")
    for mode, (want_hits, want_misses) in EXPECTED.items():
        trace = read_json(root / f"{mode}-air-satlib.json")
        measured = [
            item for item in trace["samples"]
            if item.get("edit") == "same-length-RevisionTag" and not item.get("warmup")
        ]
        hits = sum(int(x["resolutionHits"]) for x in measured)
        misses = sum(int(x["resolutionMisses"]) for x in measured)
        check(len(measured) == 4, f"{folder}/{mode}: not four measured edits")
        check((hits, misses) == (want_hits, want_misses),
              f"{folder}/{mode}: expected {(want_hits, want_misses)}, got {(hits, misses)}")
        print(f"  {mode}: {hits} hits, {misses} misses across {len(measured)} measured edits")

mixed = RESULTS / "2026-11-01-mixed-profile-41329569628"
trace = read_json(mixed / "experimental-air-mixed.json")
expected = [
    ("provider-value-changed", ("MISS", "HIT", "MISS")),
    ("provider-value-restored", ("MISS", "HIT", "MISS")),
    ("independent-suffix-insertion", ("HIT", "HIT", "HIT")),
    ("independent-suffix-restoration", ("HIT", "HIT", "HIT")),
    ("prefix-position-shift", ("MISS", "MISS", "MISS")),
]
modules = ("AirUF50", "AirAIM50", "AIR_Inspector")
check(len(trace["samples"]) == len(expected), "mixed trace must have five edits")
for sample, (expected_edit, expected_decisions) in zip(trace["samples"], expected):
    check(sample["edit"] == expected_edit, f"edit order mismatch: {sample['edit']}")
    keyed = {m["name"]: m for m in sample["trackedModules"]}
    decisions = []
    for name in modules:
        item = keyed[name]
        check(bool(item.get("hit")) != bool(item.get("miss")), f"ambiguous cache result {name}")
        decisions.append("HIT" if item["hit"] else "MISS")
    check(tuple(decisions) == expected_decisions, f"{expected_edit}: unexpected {decisions}")
    print(f"  {expected_edit}: {', '.join(f'{n}={v}' for n,v in zip(modules, decisions))}")
print("PASS: two archived profiler summaries and five mixed-edit cache outcomes are internally consistent.")
print("NOTE: This checks recorded events, not semantic equivalence or speed improvement.")
