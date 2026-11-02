# Immutable semantic summary: first genuinely optimizing, restricted Dafny subset

Pinned Dafny: de36f2ec1f9c530080eff7929ae28229f45da069.
New research patch: patches/0005-immutable-export-summary-current-graph.patch.
Opt-in: DAFNY_RESEARCH_IMMUTABLE_EXPORT_SUMMARY=1.

## Exact proof boundary

We do NOT claim sound optimized reuse of arbitrary Dafny modules. The pinned
ModuleResolver.ResolveModuleDeclaration has an empty ModuleExportDecl dispatch
branch. For that specific branch, the result comprises the CURRENT module
declaration, an empty BatchErrorReporter, an empty Signatures dictionary and
an empty ClassMembers dictionary. The declaration's own visibility/signature
was constructed or modified earlier and is never replaced with a cached AST.

Only this empty semantic payload is context-independent. The content-sensitive
candidate hash remains unproved for all other kinds of modules. The optimization
does not require that hash equality imply general semantic context equivalence.

## C# implementation

A value-only EmptyExportSummary(SchemaVersion=1, ValidatedEmpty=true)
record struct is retained in ResolutionCache. Access is protected by a lock.
Hit/miss counters are maintained with Interlocked operations.

On the first eligible ModuleExportDecl, the real upstream resolver executes.
The implementation validates exact current declaration identity, zero
signatures, zero class members and zero diagnostics. Only then does it publish
an immutable summary containing no mutable semantic references.

On subsequent eligible declarations it SKIPS the ModuleResolver construction
and empty export dispatch. It returns a NEW ModuleResolutionResult wrapping
the CURRENT ModuleDecl, a fresh BatchErrorReporter and fresh empty dictionaries.
No AST, signature, scope, reporter or module identity crosses revisions.

When DAFNY_RESEARCH_SAFE_REVALIDATE=1 is also active, all other module kinds
and the builtin system are still resolved afresh. Both flags can be set safely
because the export summary branch has priority only for ModuleExportDecl.

This is genuine work elimination for a restricted no-op dispatch; it is not a
general resolver speedup and no end-to-end latency speedup is claimed.

## Formal model and limitations

tests/formal/ImmutableExportSummaryRefinement.dfy establishes that:

- cache summary hits construct results equivalent to fresh export resolution;
- results belong to the current owner/decl identity, not the cached owner;
- a loop invariant guarantees equivalence across arbitrary revision sequences;
- a witness proves a second export declaration genuinely skips a resolver call;
- ordinary module declarations continue through fresh resolution.

The crucial C#-to-model assumption is pinned to a specific implementation:
the real ModuleExportDecl dispatch branch has no side effects and returns empty
collections. Source inspection and a runtime validation on the first miss
support, but do not formally verify, that C# fact. If upstream changes, this
patch must be reaudited before use.

## Empirical tests

.github/workflows/immutable-export-summary.yml builds the pinned real Dafny
and runs: a hotpath test that requires a true MISS and HIT for separate export
declarations; a four-revision type-change/repair LSP trace comparing exact
diagnostics, definition targets and stable hover markup against independent
fresh semantic resolution; and a four-revision proof trace comparing terminal
Correct/Error outcomes. A fail-closed comparator includes deliberately
corrupted outcome and missing-evidence controls.

## What remains unsolved

There is no verified reconstruction of nonempty AST graphs, general semantic
summaries, option/rewriter/negative-lookup completeness, or SHA-256-to-semantic
key refinement for ordinary modules. Those remain prerequisite to an
optimization applicable to general Dafny projects.

## Completed pinned real-Dafny evidence

GitHub Actions run 41479386215 passed with the opt-in immutable-export cache. The pinned C# server compiled, a real two-export test confirmed a MISS followed by a HIT on the skipped ModuleResolver branch, and the independent fresh-semantic oracle agreed on 4/4 exact diagnostic snapshots, 4/4 selected definition/hover observations and 4/4 terminal verifier outcomes. One revision produced two type diagnostics as intended; all four selected go-to-definition queries returned one definition. The verifier scenario included an intentionally failing assertion and subsequent recovery. The comparator also rejected a deliberately falsified verifier result and a missing trace.

The raw two-mode JSON traces, normalized comparison report, source-contract audit (ModuleResolver.cs SHA-256 ce2eb870fe78c31c445f146ce9c5e61405bfd140630fd3def59d29648f9061b8) and checksummed manifest are saved at experiments/results/2026-11-02-immutable-export-41479386215/. A stricter source-branch audit and nontrivial test assertions are now included in CI; the original green run predates those additional regression checks, although they passed locally on the archived evidence.

This demonstrates skipped work in a narrow pinned implementation branch, not measured end-to-end speedup, semantic completeness of the general experimental key, or soundness for nonempty module-result graphs.
