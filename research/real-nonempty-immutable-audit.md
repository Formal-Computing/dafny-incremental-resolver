# Real Dafny immutable nonempty audit integration (research only)

Parent research: PR #13. Pinned Dafny: de36f2ec1f9c530080eff7929ae28229f45da069.

## Implementation boundary

Patch 0006 adds a value-only NonemptySymbolAudit to the real
DafnyLanguageServer/Language/CachingResolver.cs, in the safe-revalidation path.

- After **fresh** resolution it captures the module signature's top-level,
  static-member and constructor names as immutable strings.
- It indexes bounded snapshots under the existing speculative candidate key,
  and logs MISS, MATCH or DIFFERENT when a key is observed again.
- A different observation for the same candidate key is evidence of a
  potentially unsound key. A match is NOT sufficient to certify it.
- Source AST, ModuleSignature, scopes, owner objects, reporters, tokens,
  ModuleResolutionResult and other mutable graphs are never stored here.
- Every ordinary nonempty module is still freshly resolved; audit outcomes
  never authorize cache hits or skipping work. The export-only optimization
  remains separately restricted to ModuleExportDecl.

The extra names represent an incomplete semantic observation, not the complete
context or all verifier-observable state. In particular the key is not proven
complete for options, plugins, rewriters, negative lookups or aliasing.

## Checks

The pinned integration workflow applies patch 0006, compiles the actual
language server, and executes the nonempty regression with both the immutable
export flag and safe revalidation enabled. The regression requires a real
ResearchNonemptyAudit MISS emitted for a nonempty module and asserts that no
export-summary HIT or MISS is attributed to that module. Source-audit checks
ensure the new audit cannot call cache.Modules.Set/TryGet or return a reused
ModuleResolutionResult.

The same workflow retains the strict fresh-vs-export semantic and terminal
verifier comparisons. The abstract model in PR #12 remains separate.

## Scope of claims

Integration into real C#: yes. A nonempty cached observation from actual
resolution: yes. A resolver-skipping nonempty HIT: **no**. General semantic
soundness, universal cache-key completeness, general speedup, and production
readiness: **not established**.

Do not promote this research audit to a caching optimization until a
sufficient, explicit context key and reattachment of nonempty object graphs
are formally validated against the pinned C# implementation.
