#!/usr/bin/env python3
"""Validate provenance manifest structure and hashes using only the stdlib."""
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research" / "provenance-manifest.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def validate(path=MANIFEST):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["schema"] == "dafny-incremental-resolver-provenance-v1"
    assert data["upstream"]["commit"] == "de36f2ec1f9c530080eff7929ae28229f45da069"
    assert data["environment"]["z3_version"].startswith("unknown")
    assert data["environment"]["ci_execution_for_this_manifest"] == "not_run"
    assert data["modes"]["experimental"]["DAFNY_RESEARCH_UNSAFE_CROSS_REVISION_REUSE"] == "1"
    entries = data["patch_chain"] + data["fixtures"]
    paths = [entry["path"] for entry in entries]
    assert len(paths) == len(set(paths)), "duplicate path entry"
    for entry in entries:
        digest = entry["sha256"]
        assert SHA256.fullmatch(digest), f"invalid SHA256: {entry['path']}"
        file_path = ROOT / entry["path"]
        assert file_path.is_file(), f"missing file: {entry['path']}"
        actual = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual == digest, f"hash mismatch: {entry['path']}"
    assert data["reproduction_commands"]
    assert data["existing_evidence_limitations"]
    return len(entries)


def self_test():
    import tempfile

    valid = json.loads(MANIFEST.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as temp:
        valid_path = Path(temp) / "valid.json"
        valid_path.write_text(json.dumps(valid), encoding="utf-8")
        assert validate(valid_path) == len(valid["patch_chain"]) + len(valid["fixtures"])
        broken = json.loads(json.dumps(valid))
        broken["fixtures"][0]["sha256"] = "0" * 64
        broken_path = Path(temp) / "broken.json"
        broken_path.write_text(json.dumps(broken), encoding="utf-8")
        try:
            validate(broken_path)
        except AssertionError as error:
            assert "hash mismatch" in str(error)
        else:
            raise AssertionError("validator accepted a tampered fixture hash")
    print("PASS: valid manifest accepted; tampered hash rejected")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        self_test()
    else:
        count = validate(Path(sys.argv[1]) if len(sys.argv) > 1 else MANIFEST)
        print(f"PASS: provenance manifest valid ({count} patch/fixture hashes)")
