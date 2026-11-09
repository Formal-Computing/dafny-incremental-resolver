#!/usr/bin/env python3
"""Validate the machine-readable nonempty feasibility audit (stdlib only)."""
import argparse
import json
import sys
from pathlib import Path

PIN = "de36f2ec1f9c530080eff7929ae28229f45da069"
DEPENDENCIES = {17, 18, 21, 22, 25}


def validate(doc):
    errors = []
    if not isinstance(doc, dict):
        return ["document must be an object"]
    required = {"schema_version", "upstream", "dependencies", "recommendation",
                "strict_gate", "candidate_classes", "unknowns", "prerequisites",
                "minimal_experiment", "claims_not_made"}
    if not required <= doc.keys():
        return ["missing required fields: " + ", ".join(sorted(required - doc.keys()))]
    if doc["schema_version"] != 1:
        errors.append("unsupported schema_version")
    upstream = doc["upstream"]
    if not isinstance(upstream, dict) or upstream.get("revision") != PIN:
        errors.append("pinned upstream revision mismatch")
    if doc["recommendation"] != "NO-GO":
        errors.append("feasibility recommendation must remain NO-GO")
    if set(doc["dependencies"]) != DEPENDENCIES:
        errors.append("explicit dependencies must be #17, #18, #21, #22, #25")
    gate = doc["strict_gate"]
    if not isinstance(gate, str) or not all(x in gate.lower() for x in
                                             ("nonempty", "resolve fresh", "forces a miss", "never authorizes")):
        errors.append("strict gate must fail closed for nonempty modules")
    classes = doc["candidate_classes"]
    if not isinstance(classes, list) or not classes:
        errors.append("candidate_classes must be a nonempty array")
    elif not any(x.get("genuinely_nonempty") is True and x.get("feasibility", "").startswith("NO-GO")
                 for x in classes if isinstance(x, dict)):
        errors.append("at least one genuinely nonempty NO-GO class must be recorded")
    for field in ("unknowns", "prerequisites", "claims_not_made"):
        if not isinstance(doc[field], list) or not doc[field]:
            errors.append(f"{field} must be a nonempty array")
    experiment = doc["minimal_experiment"]
    if not isinstance(experiment, dict) or "not run" not in experiment.get("mode", ""):
        errors.append("minimal experiment must be proposed and explicitly not run")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("audit", nargs="?", type=Path,
                        default=Path(__file__).resolve().parents[1] /
                        "research/nonempty-feasibility-2026-11-09.json")
    args = parser.parse_args()
    try:
        doc = json.loads(args.audit.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(exc, file=sys.stderr)
        return 2
    errors = validate(doc)
    if errors:
        print("\n".join(errors))
        return 1
    print("nonempty feasibility audit valid: strict NO-GO; experiment not run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
