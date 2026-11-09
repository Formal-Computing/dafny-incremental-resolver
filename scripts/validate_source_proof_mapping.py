#!/usr/bin/env python3
"""Validate anchors and required refinement caveats in the source/proof map."""
import argparse
import json
import re
import sys
from pathlib import Path

PIN = "de36f2ec1f9c530080eff7929ae28229f45da069"
REQUIRED = {"schema_version", "pinned_upstream", "proof_model", "mappings", "evidence_categories"}


def validate(doc, root):
    errors = []
    if not REQUIRED <= doc.keys():
        errors.append("missing top-level fields: " + ", ".join(sorted(REQUIRED - doc.keys())))
        return errors
    pin = doc["pinned_upstream"]
    if pin.get("revision") != PIN:
        errors.append(f"pinned revision must be {PIN}")
    expected_base = f"https://github.com/dafny-lang/dafny/blob/{PIN}/"
    if pin.get("base_url") != expected_base:
        errors.append("base_url must target the pinned upstream revision")
    if not isinstance(doc["mappings"], list) or not doc["mappings"]:
        errors.append("mappings must be a nonempty array")
        return errors
    ids = set()
    for i, mapping in enumerate(doc["mappings"]):
        where = f"mappings[{i}]"
        if not mapping.get("id") or mapping["id"] in ids:
            errors.append(f"{where}: missing or duplicate id")
        ids.add(mapping.get("id"))
        for group in ("upstream", "proof"):
            anchors = mapping.get(group)
            if not isinstance(anchors, list) or not anchors:
                errors.append(f"{where}.{group}: missing anchors")
                continue
            for j, anchor in enumerate(anchors):
                path = anchor.get("path" if group == "upstream" else "file")
                symbol = anchor.get("symbol")
                if not path or not symbol:
                    errors.append(f"{where}.{group}[{j}]: anchor needs path/file and symbol")
                    continue
                if group == "upstream":
                    if re.search(r":\d|#L\d", path + symbol):
                        errors.append(f"{where}.{group}[{j}]: line-number anchors are forbidden")
                    if not path.endswith(".cs") or not path.startswith("Source/"):
                        errors.append(f"{where}.{group}[{j}]: malformed pinned upstream source path: {path}")
                elif not (root / path).is_file():
                    errors.append(f"{where}.{group}[{j}]: proof file missing: {path}")
        fields = mapping.get("field_mapping")
        if not isinstance(fields, list) or not fields:
            errors.append(f"{where}: field_mapping must be nonempty")
        else:
            for j, field in enumerate(fields):
                for name in ("upstream_field", "abstract_field", "status", "unverified_premise"):
                    if not field.get(name):
                        errors.append(f"{where}.field_mapping[{j}]: missing {name}")
        if not mapping.get("evidence_kind"):
            errors.append(f"{where}: missing evidence_kind")
        if not isinstance(mapping.get("unverified_premises"), list) or not mapping["unverified_premises"]:
            errors.append(f"{where}: unverified_premises must be a nonempty array")
        if "source_behavior_tested" not in mapping:
            errors.append(f"{where}: source_behavior_tested must be explicit")
    return errors


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mapping", nargs="?", type=Path, default=Path(__file__).resolve().parents[1] / "research/source-to-proof-mapping.json")
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = p.parse_args()
    try:
        doc = json.loads(args.mapping.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid mapping: {exc}", file=sys.stderr)
        return 2
    errors = validate(doc, args.root)
    if errors:
        print("source-to-proof mapping INVALID:")
        print("\n".join(f"- {e}" for e in errors))
        return 1
    print(f"source-to-proof mapping valid: {len(doc['mappings'])} mappings; pinned {PIN}")
    missing = sorted({a["path"] for m in doc["mappings"] for a in m["upstream"] if not (args.root / a["path"]).is_file()})
    if missing:
        print(f"upstream source checkout unavailable; {len(missing)} distinct source anchors remain explicitly unverified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
