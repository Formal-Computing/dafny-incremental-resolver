#!/usr/bin/env python3
"""Validate the research claim-to-run evidence registry (Python stdlib only)."""

import argparse
import copy
import json
import re
import sys
from pathlib import Path


REGISTRY = Path(__file__).resolve().parents[1] / "research" / "claim-evidence-registry.json"
TIERS = {"direct_run", "model", "interpretation"}
STATUSES = {"verified", "partial", "unverified"}
HEX40 = re.compile(r"^[0-9a-f]{40}$")


class RegistryError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise RegistryError(message)


def validate(data):
    require(isinstance(data, dict), "registry root must be an object")
    require(data.get("schema") == "dafny-claim-evidence-registry-v1", "unsupported schema")
    claims = data.get("claims")
    require(isinstance(claims, list) and claims, "claims must be a nonempty array")
    ids = set()
    required_text = ("id", "claim", "input_mode", "oracle", "denominator", "scope")
    for index, claim in enumerate(claims):
        label = f"claims[{index}]"
        require(isinstance(claim, dict), f"{label} must be an object")
        for key in required_text:
            require(isinstance(claim.get(key), str) and claim[key].strip(), f"{label}.{key} must be nonempty text")
        require(claim["id"] not in ids, f"duplicate claim id: {claim['id']}")
        ids.add(claim["id"])
        require(claim.get("tier") in TIERS, f"{label}.tier is invalid")
        require(claim.get("evidence_status") in STATUSES, f"{label}.evidence_status is invalid")
        require(isinstance(claim.get("limitations"), list), f"{label}.limitations must be an array")
        require(isinstance(claim.get("missing"), list), f"{label}.missing must be an array")
        runs = claim.get("runs")
        require(isinstance(runs, list) and runs, f"{label}.runs must be a nonempty array")
        provenance_gaps = []
        for run_index, run in enumerate(runs):
            run_label = f"{label}.runs[{run_index}]"
            require(isinstance(run, dict), f"{run_label} must be an object")
            url = run.get("url")
            require(url is None or (isinstance(url, str) and url.startswith("https://")), f"{run_label}.url must be HTTPS or null")
            commit = run.get("commit")
            require(commit is None or (isinstance(commit, str) and HEX40.fullmatch(commit)), f"{run_label}.commit must be a full 40-character SHA or null")
            require(isinstance(run.get("commit_as_recorded"), str) and run["commit_as_recorded"].strip(), f"{run_label}.commit_as_recorded must explain provenance")
            artifacts = run.get("artifacts")
            require(isinstance(artifacts, list) and artifacts and all(isinstance(a, str) and a.strip() for a in artifacts), f"{run_label}.artifacts must be nonempty paths")
            if url is None or commit is None:
                provenance_gaps.append(run_label)
        require(claim["evidence_status"] != "verified" or (not provenance_gaps and not claim["missing"]), f"{label} cannot be verified with missing provenance")
        require(claim["evidence_status"] != "partial" or bool(claim["missing"]), f"{label} partial evidence must list missing evidence")
        require(claim["evidence_status"] != "unverified" or bool(claim["missing"]), f"{label} unverified evidence must list missing evidence")
    return len(claims)


def corruption_negative_test(data):
    corrupted = copy.deepcopy(data)
    del corrupted["claims"][0]["denominator"]
    try:
        validate(corrupted)
    except RegistryError:
        return
    raise AssertionError("corruption negative test failed to reject missing denominator")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", nargs="?", type=Path, default=REGISTRY)
    parser.add_argument("--self-test", action="store_true", help="also verify that a corrupted registry is rejected")
    args = parser.parse_args()
    try:
        data = json.loads(args.registry.read_text(encoding="utf-8"))
        count = validate(data)
        print(f"PASS: {args.registry} ({count} claims; schema and evidence fields valid)")
        if args.self_test:
            corruption_negative_test(data)
            print("PASS: corruption negative test rejected a missing denominator")
    except (OSError, json.JSONDecodeError, RegistryError, AssertionError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
