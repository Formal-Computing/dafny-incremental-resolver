#!/usr/bin/env python3
"""Calibrate restricted two-mode immutable-export oracle against stale alias reuse.

Uses real archived or current LSP JSON. Never modifies input traces.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

FILES = (
    "fresh-semantic-export_summary.json",
    "immutable-export-export_summary.json",
    "fresh-semantic-negative_alias.json",
    "immutable-export-negative_alias.json",
    "fresh-semantic-verification-export-proof.json",
    "immutable-export-verification-export-proof.json",
)


def calibrate(source: Path) -> None:
    missing = [name for name in FILES if not (source / name).is_file()]
    if missing:
        raise ValueError("Required two-mode traces missing: " + ", ".join(missing))
    fresh = json.loads((source / "fresh-semantic-negative_alias.json").read_text())
    records = fresh.get("records", [])
    if len(records) != 4:
        raise ValueError("Fresh negative-alias trace must contain four revisions")
    withdrawn = records[2]
    if not withdrawn.get("diagnostics") or (withdrawn.get("semantic") or {}).get("definitions"):
        raise ValueError("Fresh oracle did not observe an unresolved alias lookup on revision 2")

    with tempfile.TemporaryDirectory(prefix="dafny-immutable-alias-calibration-") as temp:
        root = Path(temp)
        for name in FILES:
            shutil.copyfile(source / name, root / name)
        target = root / "immutable-export-negative_alias.json"
        data = json.loads(target.read_text())
        altered = data["records"][2]
        altered["diagnostics"] = []
        altered["semantic"] = {
            "definitions": [{"uri": "file:///deliberately-stale-provider.dfy",
                             "from": [0, 0], "to": [0, 7]}],
            "hover": "\x60\x60\x60dafny\nfunction Missing(): int\n\x60\x60\x60",
        }
        target.write_text(json.dumps(data, indent=2) + "\n")
        comparator = Path(__file__).with_name("compare_immutable_export.py")
        run = subprocess.run([sys.executable, str(comparator), str(root)],
                             capture_output=True, text=True, check=False, timeout=30)
        expected = ("UNEXPECTED_NEGATIVE_BINDING_PRESENCE", "DIAGNOSTIC_DIFFERENCE")
        if run.returncode != 1 or not all(signal in run.stdout for signal in expected):
            raise ValueError("Injected stale alias binding not rejected: " + run.stdout[-1000:])
    print("PASS: two-mode immutable-export oracle rejects a corrupted stale alias binding")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: calibrate_immutable_alias.py <real-two-mode-trace-directory>")
    try:
        calibrate(Path(sys.argv[1]))
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as error:
        raise SystemExit("FAIL: " + str(error))
