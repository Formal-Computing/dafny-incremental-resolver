# Dafny integration experiment — 29 October 2026

## Reproducibility

- Research repository: `Formal-Computing/dafny-incremental-resolver`
- Upstream Dafny pinned commit: `de36f2ec1f9c530080eff7929ae28229f45da069`
- Research commit tested: `2a9d765`
- Runner: GitHub Actions `ubuntu-24.04`, .NET 8, Z3 installed with apt
- [Successful CI run](https://github.com/Formal-Computing/dafny-incremental-resolver/actions/runs/40892523245)

## Verified outcomes

| Test | Result |
| --- | --- |
| Apply token-hash patch to upstream Dafny | PASS |
| Compile Dafny language-server test project | PASS |
| Baseline `CloneId` same-file experiment | PASS (1/1) |
| Experimental source-token hash same-file experiment | PASS (1/1) |
| Upstream `CachingTest` suite, experimental mode | 8 PASS, 1 SKIP |
| Independent C# reference-model smoke tests | 11 PASS (previous CI and Paradis) |

The regression changes `Beta.Value()` from `21` to `22` without changing the
length of the file or any token position within `Alpha`. It asserts:

- `Beta` has a resolution-cache miss in both modes.
- The unmodified `Alpha` has a cache miss with baseline `CloneId` hashing.
- The unmodified `Alpha` has a cache hit with experimental token hashing.

The upstream suite includes an older test named `ResolutionInSingleFileIsCached`
still explicitly skipped by Dafny; our separate test is not skipped.

## Interpretation

The test demonstrates that module-local, position-sensitive token hashing
can reuse a previously resolved independent module after a same-file edit,
using Dafny's own parser, resolver and persistent LSP cache.

**Not established:** a general cache-soundness proof; unchanged diagnostic
locations under all edits; member/declaration-level resolution reuse;
memory benefits; or a measured end-to-end latency speedup. No timings
from these runs should be represented as benchmark results: the testhost
startup time and unrelated test overhead dominate the reported durations.

The next milestones are source-shift tests, dependency and negative
name-lookup invalidation, differential diagnostics, controlled latency
benchmarks, and possible declaration-level resolver refactoring.
