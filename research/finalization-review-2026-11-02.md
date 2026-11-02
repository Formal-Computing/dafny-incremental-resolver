# Incremental Dafny: 2 November 2026 finalization review

## Scope

This review augments, but does not merge or declare production-safe, the draft research PRs #2, #3, and #4. The 1 November five-page paper predates the best AIR/SATLIB mixed-edit and instrumented profiler results. The revised 2 November reading edition should keep that evidence separate from the small semantic-differential oracle, because **the AIR mixed-edit trace did not independently establish per-edit semantic equivalence**.

## Fresh local execution (paradis WSL)

- Reference-model command: `DOTNET_ROLL_FORWARD=Major dotnet run --project tests/IncrementalResolver.SmokeTests/IncrementalResolver.SmokeTests.csproj -c Release`. Result: **11/11 checks passed**. .NET 10 SDK/runtime used as a roll-forward from net8, not a native .NET 8 runtime.
- Semantic resolution: `/home/admin/.local/opt/dafny/dafny/dafny resolve examples/two-modules.dfy` and `... resolve tests/air/satlib_case_study.dfy`. Both exited **0**.
- New handwritten verification example: `.../dafny verify examples/dependency-walkthrough.dfy`. Result: **2 verified, 0 errors**.
- Deliberately modified temporary copy, changing provider `x+1` to `x+2`, while leaving consumer's assertion intact: **1 verified, 1 error**, assertion may not hold. Expected negative control. This is proof verification, *not a cache-hit or cache-oracle measurement*.
- Local installed CLI identifies itself as Dafny **4.11.0**. The dedicated GitHub LSP integration workflow instead uses pinned Dafny source SHA `de36f2ec1f9c530080eff7929ae28229f45da069`.

## Archived evidence revalidated, not freshly re-executed under CI

Run `python3 scripts/check_archived_evidence.py` to recompute and assert:
- Instrumented profiler runs **41329209347** and **41329569628** each record baseline **4 hits/32 misses** and experiment **28 hits/8 misses** over four measured same-length AIR suffix edits.
- Five mixed-edit decisions (all for AirUF50, AirAIM50, AIR_Inspector) are respectively `MISS HIT MISS`, `MISS HIT MISS`, `HIT HIT HIT`, `HIT HIT HIT`, `MISS MISS MISS`. The experiment reuses an independent provider when another provider changes, and conservatively misses after a prefix position shift.
- The source is **298 clauses / 359 lines** for the profiler workload, derived from two SHA-256 checked SATLIB instances. A prior broader PR may use a **different** three-instance, 662-clause fixture. Do not conflate those workloads.
- The observed reduction is **24 avoided misses (75% fewer misses)**. It is not a 75% latency or CPU improvement.
- Synchronous profiler events report **inclusive wall microseconds** and **current-thread managed allocations**, not CPU seconds, whole-program allocations, exclusive memory or RSS. Increased hash work must be reported alongside reduced resolution-region work.
- The prior semantic differential oracle's **75/75 diagnostic and 42/42 selected semantic-query comparisons** cover seven short traces and 25 revisions across three caching modes. They are not 117 independently tested programs, nor do they prove AIR mixed-trace equivalence.

## Paper edits for the updated reading edition

1. Replace the old unsupported 'performance unmeasured' statement with the strictly bounded profiler data and the changed hashing overhead. Preserve that end-to-end latency rankings were inconsistent.
2. Add five AIR mixed edits as a concrete dependency/position worked example and distinguish this experiment from the shorter differential oracle.
3. Preserve explicit limitations for incomplete negative dependencies, option/plugin state, source origins, mutable result reuse, parser cache persistence, and no general soundness theorem.
4. Clarify direct prior art: Mercaș's thesis and the Dafny interactive-proof-mode research; do not call content hashing or module-level caching novel.
5. Repair broken Romanian author-name glyphs in the 1 November PDF by using Unicode-capable LuaLaTeX fonts.
6. Keep PI/university confirmation, venue compliance and final peer/supervisor review outside the scientific claims; do not mark research PRs ready to merge without correctness review.

## Reproducibility links

- [Repository](https://github.com/Formal-Computing/dafny-incremental-resolver)
- [Semantic oracle run](https://github.com/Formal-Computing/dafny-incremental-resolver/actions/runs/41314947494)
- [First instrumented profiler](https://github.com/Formal-Computing/dafny-incremental-resolver/actions/runs/41329209347)
- [Mixed-edit + second profiler run](https://github.com/Formal-Computing/dafny-incremental-resolver/actions/runs/41329569628)
- [Profiler PR #4](https://github.com/Formal-Computing/dafny-incremental-resolver/pull/4)
