#!/usr/bin/env python3
"""Pinned-source to model contract audit for immutable export summaries.

This textual source audit is a regression guard, not a formal C# proof.
Fail closed if the pinned upstream branch or reconstruction shape changes.
"""
import hashlib
import json
from pathlib import Path
import re
import sys

PIN="de36f2ec1f9c530080eff7929ae28229f45da069"
EXPECTED_SHA="ce2eb870fe78c31c445f146ce9c5e61405bfd140630fd3def59d29648f9061b8"

def verify(dafny, results):
    source_path=dafny/"Source/DafnyCore/Resolver/ModuleResolver.cs"
    source=source_path.read_bytes()
    sha=hashlib.sha256(source).hexdigest()
    if sha!=EXPECTED_SHA:
        raise AssertionError("Pinned ModuleResolver.cs changed: "+sha)
    s=source.decode("utf-8")
    pattern=r"} else if \(decl is ModuleExportDecl\) \{(?P<body>.*?)\} else \{"
    matches=list(re.finditer(pattern,s,re.DOTALL))
    assert len(matches)==1, "Missing or ambiguous export resolver branch"
    assert not matches[0].group("body").strip(), "Export resolver branch is no longer empty"
    assert "Dictionary<ModuleDefinition, ModuleSignature> signatures = new();" in s
    assert "public Dictionary<TopLevelDeclWithMembers, Dictionary<string, MemberDecl>> moduleClassMembers = new();" in s
    assert "reporter = new BatchErrorReporter(Options);" in s
    assert "return new ModuleResolutionResult(decl, (BatchErrorReporter)reporter, signatures, moduleClassMembers);" in s

    cache=(dafny/"Source/DafnyLanguageServer/Language/CachingResolver.cs").read_text()
    assert "internal readonly record struct EmptyExportSummary(int SchemaVersion, bool ValidatedEmpty);" in cache
    assert "if (ResearchImmutableExportSummary && decl is ModuleExportDecl)" in cache
    assert "ReferenceEquals(resolved.ResolvedDeclaration, decl)" in cache
    assert "resolved.Signatures.Count == 0" in cache
    assert "resolved.ClassMembers.Count == 0" in cache
    assert "resolved.ErrorReporter.AllMessages.Count == 0" in cache
    method=cache.split("private ModuleResolutionResult ResolveEmptyExportSummary",1)[1].split("// Explicit research-only guard",1)[0]
    assert "base.ResolveModuleDeclaration(compilation, decl)" in method
    assert "return new ModuleResolutionResult(" in method
    assert "new BatchErrorReporter(decl.Options)" in method
    assert "new Dictionary<ModuleDefinition, ModuleSignature>()" in method
    assert "new Dictionary<TopLevelDeclWithMembers, Dictionary<string, MemberDecl>>()" in method
    assert "cache.Modules.TryGet" not in method and "cache.Modules.Set" not in method
    assert "Interlocked.Increment(ref cache.ResearchExportSummaryHits)" in method
    # Research nonempty summaries are value-only and used strictly for audit.
    assert "internal readonly record struct NonemptySymbolAudit(int SchemaVersion, ImmutableArray<string> Names);" in cache
    assert "private static NonemptySymbolAudit CaptureNonemptyNames(ModuleResolutionResult result)" in cache
    assert "ResearchNonemptyAudit|" in cache
    audit=cache.split("private void AuditFreshResult(",1)[1].split("private byte[] GetExperimentalHash(",1)[0]
    assert "var fresh" not in audit or "var symbols = CaptureNonemptyNames(fresh);" in audit
    assert "cache.ResearchNonemptySymbolAudits[candidate] = symbols;" in audit
    assert "return new ModuleResolutionResult(" not in audit
    assert "cache.Modules.Set(" not in audit and "cache.Modules.TryGet(" not in audit

    out={
        "schema":"pinned-export-branch-contract-v1",
        "pinned_dafny":PIN,
        "module_resolver_sha256":sha,
        "branch_empty":True,
        "fresh_result_current_decl_empty_collections_reporter":True,
        "summary_primitive_record_only":True,
        "summary_hit_skips_module_resolver":True,
        "summary_hit_constructs_new_current_program_objects":True,
        "limitations":"Textual anchors and a pinned source revision; not a machine-checked C# implementation refinement or proof about custom rewriters.",
    }
    results.mkdir(parents=True,exist_ok=True)
    (results/"export-contract-audit.json").write_text(json.dumps(out,indent=2)+"\n")
    print("Pinned export branch contract PASS",sha)
    return True

if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: assert_export_contract.py <pinned-dafny> <out-dir>")
    verify(Path(sys.argv[1]),Path(sys.argv[2]))
