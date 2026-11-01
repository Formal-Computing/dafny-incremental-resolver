# Research extension: a dependency-aware AIR/SATLIB Dafny edit trace

## Why this benchmark exists

The previous report established 24 fewer cache misses on four equal-length edits
in an unrelated trailing module. It did **not** show how the system responds
to changes to dependency providers, realistic length-changing edits or the cost
of computing the cache keys. This extension targets those blind spots.

This is a controlled source-edit workload generated from *original* AIR SATLIB
benchmarks. The source data are pinned and checksum-verified. It is not a
benchmark of SAT solving, a realistic Dafny verification project, or evidence
of correctness for arbitrary Dafny programs.

## Substantial source graph

```text
  AirUF50                 AirAIM50
  218 clauses             80 clauses
        \                  /
         \                /
          v              v
             AIR_Inspector       AIR_WorkingEdit
             imports both       independent tag
```

Each clause is represented as a typed Dafny sequence constant. A single file
contains 359 source lines and 298 original clauses. Modules `AirUF50`,
`AirAIM50` and `AIR_Inspector` are observed individually.

## Predeclared edits and expected cache decisions

| Edit | AirUF50 | AirAIM50 | AIR_Inspector | Reason |
| --- | --- | --- | --- | --- |
| `C000: [-3, 36, 7]` → `[-3, 37, 7]` | MISS | HIT | MISS | Provider changed; dependent inspector must be invalidated |
| Restore `37` → `36` | MISS | HIT | MISS | Provider content changes back; it must be resolved against new revision |
| Independent `RevisionTag() { 10 }` → `{ 100 }` | HIT | HIT | HIT | Edit extends source *after* all tracked modules; their origins do not shift |
| Restore `100` → `10` | HIT | HIT | HIT | Same stability rationale |
| Insert a comment before every module | MISS | MISS | MISS | Source positions move; existing position-sensitive fingerprints become unsafe |

These are **expected outcomes, not claims of observed results** until raw
mode-by-mode traces and a green CI run verify the prediction. In particular,
the experimental cache can be more conservative.

## Separate metrics and honesty about resource savings

The new opt-in `0002-opt-in-resolver-regions.patch` profiles hash computation
and synchronous resolver-body work separately using `Stopwatch`, plus the
managed allocations on the current thread using
`GC.GetAllocatedBytesForCurrentThread`.

- `hashMicroseconds` includes recursive dependency-hash work.
- `resolutionBodyMicroseconds` is an inclusive synchronous wall-clock region,
  not CPU time; nested operations may be double counted.
- `resolutionBodyThreadAllocatedBytes` measures allocations on the current
  resolver thread, not retained memory, peak RSS or all threads.
- LSP wall-clock edit completion remains end-to-end and cannot be substituted
  for resolver time.

Two separately launched xUnit tests control the workloads. Raw per-revision
JSON is preserved for every mode, and CI summaries are generated from that
data. Mode D disables resolution caching but still uses Dafny's parser cache.

## What would be needed for a publication

A stronger experimental design would include multiple independent CI runners,
counterbalanced mode order, a true no-parser-cache oracle, isolated CPU time,
no global state between traces, a hand-written Dafny corpus with verification
outputs, and confidence intervals. The current work establishes behaviors
within a deliberately controlled local source graph.

- Prior benchmark and archival evidence: PR #3
- Profiling + mixed edit research branch: PR #4


## Measured mixed-edit result (CI run 41329569628, 1 November 2026)

**All five predeclared decisions matched the expected directions for the three named modules.**
The actual cache events for the experimental resolver are:

| Edit | AirUF50 | AirAIM50 | AIR_Inspector | Experimental cache hits/misses, all modules | Upstream hits/misses |
|---|---|---|---|---:|---:|
| Provider clause 36 to 37 | MISS | HIT | MISS | 5 / 4 | 1 / 8 |
| Provider clause 37 to 36 | MISS | HIT | MISS | 5 / 4 | 1 / 8 |
| Suffix function 10 to 100 (length increases) | HIT | HIT | HIT | 7 / 2 | 1 / 8 |
| Suffix function 100 to 10 (length decreases) | HIT | HIT | HIT | 7 / 2 | 1 / 8 |
| Prefix comment inserted before all modules | MISS | MISS | MISS | 1 / 8 | 1 / 8 |

This is a stronger case than the earlier same-length edit only: a source-length
change **after** unchanged modules preserves their source positions and permits
reuse; a source-length change **before** them does not. A modification to
AirUF50 invalidates itself and the dependent inspector, but not independent
AirAIM50. Both original and patched baseline miss all three named modules on
each of these edits.

The five controlled scenarios are **not** a sample of natural editing behavior.
The test collects timing and caching logs, not independent per-revision semantic
equivalence for this particular AIR scenario.

[Full CI execution](https://github.com/Formal-Computing/dafny-incremental-resolver/actions/runs/41329569628).
Raw original/fresh/baseline/experimental JSON and per-edit report are archived at
experiments/results/2026-11-01-mixed-profile-41329569628.

## Resolver-specific profile replication

Two green instrumented runs used exactly the same opt-in profiler patch on
the patched baseline and the experimental implementation.

| Four measured equal-length edits | Baseline run 41329209347 | Experimental run 41329209347 | Baseline run 41329569628 | Experimental run 41329569628 |
|---|---:|---:|---:|---:|
| Cache misses | 32 | 8 | 32 | 8 |
| Inclusive body wall-time (ms) | 365.289 | 17.196 | 223.181 | 20.754 |
| Inclusive body managed allocations (MiB) | 71.53 | 2.20 | 71.53 | 2.20 |
| Hashing wall-time (ms) | 0.658 | 29.058 | 0.404 | 43.552 |
| Hashing managed allocations (MiB) | 0.024 | 10.414 | 0.024 | 10.414 |

This demonstrates a reproducible reduction in the **recorded inclusive
synchronous resolver-body work** in this workload, despite increased hashing
cost. The time magnitudes vary across CI runs, and LSP latency did not
consistently improve. These figures are **not** resolver-only CPU seconds,
peak RSS, retained heap size, exclusive allocations or general soundness
measurements. Nested calls may make summed inclusive costs count some work
more than once. Raw event traces permit a stricter exclusive attribution
in future work.

[Profiler CI execution](https://github.com/Formal-Computing/dafny-incremental-resolver/actions/runs/41329209347).
