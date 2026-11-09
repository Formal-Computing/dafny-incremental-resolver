#!/usr/bin/env python3
"""Check that the *diagnostic comparator* detects a deliberately corrupted trace.

This does not inject a faulty resolver into Dafny; that remains a separate
end-to-end correctness obligation.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from compare_differential import MODES, SCENARIOS

if len(sys.argv) != 2:
    raise SystemExit("usage: calibrate_differential.py <five-mode-LSP-traces>")
source = pathlib.Path(sys.argv[1])
required = [source / f"{mode}-{scenario}.json"
            for scenario in SCENARIOS for mode in MODES]
missing = [path.name for path in required if not path.is_file()]
if missing:
    raise SystemExit("Missing pinned-Dafny oracle artifacts: " + ", ".join(missing))
with tempfile.TemporaryDirectory(prefix="dafny-research-calibration-") as td:
    dest = pathlib.Path(td)
    for path in required:
        if path.name != "differential-report.json":
            shutil.copyfile(path, dest / path.name)
    def remove_revision_zero_diagnostic(obj):
        obj["records"][0]["diagnostics"] = []

    def change_only_definition_target(obj):
        record = obj["records"][1]
        if record["diagnostics"] != [] or not record["semantic"]["definitions"]:
            raise SystemExit("Expected resolved Missing() with no diagnostics at revision 1")
        record["semantic"]["definitions"][0]["uri"] += ".corrupt"

    def stale_failure_after_provider_add(obj):
        record = obj["records"][1]
        if record["diagnostics"]:
            raise SystemExit("Expected no diagnostics after provider adds Missing at revision 1")
        # Keep consumer source unchanged; change only observed diagnostic output.
        record["diagnostics"] = [{"message": "stale unresolved Missing", "severity": "Error",
                                  "code": "R", "source": "dafny", "from": [0, 0],
                                  "to": [0, 1], "related": []}]

    # Corrupt the fresh oracle itself for the required revision-0 diagnostic
    # control, and persistent experimental outputs for the two differential
    # implementation errors.
    def cli_check_file(filename, mutator, expected, label):
        for path in required:
            shutil.copyfile(path, dest / path.name)
        target = dest / filename
        obj = json.loads(target.read_text())
        mutator(obj)
        target.write_text(json.dumps(obj, indent=2))
        run = subprocess.run(
            [sys.executable, str(pathlib.Path(__file__).with_name("compare_differential.py")), str(dest)],
            capture_output=True, text=True, timeout=30)
        if run.returncode != 1 or expected not in run.stdout:
            raise SystemExit(f"FAIL: {label} calibration did not report {expected}; stdout={run.stdout}")

    cli_check_file("fresh-semantic-negative.json", remove_revision_zero_diagnostic,
                   "UNEXPECTED_NEGATIVE_DIAGNOSTIC_COUNT", "missing revision-0 unresolved diagnostic")
    cli_check_file("experimental-negative.json", change_only_definition_target,
                   "DIFFERENCE", "go-to-definition target corruption")
    cli_check_file("experimental-negative.json", stale_failure_after_provider_add,
                   "DIFFERENCE", "stale failure after provider adds Missing")
    # Calibrate an actual stale POSITIVE in the CANDIDATE while the fresh
    # oracle remains untouched: Missing was withdrawn at revision 2.
    for path in required:
        shutil.copyfile(path, dest / path.name)
    alias = dest / "experimental-negative_alias.json"
    if not alias.is_file():
        raise SystemExit("Missing experimental alias lookup trace")
    obj = json.loads(alias.read_text())
    if len(obj.get("records", [])) != 4:
        raise SystemExit("Alias negative-lookup trace must have four revisions")
    withdrawn = obj["records"][2]
    if not withdrawn.get("diagnostics") or (withdrawn.get("semantic") or {}).get("definitions"):
        raise SystemExit("Expected unresolved lookup after provider withdrawal")
    withdrawn["diagnostics"] = []
    withdrawn["semantic"] = {
        "definitions": [{"uri": "file:///stale-provider.dfy", "from": [0, 0], "to": [0, 7]}],
        "hover": "```dafny\nfunction Missing(): int\n```",
    }
    alias.write_text(json.dumps(obj, indent=2))
    run = subprocess.run(
        [sys.executable, str(pathlib.Path(__file__).with_name("compare_differential.py")), str(dest)],
        capture_output=True, text=True, timeout=30)
    if run.returncode != 1 or "DIFFERENCE" not in run.stdout:
        raise SystemExit("FAIL: stale alias-binding corruption was not rejected")
    print("PASS: corrupted diagnostic and stale experimental alias binding were rejected")
