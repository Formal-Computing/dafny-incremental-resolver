# Evaluation protocol (October 2026)

## Experimental system
- Pinned upstream: dafny-lang/dafny @ `de36f2ec1f9c530080eff7929ae28229f45da069`.
- Baseline: original `CloneId` key, `DAFNY_EXPERIMENTAL_CONTENT_HASH=0`.
- Experimental: position-sensitive token-content key, `DAFNY_EXPERIMENTAL_CONTENT_HASH=1`.
- Shared implementation: Dafny's existing `CachingResolver`, `ResolutionCache`, parser and language-server test harness.
- Isolation: restart testhost for each mode; the flag is read at process initialization.
- Configuration: same source, SDK, options and edit sequence in both modes.

## Level of evidence
1. **Reference model**: deterministic simulated changes and dependency-graph invalidation.
2. **Build**: patched real Dafny language server compiles.
3. **LSP tests**: real parser/resolver and persistent cache reuse results.
4. **Differential tests**: compare resolved diagnostics and cache hits across identical edit sequences.
5. **Benchmarks**: after semantic equivalence, report measured latencies, memory, and warmups.

A successful reference-model run does **not** establish that the full Dafny resolver is incremental.

## Edit scenarios
| Case | Edit | Required behavior |
| --- | --- | --- |
| Independent same-file | Same-length edit in module Beta; module Alpha unchanged | Experimental Alpha cache hit, Beta miss; same diagnostics |
| Shifted source location | Insert line before Alpha | Alpha not reused unless diagnostics/source origins are safely relocated |
| Dependency | Change an exported function type in Alpha, imported by Beta | Both invalidated; no stale Beta resolution |
| Rename and error | Remove or rename declaration that is referenced | Correct fresh diagnostic |
| Import/export/refinement | Change visibility and referenced modules | Conservative invalidation |
| Options | Change language or resolver options between revisions | No stale entries; ideally option-aware keys |
| Error recovery | Repair an invalid program | Diagnostics regenerated correctly |
| Synthetic/prefix modules | Include and nested/prefix declarations | Conservative fallback where token coverage is ambiguous |

## Measurements to record
- Dafny commit and prototype commit, OS and SDK, source fixture, edit diff.
- Cache hits/misses *per module*, not just global totals.
- Parser and resolver latency separately; cold and warm runs.
- At least 10 measured repetitions once a repeatable benchmark runner exists.
- Diagnostic differences (severity, message, location) as a correctness gate.
- Peak memory or allocation measurements where available.

## Current limits
The patch remains module-granular. It does not cache member-level name resolution, type inference, or declaration-level semantic results. A cache hit cannot by itself prove soundness; source-position changes, global name lookup, plugins, mutable resolved ASTs, and resolution options all require review.

## Reproducing CI
The `Dafny resolver integration` GitHub Actions workflow checks out the pinned Dafny commit, applies our source patch, injects one regression test into upstream `CachingTest`, builds the actual language-server test project, runs baseline and experimental variants, and runs the upstream cache regression suite with the experiment enabled.
