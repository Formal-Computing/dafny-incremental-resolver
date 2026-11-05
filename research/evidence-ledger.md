# Evidence ledger — reproducible sources

| ID | Claim | Source / commit | Scope |
|---|---|---|---|
| O29-PRECISION | Alpha HIT in experimental, MISS in baseline after same-length Beta edit; Beta MISS both | Actions https://github.com/Formal-Computing/dafny-incremental-resolver/actions/runs/40892523245 at 2a9d765 | One real Dafny LSP cache-log trace |
| O29-REGRESS | Two targeted conditions pass; 8 upstream caching tests pass and one skipped | Same Actions run 40892523245 | Upstream test corpus |
| O29-REF | Eleven synthetic reference-model checks pass | Repo `tests/IncrementalResolver.SmokeTests/Program.cs`; reexecuted 30 October on Paradis with .NET 10 roll-forward | Does not exercise Dafny parser/resolver |
| N30-INITIAL-FAIL | Initial trace harness awaited absent empty diagnostics, timed out in all five original-upstream tests | Actions https://github.com/Formal-Computing/dafny-incremental-resolver/actions/runs/41068377799 at 20208cb | Harness failure, not cache counterexample |
| N30-DIFF | Original upstream, patched baseline, experimental vs fresh uncached: 54/54 extracted diagnostic comparisons match across 18 source revisions, five deterministic scenarios | Actions https://github.com/Formal-Computing/dafny-incremental-resolver/actions/runs/41069722625 at 8d374e75c959809744474f874383a2fa4ab608e2, artifact `dafny-research-traces-8d374e75c959809744474f874383a2fa4ab608e2/differential-report.json` | Real Dafny diagnostics ONLY. No binding/verification/semantic proof |
| N30-DIAG | Fresh diagnostic counts per revision: independent [0,0,0,0]; dependency [0,1,0,1]; shadowing [0,0,0]; roster [0,0,1]; recovery [0,1,0,1] | Same run and artifact `fresh-*.json` | 18 revisions |
| N30-BUILD | Unmodified and patched pinned Dafny language server test project builds succeed, patch applies cleanly, baseline and experimental tests and existing upstream cache regressions pass | Actions 41069722625, full job steps | Controlled .NET 8 Ubuntu GitHub Actions environment |
| PERF-NONE | No valid median latency, allocation, peak memory or speedup estimate | No benchmark result artifacts exist | **DO NOT CLAIM ANY PERFORMANCE NUMBERS** |

All claims must cite a run, input trace, exact commit, and test scope. Successful 54 comparisons do not cover symbol-binding maps, types, verification, configuration changes, plugin state, or mutable-AST correctness in general.
| N30-DIFF-V2 | Correct diagnostic code union extraction and full related-origin URI; 54/54 comparisons match fresh resolution | Actions https://github.com/Formal-Computing/dafny-incremental-resolver/actions/runs/41071268299 commit b484785e3b313391f3bdd1e4a8135db87ce4e757, JSON snapshots in `experiments/results/2026-10-30-ci-41071268299/` | 5 real Dafny LSP scenarios, 18 revisions, diagnostic-only |
| N30-FAULT-CAL | Comparator rejects a modified experimental diagnostic; deliberately faulty actual Dafny cache not tested | same run, `scripts/calibrate_differential.py` | Comparator sensitivity only |
| N30-LSP-PILOT | End-to-end LSP update medians in ms after 3 warmups, 17 timed edits each: original=20.3143, patched-baseline=12.3859, experiment=9.9976, fresh=11.7054; Alpha hits 0/0/17/N.A. respectively | same run, 4 `*-benchmark.json` plus `benchmark-summary.json` | One CI runner, nonrandomized mode order, includes harness/notification cost; **NOT a resolver-only or causal speedup result** |
