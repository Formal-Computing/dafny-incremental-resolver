# Controlled revalidation: a safe implementation refinement boundary

**Research branch:** research/controlled-reattachment-proof-2026-11-02
**Pinned implementation:** dafny-lang/dafny@de36f2ec1f9c530080eff7929ae28229f45da069

## Problem and deliberately restricted result

An experimental key based on source text, dependency hashes, module roster and
builtins is not proven a complete description of semantic resolution context.
Moreover, an upstream `ModuleResolutionResult` retains mutable resolved AST
graphs, module signature dictionaries, class-member dictionaries and reporter
state. Neither a shallow `record with { }` copy nor a hash match proves
cross-compilation reattachment is safe.

The implemented *safe-audit* path addresses both hazards conservatively:
a speculative key is computed and used only to index a **bounded primitive
observation digest**; **both the system module and each module declaration are
resolved afresh**, using the current compilation. The cached mutable module
result is never read or returned and neither resolved AST nor signature graph
is inserted in the audit store. The audit-only snapshot records a digest of
module name, exported top-level/member/constructor name sets, member-group
names and diagnostic strings. The snapshot is purposefully incomplete:
matching digests **never authorize semantic reuse**.

This is controlled *non-reattachment*, not a deep-clone implementation.
It is the strongest currently implementable refinement without inventing
an unverified deep clone for Dafny's graph-rich AST.

### Mode activation

`DAFNY_RESEARCH_SAFE_REVALIDATE=1` enables the safe path in
`CachingResolver`. The existing `DAFNY_EXPERIMENTAL_CONTENT_HASH=1`
may additionally request the content-sensitive candidate key.
If the unsafe experimental flag is simultaneously enabled, the safe path
takes precedence. A deliberately faulty Beta key is excluded when safe mode
is enabled.

The existing normal mode and unsafe research path are otherwise unchanged.
No changes are merged into Dafny upstream; this is an isolated patch #4
applied after patches #1–#3.

### Immutable-by-ownership audit metadata

Each observation is a new `ImmutableArray<byte>` digest stored in
`ResolutionCache.ResearchAuditFingerprints`, keyed by hexadecimal candidate
hash. The dictionary is exclusively accessed under a lock, only stores
immutable primitive digest values, and clears when it reaches 2048 entries. Cached
mutable `ModuleResolutionResult` graphs are neither stored in this audit
dictionary nor reattached by this mode. A matching key with different digest
produces a warning, but always returns fresh resolved data.

The current implementation is **not a general speedup**: every module
resolution and builtins resolution is recomputed. Hashing and observation
auditing add overhead.

## Formal relation and what it proves

`tests/formal/ControlledRevalidationRefinement.dfy` models:
- complete semantic contexts including source, imports, project options,
  rewriters, failed lookups and builtins;
- an *opaque fresh resolver* that is deterministic in that complete context;
- arbitrary stale cache-key candidates and arbitrarily modified heap data;
- bounded, value-only audit records, and a safe mode that always returns
  `FreshResolve(context)`.

The proof establishes, by an inductive loop invariant, observational
equivalence over **arbitrary revision sequences** in the model, independent
of speculative key collisions and heap mutations. It also constructs two
contexts with identical incomplete candidate keys but different fresh
resolution observations; the safe path correctly returns the current
fresh result in both cases. This is a refinement theorem for the **audit
path**, not a theorem allowing faster reuse.

The source-level correspondence obligation is explicit: the actual C#
branch must invoke `base.ResolveModuleDeclaration` and
`base.ResolveSystemModule` without reading a cached mutable result. CI tests
the guard and compares both final verifier statuses and stable LSP
observables against the independent semantic-cache-disabled oracle.

## Remaining conditions for *optimizing* reattachment

Let `C` be complete semantic context, `R(C)` fresh resolved result,
`K(C)` the experimental cache key and `A` a reattachment operation.
To return a cached result with soundness, at least two obligations remain:

1. **Key completeness/refinement:** `K(C1)=K(C2) => R(C1) ≈ R(C2)`,
   accounting for lookup visibility, rewriter state, all compiler options,
   project/import changes and environmental inputs; equality also needs a
   collision-resistance assumption if SHA-256 is involved.
2. **Graph-safe reattachment:** `Obs(A(cachedGraph, currentProgram)) =
   Obs(R(currentProgram))` over all relevant symbols, types, diagnostics
   and verification outcomes, preserving alias boundaries and program
   ownership. Avoid cross-compilation mutable identity reuse.

Neither requirement is proven by the audit-only implementation. The next
optimizing design should cache immutable, self-contained semantic summaries
with explicit ownership and a fresh graph-reconstruction operation, then
prove a refinement relation for that reconstruction. A generic AST deep clone
without an identity/rewriter/visibility proof is not sufficient.

## Reproducibility

- Formal proof:
  `dafny verify tests/formal/ControlledRevalidationRefinement.dfy`
- Runtime tests: `.github/workflows/controlled-revalidation.yml` on
  pinned Dafny, comparing 12 revision-level verifier outcomes and 75
  revision-level diagnostic snapshots, plus selected hover/definition
  observations. The runner tests `ResearchControlledRevalidationModeIsActive`
  to prevent accidental execution in the wrong configuration.
- Exact traces and the strict differential report are archived as a GitHub
  Actions artifact. In case of missing or different observations, the
  comparison fails and no soundness claim may be made.

The suitable publication claim is **a proven abstract refinement for a
conservative fresh-resolution audit mode** and the corresponding tested
pinned C# implementation, not production readiness or an optimized
sound incremental cache.

## Complete-key refinement theorem (specification only)

The expanded Dafny model includes an injective structural key over source,
imports, options, rewriters, negative lookups and builtins. It proves that
**equality of these fully specified context keys implies equality of complete
contexts and thus deterministic fresh-resolution observations**. This is
conditional on *all* real resolver inputs being mapped into the model. The
current content-aware C# key omits some candidate inputs and uses SHA-256, so
this theorem cannot yet certify the optimizing cache. It is a precise future
implementation-refinement obligation, distinct from the unconditional
safe-audit proof, which does not reuse any mutable graph.

## Completed pinned Dafny integration (initial immutable-snapshot revision)

GitHub Actions run 41471521253 passed after compiling the patched Dafny C# language server, verifying the safe-audit feature flag and immutable snapshot type, and executing the independent fresh-semantic oracle. The archived traces show 12/12 terminal verifier outcome pairs, 75/75 exact diagnostic snapshot pairs, and 64/64 selected stable definition/hover pairs matching the independent oracle, with 0 differences. All 151 informative two-mode comparisons are archived with SHA-256 manifests at experiments/results/2026-11-02-controlled-revalidation-41471521253/. The source code for this pinned run was commit 8c6117d; later commits strengthen the model/comparator/documentation without changing the conservative graph-reuse policy. The initial CI is evidence of runtime equivalence on sampled edit sequences, not a proof of global correctness or performance benefits.
