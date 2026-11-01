# Case study: AIR SATLIB data as a substantial Dafny semantic-resolution workload

## Research question

Can a Dafny Language Server avoid rerunning semantic resolution for unchanged,
clause-heavy modules when an unrelated function is edited **within the same source file**?

This measures **Dafny language-server resolution**, not the time required to solve SAT
instances. DIMACS CNF is source data: it does not directly exercise Dafny's resolver.

## Data provenance

The immutable SATLIB originals are from
[Formal-Computing/cdcl-sat-solver](https://github.com/Formal-Computing/cdcl-sat-solver/tree/88247ab605ee0e3da2aca711885e3340eb78c782/benchmarks/satlib)
at commit 88247ab605ee0e3da2aca711885e3340eb78c782.
The generator checks each original file's SHA-256 against the AIR manifest.

| SATLIB instance | Classification | Vars | Clauses | Dafny module |
| --- | --- | ---: | ---: | --- |
| uf50-01.cnf | SAT | 50 | 218 | AirUF50 |
| aim-50-1_6-no-1.cnf | UNSAT | 50 | 80 | AirAIM50 |
| **Total** | | **100 (sum across instances)** | **298** | |

The CI input is converted to a single **359-line Dafny program**. Every selected original
clause becomes a distinct, typed Dafny constant of type `seq<int>`, and each
benchmark module contains a typed aggregate of the clauses. AIR_Inspector
imports all three and uses their typed declarations. AIR_WorkingEdit contains
a final function that can be edited without changing the other modules.

## The edit, step by step

1. Open the generated Dafny file in one persistent Language Server session.
2. Resolve all modules and construct the module cache.
3. Replace `AIR_WorkingEdit.RevisionTag(): int { 10 }` with the variant
   ending in `{ 11 }`, then alternate the digits; the two versions have
   identical length, so every preceding source token retains its URI and
   absolute source position.
4. **Upstream baseline:** a file reparse may regenerate module CloneIds, so
   the source-identical benchmark modules can suffer conservative misses.
5. **Experimental resolver:** content-aware keys permit reuse of unchanged
   modules when dependency hashes and context-sensitive identity are stable.
6. After the measured edits, insert a new comment **at the beginning** of
   the file. This shifts all downstream token positions; the experimental
   policy is expected to issue conservative misses rather than reuse source
   locations which may have changed.

This is a good test of *one known reuse opportunity*, not a representative
distribution of realistic developer edits. The source is generated from real
benchmarks, but is not an independent hand-written Dafny software project.

## Measurement protocol

Four separate testhost configurations: unmodified upstream caching,
the patched upstream baseline (experimental flag off), opt-in
content-aware cache keys, and resolution caching disabled
(`UseCaching=false`). **The last one still retains the parser cache.**

For each mode we record module-resolution hit/miss log events, a per-module
breakdown, wall time from applying the document edit until the LSP update
completes, and the allocated bytes in the *entire testhost process*.

The robust resource-saving metric is the **number of complete module
resolutions not performed**. Elapsed time includes the parser, client
scheduling and LSP notification latency; process allocations also contain
the test harness. Do not claim an isolated speedup or memory saving from
those figures without follow-on controlled profiling.

The fault-injection and semantic-oracle tests live in the parent
[research PR #2](https://github.com/Formal-Computing/dafny-incremental-resolver/pull/2).
The AIR case study is developed as
[research PR #3](https://github.com/Formal-Computing/dafny-incremental-resolver/pull/3).

## Reproduce and inspect

- Generator: `tests/air/generate_satlib_fixture.py`
- CI source data converted to Dafny: `tests/air/satlib_case_study.dfy`
- Checksums and source manifest: `tests/air/satlib_case_study.json`
- LSP integration test: `tests/air/ResearchAirSatlibCaseStudy.txt`
- Install into pinned Dafny CachingTest: `scripts/install_air_case_study.py`
- Analysis from CI JSON: `scripts/summarize_air_case_study.py`

To independently reproduce the generated file, clone the pinned AIR source
and run the generator with its directory as the sole argument.
The resulting fixture SHA-256 is recorded in `satlib_case_study.json`.

## Evidence boundary / follow-on work

- Need a larger, pre-registered **mixed edit-trace corpus** to estimate how
  often equal-position reuse is achievable under actual typing edits.
- Need sound semantic-oracle coverage for symbol bindings, types and
  downstream verifier output across this large workload.
- Need process-isolated resolver timing, allocations and memory profiling
  and counterbalanced repetitions on multiple machines.
- Need realistic hand-maintained Dafny sources, in addition to the converted
  SATLIB exercise, before generalizing to production use.

## Larger preserved stress input

The original 662-clause 768-line translation from uf50-01, hole7, dubois30 is preserved as tests/air/satlib_stress_662.dfy with its manifest. It exceeded the pinned LSP test cancellation window and has **no validated resource-savings measurement**. Regenerate it with the generator and argument `stress`.
