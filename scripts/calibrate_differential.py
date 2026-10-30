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

if len(sys.argv) != 2:
    raise SystemExit("usage: calibrate_differential.py <successful-four-mode-traces>")
source = pathlib.Path(sys.argv[1])
required = list(source.glob("*-*.json"))
if len(required) < 20:
    raise SystemExit("Expected 20 four-mode trace JSON files")
with tempfile.TemporaryDirectory(prefix="dafny-research-calibration-") as td:
    dest = pathlib.Path(td)
    for path in required:
        if path.name != "differential-report.json":
            shutil.copyfile(path, dest / path.name)
    target = dest / "experimental-dependency.json"
    obj = json.loads(target.read_text())
    # The second dependency revision genuinely has a diagnostic in the oracle.
    diagnostics = obj["records"][1]["diagnostics"]
    if not diagnostics:
        raise SystemExit("Expected a diagnostic to corrupt in dependency revision 1")
    diagnostics[0]["message"] += " [FAULT-INJECTED]"
    target.write_text(json.dumps(obj, indent=2))
    run = subprocess.run(
        [sys.executable, str(pathlib.Path(__file__).with_name("compare_differential.py")), str(dest)],
        capture_output=True, text=True, timeout=30)
    if run.returncode != 1 or "DIFFERENCE" not in run.stdout:
        raise SystemExit("FAIL: comparison did not detect deliberately corrupted diagnostic")
    print("PASS: mutated experimental diagnostic was rejected by fresh oracle")
