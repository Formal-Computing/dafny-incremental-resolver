#!/usr/bin/env python3
"""Fail-closed completeness gate for explicitly configured archived evidence.

This checks presence and informativeness of recorded observations. It does not
rerun Dafny or turn historical artifacts into results for the current checkout.
"""
import argparse
import json
from pathlib import Path
import re
import sys

SCRIPT_VERSION = "1.0.0"
TERMINAL = {"Correct", "Error"}
VOLATILE_PROGRESS = re.compile(r"\n?\s*(?:\d+\s+verified,\s*\d+\s+errors?|verification (?:is )?(?:in progress|complete)|verified at)\b[^\n]*", re.I)


def stable_hover(value):
    """Preserve code/signatures while removing only recognized async progress lines."""
    if not isinstance(value, str):
        return value
    blocks = re.findall(r"```dafny\s*\n([\s\S]*?)```", value)
    if blocks:
        return {"dafny-signatures": [VOLATILE_PROGRESS.sub("", x).strip() for x in blocks]}
    return {"exact-hover": VOLATILE_PROGRESS.sub("", value).strip()}


def informative(value):
    return value not in (None, "", [], {})


def load_trace(root, spec, errors):
    path = root / spec["path"]
    if not path.is_file() or path.stat().st_size == 0:
        errors.append({"status": "MISSING_OR_EMPTY_FILE", "file": spec["path"]})
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append({"status": "INVALID_JSON", "file": spec["path"], "reason": str(exc)})
        return None
    if obj.get("mode") != spec["mode"] or obj.get("scenario") != spec["scenario"]:
        errors.append({"status": "BAD_METADATA", "file": spec["path"]})
        return None
    records = obj.get("records")
    if not isinstance(records, list) or len(records) != spec["revisions"]:
        errors.append({"status": "WRONG_REVISION_COUNT", "file": spec["path"],
                       "expected": spec["revisions"], "actual": len(records) if isinstance(records, list) else None})
        return None
    for i, rec in enumerate(records):
        if not isinstance(rec, dict) or rec.get("revision") != i or not informative(rec.get("source")):
            errors.append({"status": "EMPTY_OR_BAD_OBSERVATION", "file": spec["path"], "revision": i})
            return None
    return records


def validate(config_path):
    config_path = Path(config_path).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    root = (config_path.parent / config["bundle_root"]).resolve()
    errors, skips, loaded = [], [], {}
    required = config.get("observations", [])
    declared = {x["path"] for x in required}
    for spec in required:
        loaded[spec["path"]] = load_trace(root, spec, errors)
    # Every result JSON in the configured group must be declared, so omitted files/groups cannot hide.
    for path in sorted(root.glob(config.get("group_glob", "*.json"))):
        if path.name not in declared and path.name not in config.get("ignore_files", []):
            errors.append({"status": "UNDECLARED_RESULT_GROUP", "file": path.name})

    counts = {"diagnostics": 0, "definition_typed_hover": 0, "terminal_verification": 0}
    for pair in config.get("comparisons", []):
        left, right = loaded.get(pair["left"]), loaded.get(pair["right"])
        if left is None or right is None:
            continue
        kind = pair["kind"]
        for i, (a, b) in enumerate(zip(left, right)):
            if a.get("source") != b.get("source"):
                errors.append({"status": "SOURCE_MISMATCH", "kind": kind, "revision": i})
                continue
            if kind == "diagnostics":
                x, y = a.get("diagnostics"), b.get("diagnostics")
                if not isinstance(x, list) or not isinstance(y, list):
                    errors.append({"status": "MISSING_DIAGNOSTICS", "revision": i})
                else:
                    counts[kind] += 1
                    if x != y: errors.append({"status": "DIAGNOSTIC_DIFFERENCE", "revision": i})
            elif kind == "definition_typed_hover":
                x, y = a.get("semantic"), b.get("semantic")
                if not isinstance(x, dict) or not isinstance(y, dict):
                    errors.append({"status": "MISSING_SEMANTIC", "revision": i})
                    continue
                dx, dy = x.get("definitions"), y.get("definitions")
                hx, hy = x.get("hover"), y.get("hover")
                if not informative(dx) or not informative(dy) or not informative(hx) or not informative(hy):
                    errors.append({"status": "NONINFORMATIVE_SEMANTIC", "revision": i})
                    continue
                counts[kind] += 1
                if dx != dy or stable_hover(hx) != stable_hover(hy):
                    errors.append({"status": "SEMANTIC_DIFFERENCE", "revision": i})
            elif kind == "terminal_verification":
                x, y = a.get("verification"), b.get("verification")
                if not isinstance(x, list) or not x or not isinstance(y, list) or not y or any(not isinstance(t, dict) or t.get("outcome") not in TERMINAL for t in x + y):
                    errors.append({"status": "NONTERMINAL_VERIFICATION", "revision": i})
                    continue
                counts[kind] += 1
                if x != y: errors.append({"status": "VERIFICATION_DIFFERENCE", "revision": i, "left": x, "right": y})
            else:
                errors.append({"status": "UNKNOWN_COMPARISON_KIND", "kind": kind})
    for kind, minimum in config.get("minimum_comparisons", {}).items():
        if counts.get(kind, 0) < minimum:
            errors.append({"status": "INSUFFICIENT_INFORMATIVE_COMPARISONS", "kind": kind,
                           "minimum": minimum, "actual": counts.get(kind, 0)})
    for item in config.get("known_incomplete", []):
        skips.append({"status": "SKIPPED_INCOMPLETE", **item})
    # Persist portable provenance only, never machine-specific home paths.
    try:
        portable_bundle = root.relative_to(Path(__file__).resolve().parents[1]).as_posix()
    except ValueError:
        portable_bundle = "external-bundle:" + str(config.get("bundle_id", "unspecified"))
    report = {"schema": "evidence-bundle-completeness-v1", "script": "check_evidence_bundle.py",
              "script_version": SCRIPT_VERSION, "bundle": portable_bundle, "bundle_id": config.get("bundle_id"),
              "status": "PASS" if not errors else "FAIL", "comparison_counts": counts,
              "required_observation_files": len(required), "errors": errors, "skips": skips,
              "caveats": config.get("caveats", [])}
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="JSON manifest describing the expected bundle")
    parser.add_argument("--report", help="write machine-readable report JSON")
    args = parser.parse_args()
    report = validate(args.config)
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        Path(args.report).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
