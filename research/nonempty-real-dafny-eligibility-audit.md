# Real-Dafny eligibility audit: why nonempty modules must fail closed

Target: dafny-lang/dafny at de36f2ec1f9c530080eff7929ae28229f45da069.
Parent: PR #12, abstract nonempty immutable-summary model.

## Pinned resolver dispatch audit

ModuleResolver.ResolveModuleDeclaration dispatches the following:

| Branch | Nontrivial semantic effects | Eligible for PR #11 export summary? |
|---|---|---|
| ModuleExportDecl | Empty dispatch body; surrounding result is a fresh wrapper | Yes, pinned-source guarded only |
| LiteralModuleDecl | Calls literalModuleDecl.Resolve and publishes a ModuleSignature | No |
| AliasModuleDecl | Calls ResolveExport, resolves target/export visibility, may update Signature | No |
| AbstractModuleDecl | Calls ResolveExport/MakeAbstractSignature and updates Signature | No |

The literal and alias branches reference mutable module declarations and environment-sensitive
signatures. PR #12's value-only model is not a serialization contract for those graph structures.
Matching a content hash does not establish equivalence of scopes, imports, options, negative lookups,
rewriter state or current-compilation ownership.

## Added executable negative control

ResearchNonemptyModulesNeverUseExportSummary exercises a program with:
- two real nonempty literal modules;
- a datatype with a constructor and field;
- a function, a class with mutable field, and an opened import;
- a client method using imported declarations.

The test enables both DAFNY_RESEARCH_IMMUTABLE_EXPORT_SUMMARY=1 and
DAFNY_RESEARCH_SAFE_REVALIDATE=1, waits for LSP resolution and checks no
ResearchExportSummary HIT or MISS is attributed to these modules. The source
and enabled guarded path establish that the no-op optimization is not applied
to this nonempty case. This is **not** proof that all modules are always fresh:
other caching paths are governed by separate flags and tests.

The pinned export MISS/HIT test, independent fresh-semantic differential oracle,
and terminal verification outcome comparison remain in the same CI workflow.
No new nonempty skip is implemented.

## Next nonempty optimization obligations

1. Choose a restricted nonempty production branch and define its complete side-effect trace.
2. Characterize its AST/ModuleSignature ownership, scope, binding and source-location graph.
3. Serialize a sufficient immutable summary with a complete structural context key.
4. On a hit, reconstruct *all* mutable nodes/references within the current compilation.
5. Prove a refinement mapping from actual C# state transitions to the formal summary model.
6. Run paired fresh-vs-cache diagnostic, binding and final-verifier comparisons across
   edits to imports, options, shadowing, negative lookups, plugins and cancellation.

Until these hold, returning an old ModuleResolutionResult is forbidden. The
research flag remains restricted to the source-audited no-op export dispatch.
