# Resolver soundness: verifier outcomes, mutable aliasing, and semantic key coverage

Research date: 2026-11-02. Tested upstream pin:
`dafny-lang/dafny@de36f2ec1f9c530080eff7929ae28229f45da069`.

## 1. Completed-verifier equivalence (empirical)

CI [run 41454697762](https://github.com/Formal-Computing/dafny-incremental-resolver/actions/runs/41454697762)
**passed** with **48/48 informative** comparisons of *completed* per-declaration outcomes
and name ranges: 3 scenarios × 4 revisions × 4 non-oracle modes (plus the fresh-semantic oracle).

The scenarios cover assertion pass/fail/recovery, changes to a dependency
used by a proof, and unrelated edits alongside both a correct and an
incorrect method. Unlike the older hover oracle, the test explicitly waits
for `NamedVerifiableStatus` to be terminal (`Correct` or `Error`) at the
current document version. It asserts the expected failing revisions. A
comparator self-test confirms that a false success on an expected error is
rejected; missing modes, revisions and non-terminal statuses fail closed.

Five execution modes: original upstream; no parser/resolver caching; only
semantic caching disabled (parser cache stays enabled); guarded patched
baseline; explicitly unsafe experimental content hash. Raw snapshots,
comparator report and SHA-256 manifest are archived in
`experiments/results/2026-11-02-verifier-41454697762/`.

**Scope:** terminal LSP outcomes on selected declarations in twelve controlled
source revisions. Not a byte-for-byte equivalence of Boogie VC,
SMT-LIB queries, prover traces, counterexample models or resource usage.
Not evidence for every Dafny project.

## 2. Mutable ModuleResolutionResult

The pinned C# definition in `ModuleResolver.cs` is a `record` containing:
- `ResolvedDeclaration: ModuleDecl`
- `ErrorReporter: BatchErrorReporter`
- `Signatures: Dictionary<ModuleDefinition, ModuleSignature>`
- `ClassMembers: Dictionary<TopLevelDeclWithMembers, Dictionary<string, MemberDecl>>`

`CachingResolver.ResolveModuleDeclaration` stores this result and returns
the same reference after a hit (no deep clone), while
`ProgramResolver.ProcessDeclarationResolutionResult` reinstalls the resolved
declaration, signatures and class members from the same object graph.

The research test `ResearchMutableResolutionResultAliasing` on the actual
pinned record class demonstrates that even a C# record `with { }` copy is
shallow: the dictionary objects remain shared and their mutation is
observable across aliases. Its purpose is to establish the *aliasing
mechanism*, not to assert that a real semantic error has happened.

The Dafny countermodel `tests/formal/MutableReuseAndKeyCompleteness.dfy`
proves that changing the heap value at the cached address can change the
observation without changing the cache key. An immutable value snapshot does
not exhibit that particular alias behavior.

**Still unproved:** that the actual resolved AST, signatures, scopes and
reporter are unchanged by downstream rewrites, verifier translation, source
revisions, or cross-compilation attachment. A real proof requires either a
verified deep clone/rebase operation or cached immutable semantic summaries
plus a refinement relation. Merely shallow-cloning the C# record does
not discharge this obligation.

## 3. Completeness of the content-aware key

Source-inspection audit:
`scripts/audit_semantic_context.py`; output:
`research/source-context-audit.json`, with SHA-256 for pinned source and
patches. It checks that the experimental hash incorporates token text/
trivia/origins/positions, transitive dependency hashes, a module roster and
builtins. It does **not** find explicit encodings of all compiler/project
options, rewriter and plugin state, or negative name-lookup context.
Because `ProgramResolver.Resolve` invokes pre/post rewriters, these are
material candidate dependencies requiring investigation.

The formal model gives three distinct constructive cases where the abstract
experimental key remains identical while a richer semantic observation
differs (options, rewriters, failed lookups). These prove the *candidate
fingerprint cannot be declared complete from the modeled fields*;
they are not actual Dafny miscompilation counterexamples.

**Conclusion:** soundness of cross-revision content reuse remains
**unproved**. Current two-flag unsafe research opt-in is intentional; a
default-on or production merge would be premature. The guarded baseline
continues to use upstream key semantics.

## Next proof and engineering obligations

1. Trace all implicit resolver input dependencies and demonstrate actual
   influence with controlled Dafny option, project, import, pre/post-rewriter
   edits; record the semantic difference or prove invariance.
2. Define a sound reattachment transformation and immutable semantic
   summary schema for `ModuleResolutionResult`; independently check
   identity and name binding on retained modules.
3. Extend verification oracle to full resolved binding maps and Boogie VC/
   verification outcomes, including multi-file projects, cancellation and
   option changes.
4. Run randomized, paired performance trials only after semantic safety
   gates; compare hash costs against end-to-end speed improvements.

Publication-safe formulation: **empirical equality of selected terminal
verifier outcomes, a formal aliasing countermodel, and a pinned-source
audit identifying unresolved key-completeness obligations.** Not a complete
proof of actual incremental resolver semantic soundness.

The initial CI report counted 60/60 comparisons, including 12 oracle-to-itself comparisons. The corrected comparator omits those 12 trivial comparisons and reports 48/48 informative matches.
