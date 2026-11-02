#!/usr/bin/env python3
"""Generate reproducible single-document Dafny workloads from checksum-pinned SATLIB files.

For semantic resolution only: NO assertion about solving the original CNF.
Source path is a local clone of Formal-Computing/cdcl-sat-solver at the exact
revision recorded in the generated manifest.
"""
from __future__ import annotations
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "tests/air/corpus"
SOURCES = (
    ("uf20-01.cnf", "Random3SAT-20-SAT"),
    ("uf50-02.cnf", "Random3SAT-50-SAT"),
    ("uuf50-02.cnf", "Random3SAT-50-UNSAT"),
    ("aim-50-1_6-yes1-1.cnf", "AIM-50-SAT"),
    ("aim-50-1_6-no-1.cnf", "AIM-50-UNSAT"),
    ("hole7.cnf", "Pigeonhole-7-UNSAT"),
    ("dubois30.cnf", "Dubois-30-UNSAT"),
)

def parse_dimacs(raw: bytes):
    variables = clauses_expected = None
    clauses: list[list[int]] = []
    pending: list[int] = []
    for line in raw.decode("ascii").splitlines():
        line = line.strip()
        if line == "%":
            break
        if not line or line.startswith("c"):
            continue
        if line.startswith("p "):
            bits = line.split()
            assert len(bits) == 4 and bits[1] == "cnf"
            variables, clauses_expected = map(int, bits[2:])
            continue
        assert variables is not None, "CNF header missing"
        for word in line.split():
            lit = int(word)
            if lit == 0:
                assert pending, "Empty clause is outside this workload's scope"
                clauses.append(pending)
                pending = []
            else:
                assert 0 < abs(lit) <= variables
                pending.append(lit)
    assert not pending
    assert variables is not None and len(clauses) == clauses_expected
    return variables, clauses

def main():
    origin = Path(sys.argv[1]).resolve()
    expected_revision = "88247ab605ee0e3da2aca711885e3340eb78c782"
    from subprocess import check_output
    actual_revision = check_output(["git", "-C", str(origin), "rev-parse", "HEAD"], text=True).strip()
    assert actual_revision == expected_revision, f"SATLIB source commit drift: {actual_revision}"
    manifest = json.loads((origin / "benchmarks/satlib/manifest.json").read_text())
    index = {x["file"]: x for x in manifest["benchmarks"]}
    DEST.mkdir(parents=True, exist_ok=True)
    entries = []
    for filename, label in SOURCES:
        raw = (origin / "benchmarks/satlib/cnf" / filename).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        spec = index[filename]
        assert digest == spec["sha256"], f"checksum mismatch for {filename}"
        variables, clauses = parse_dimacs(raw)
        assert variables == spec["variables"] and len(clauses) == spec["clauses"]
        lines = [
            "// Generated from original SATLIB DIMACS; this program does NOT solve SAT.",
            f"// {filename}; SHA-256 {digest}; reported SATLIB class: {spec['expected']}",
            "module CorpusProvider {",
            f"  const VariableCount: nat := {variables}",
        ]
        for i, clause in enumerate(clauses):
            lines.append(f"  const C{i:03d}: seq<int> := [{', '.join(map(str, clause))}]")
        lines.append("  const Clauses: seq<seq<int>> := [")
        for i in range(0, len(clauses), 12):
            part = ", ".join(f"C{j:03d}" for j in range(i, min(i + 12, len(clauses))))
            lines.append("    " + part + ("," if i+12 < len(clauses) else ""))
        lines += [
            "  ]",
            "  function SourceVersion(): int { 0 }",
            "}",
            "module CorpusInspector {",
            "  import Src = CorpusProvider",
            "  function ClauseCount(): nat { |Src.Clauses| }",
            "}",
            "module CorpusWorkingEdit {",
            "  function RevisionTag(): int { 10 }",
            "}",
            "",
        ]
        result = "\n".join(lines)
        slug = label.lower()
        assert re.fullmatch(r"[a-z0-9-]+", slug)
        dest = DEST / (slug + ".dfy")
        dest.write_text(result, encoding="utf-8")
        entries.append(dict(id=slug, source=filename, kind=label, expected_sat_class=spec["expected"],
                            variables=variables, clauses=len(clauses),
                            sha256_dimacs=digest,
                            dafny_lines=result.count("\n"), sha256_dafny=hashlib.sha256(result.encode()).hexdigest()))
    metadata = dict(schema="dafny-satlib-matrix-v1", origin="Formal-Computing/cdcl-sat-solver",
                    origin_revision=expected_revision, transforms="DIMACS clauses become typed Dafny const declarations; never a SAT computation",
                    cases=entries)
    (DEST / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"count": len(entries), "totalClauses": sum(x["clauses"] for x in entries),
                      "cases": [{k:v for k,v in x.items() if k in ("id","clauses","variables","expected_sat_class")} for x in entries]},indent=2))

if __name__ == "__main__":
    main()
