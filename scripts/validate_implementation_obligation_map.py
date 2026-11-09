#!/usr/bin/env python3
"""Validate the implementation-facing resolver refinement obligation map."""
import argparse
import copy
import json
import sys
from pathlib import Path

PIN = "de36f2ec1f9c530080eff7929ae28229f45da069"
TOP = {"schema_version", "issue", "pinned_upstream", "claim_boundary",
       "pr39_cross_revision_aliasing", "abstract_state", "implementation_state",
       "candidate_simulation_relation", "obligations", "evidence_ledger"}
OBLIGATION = {"id", "abstract", "implementation", "precondition", "fallback",
              "formal_evidence", "csharp_evidence", "status"}
EVIDENCE = {"discharged_abstract_lemmas", "executed_csharp_tests_this_task",
            "repository_csharp_evidence_not_rerun", "unverified_correspondence", "tooling"}
REQUIRED_IDS = {
    "key-completeness-positive-negative-lookups", "dependency-roster-imports-aliases",
    "determinism-and-complete-key", "mutable-payload-owner-reconstruction",
    "diagnostics-and-token-origin", "rewriters-plugins-options-builtins",
    "cancellation-and-partial-state", "safe-branch-and-nonempty-eligibility",
}


def validate(doc):
    errors = []
    if not isinstance(doc, dict) or not TOP <= doc.keys():
        return ["missing required top-level fields"]
    if doc["schema_version"] != 1:
        errors.append("unsupported schema_version")
    issue = doc["issue"]
    if issue.get("number") != 24 or issue.get("repository") != "Formal-Computing/dafny-incremental-resolver":
        errors.append("issue identity mismatch")
    if issue.get("access") != "unverified":
        errors.append("issue access must remain explicitly unverified")
    pin = doc["pinned_upstream"]
    if pin.get("revision") != PIN:
        errors.append("pinned upstream revision mismatch")
    if "not a universal proof" not in doc["claim_boundary"]:
        errors.append("claim boundary must disclaim universal proof")
    pr = doc["pr39_cross_revision_aliasing"]
    if pr.get("status") != "unverified":
        errors.append("PR #39 cross-revision aliasing must be explicitly unverified")
    relation = doc["candidate_simulation_relation"]
    for phrase in ("complete semantic context", "collision", "Fresh resolution", "current-owner"):
        if phrase.lower() not in json.dumps(relation).lower():
            errors.append(f"simulation relation must state {phrase}")
    obligations = doc["obligations"]
    if not isinstance(obligations, list):
        return errors + ["obligations must be an array"]
    ids = set()
    for i, item in enumerate(obligations):
        where = f"obligations[{i}]"
        if not isinstance(item, dict) or not OBLIGATION <= item.keys():
            errors.append(f"{where}: missing required fields")
            continue
        if item["id"] in ids:
            errors.append(f"{where}: duplicate id {item['id']}")
        ids.add(item["id"])
        for field in OBLIGATION - {"id", "status"}:
            if not isinstance(item[field], str) or not item[field].strip():
                errors.append(f"{where}: {field} must be nonempty")
        if item["status"] not in {"open", "partially_supported"}:
            errors.append(f"{where}: invalid status")
        if not any(s in item["fallback"].lower() for s in ("fresh", "discard", "fail")):
            errors.append(f"{where}: fallback must be fail-closed")
    missing = REQUIRED_IDS - ids
    if missing:
        errors.append("missing required obligations: " + ", ".join(sorted(missing)))
    ledger = doc["evidence_ledger"]
    if not isinstance(ledger, dict) or not EVIDENCE <= ledger.keys():
        errors.append("evidence ledger missing required categories")
    else:
        if ledger["executed_csharp_tests_this_task"]:
            errors.append("this task must not claim C# tests were executed")
        if not ledger["unverified_correspondence"]:
            errors.append("unverified correspondence must be explicit")
        if ledger["tooling"].get("dafny_cli") != "not installed; no Dafny verification run":
            errors.append("Dafny verification availability must be explicit")
    return errors


def corruption_checks(doc):
    cases = []
    broken = copy.deepcopy(doc)
    broken["pinned_upstream"]["revision"] = "wrong"
    cases.append(("wrong pin", broken))
    broken = copy.deepcopy(doc)
    broken["obligations"] = [x for x in broken["obligations"]
                              if x["id"] != "negative" and x["id"] != "key-completeness-positive-negative-lookups"]
    cases.append(("missing negative lookup obligation", broken))
    broken = copy.deepcopy(doc)
    broken["pr39_cross_revision_aliasing"]["status"] = "verified"
    cases.append(("invented PR verification", broken))
    broken = copy.deepcopy(doc)
    broken["obligations"][0]["fallback"] = "reuse cached value"
    cases.append(("non-fail-closed fallback", broken))
    for label, corrupt in cases:
        if not validate(corrupt):
            return [f"corruption test failed to reject {label}"]
    return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("map", nargs="?", type=Path,
                        default=Path(__file__).resolve().parents[1] / "research/implementation-obligation-map.json")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        doc = json.loads(args.map.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid obligation map: {exc}", file=sys.stderr)
        return 2
    errors = validate(doc)
    if not errors and args.self_test:
        errors.extend(corruption_checks(doc))
    if errors:
        print("implementation obligation map INVALID:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"implementation obligation map valid: {len(doc['obligations'])} obligations; pin {PIN}")
    if args.self_test:
        print("corruption checks passed: wrong pin, missing negative lookup, invented PR verification, unsafe fallback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
