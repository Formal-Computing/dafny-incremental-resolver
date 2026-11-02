# Refinement boundary and fail-closed experimental cache (2 November 2026)

## Scope, scientific claim, and non-claim

The prior abstract theorem in `tests/formal/CacheSoundness.dfy` establishes
memoization correctness for **complete, exact semantic keys** and **pure,
immutable resolution observations**. It does not establish those premises for
the pinned Dafny language server.

This change proves a narrower property in `tests/formal/CacheRefinement.dfy`:
**when speculative cross-revision reuse is not explicitly enabled, the
selected key and key-equality reuse decisions equal those of the upstream
CloneId-based cache**. A module lacking complete single-file token coverage
also receives the recursively computed upstream key. This is a **relative
non-regression result for cache-key decisions**, not an absolute proof that
Dafny's baseline is semantically sound.

The proof operates over an abstract structural model; it does not
machine-verify C# source, SHA-256 collision resistance, byte-serialization
correctness, object-identity semantics, or the Dafny resolver's mutable state.

## Pinned source implementation

Upstream: `dafny-lang/dafny@de36f2ec1f9c530080eff7929ae28229f45da069`.

- `Source/DafnyLanguageServer/Language/CachingResolver.cs`: persistent
  `ResolutionCache.Modules` caches `ModuleResolutionResult`.
- A feature flag alone is **not sufficient** to enable speculative reuse.
  `UnsafeResearchCrossRevisionReuse` is true only when both
  `DAFNY_EXPERIMENTAL_CONTENT_HASH=1` and
  `DAFNY_RESEARCH_UNSAFE_CROSS_REVISION_REUSE=1`.
- Without both flags, `GetHash` always follows `GetUpstreamHash`. That
  function recursively calls **itself**, not `GetHash`, using a separate
  `upstreamHashes` memo. This prevents experimental dependency hashes from
  contaminating the baseline key when a parent falls back.
- The additional local eligibility test requires `SingleFileToken`, start
  and end origins sharing a non-null URI, and nonempty covered tokens all
  sharing the URI. A failure selects `GetUpstreamHash` even in unsafe mode.
  This test is **not** a complete semantic context certificate.
- The experimental insertion policy still excludes results with diagnostic
  messages, a partial mitigation for negative dependencies.
- `DAFNY_RESEARCH_INJECT_STALE_BETA=1` is an intentionally unsound fixture
  available *only* under the two unsafe-reuse research flags. Never deploy it.

## Refinement relation

For module M, define `B(M)` as the upstream fingerprint computed with
upstream-only recursive dependency fingerprints. Let `E(M)` be the
experimental content/position fingerprint and `C(M)` denote the local token
coverage check. Then the selector is:

`K(M) = E(M)` if `experimental && unsafe && C(M)`, else `B(M)`.

For `!(experimental && unsafe)`, K(M)=B(M) for all M.
For `!C(M)`, K(M)=B(M) recursively through dependencies, regardless of
whether those dependencies are individually eligible for E.

It follows under exact fingerprint equality that, in guarded mode,
`K(old)==K(new) iff B(old)==B(new)`. This makes *no new* cross-revision
reuse decisions relative to baseline. The model proves analogous behavior
for a parent with an experimentally eligible provider but an unsupported
parent, conditional on the actual C# implementation implementing this
recursion exactly.

A second mechanically verified counterexample constructs two states with
the same E but different failed-name lookup context. Thus `C(M)` alone
cannot be elevated to a certificate of safe semantic reuse.

## Verification matrix

| Case | Required key | Effect |
|---|---|---|
| No flags | Upstream B | No additional research reuse |
| Only DAFNY_EXPERIMENTAL_CONTENT_HASH=1 | Upstream B | Fail closed |
| Both flags, incomplete token coverage | Upstream B | Fail closed for module and its upstream recursion |
| Both flags, complete local tokens | Experimental E | **Unproved; intentionally unsafe research mode** |
| Introduce or remove negative lookup context | Must invalidate | Counterexample shows E may be incomplete |
| Change project options or plugins | Must invalidate or rebuild cache | Unproved for E |
| Mutable cached AST/signatures/reporter | Must be safe under reattachment | Unproved for both abstract-to-real correspondence |

## Verification and reproducibility

Local abstract proofs on `paradis`, Dafny 4.11.0:
`dafny verify tests/formal/CacheSoundness.dfy` => 8 verified, 0 errors;
`dafny verify tests/formal/CacheRefinement.dfy` => 8 verified, 0 errors.

Pinned C# patch chain:
`git apply --check patches/0001-experimental-module-token-hashing.patch`;
then apply 0001; check/apply 0002; `git diff --check`.
In the disposable upstream worktree this chain applied cleanly.

The GitHub Actions integration workflow tests guarded baseline behavior with
the experiment flag requested but unsafe permission absent, and executes the
older experimental oracle with both flags. Source compilation and passing
tests depend on those workflows completing; a green formal proof alone is
not evidence of C# source-level soundness.

## Remaining route to an actual implementation-soundness theorem

1. Formalize the complete semantic context `E`: failed name lookups,
   module exports/import views, project/compiler options, plugin/rewriter
   state, dependency graph changes, source origins, and tool versions.
2. Prove/refine that C# key equality implies complete-context equivalence,
   including SHA-256 collision assumptions and deterministic serialization.
3. Establish immutable cache summaries or safe deep cloning. Current cached
   `ModuleResolutionResult` and resolved AST graphs are mutable.
4. Prove observationally safe result reattachment, replay of diagnostics and
   post-rewriter behavior across compiler revisions.
5. Extend fresh-resolution oracle to independent parser and semantic-cache
   switches, full symbol/type/verification comparisons, randomized
   differential edits and multiple real AIR/SATLIB projects.
6. Retain unsafe opt-in until independent source-level review and the above
   obligations are discharged; do not present this as production-ready.
