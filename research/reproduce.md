# Reproduction — Dafny incremental semantic resolution

**Upstream pin**: dafny-lang/dafny @ `de36f2ec1f9c530080eff7929ae28229f45da069`. Research branch: `research/semantic-contract-hardening`; validated commit: `8d374e75c959809744474f874383a2fa4ab608e2`. The original independent-module experiment is in Actions 40892523245. Four-mode diagnostic differential experiment: Actions 41069722625 (successful).

## Reproduce with CI (recommended)

1. Open Actions → **Dafny resolver integration**; run on `research/semantic-contract-hardening`.
2. The workflow checks out the pinned full Dafny source and recursive submodules on ubuntu-24.04, sets up .NET 8, installs Z3, builds unmodified upstream tests and runs all five scenarios under original upstream and uncached fresh modes.
3. It applies the research patch, rebuilds and repeats the same traces with patched original caching and experimental caching, tests existing upstream cache cases and the 11 synthetic reference-model checks.
4. Download the uploaded `dafny-research-traces-<commit>` artifact. It contains 20 trace JSON files (four modes × five scenarios) and `differential-report.json`, including failures if emitted.
5. Inspect `scripts/compare_differential.py`, which asserts exact revision inputs and diagnostic equivalence against fresh resolution. `scripts/calibrate_differential.py <artifact directory>` deliberately mutates one experimental diagnostic and verifies comparison failure. This calibration does NOT test deliberately faulty Dafny cache behavior.

## Local core tests

```sh
dotnet run --project tests/IncrementalResolver.SmokeTests/IncrementalResolver.SmokeTests.csproj
```

.NET 8 SDK/runtime recommended. On .NET 10-only setups the reference-model runtime can be run using `DOTNET_ROLL_FORWARD=Major` without changing the research pin. These 11 checks use synthetic snapshots, **not actual Dafny semantics**.

## Manual pinned integration

```sh
git clone --recursive https://github.com/dafny-lang/dafny.git dafny
git -C dafny checkout de36f2ec1f9c530080eff7929ae28229f45da069
git -C dafny apply --check ../dafny-incremental-resolver/patches/0001-experimental-module-token-hashing.patch
python3 dafny-incremental-resolver/scripts/install_integration_test.py dafny/Source/DafnyLanguageServer.Test/Synchronization/CachingTest.cs
python3 dafny-incremental-resolver/scripts/install_differential_test.py dafny/Source/DafnyLanguageServer.Test/Synchronization/CachingTest.cs
git -C dafny apply ../dafny-incremental-resolver/patches/0001-experimental-module-token-hashing.patch
cd dafny
dotnet tool restore
dotnet build Source/DafnyLanguageServer.Test/DafnyLanguageServer.Test.csproj -c Debug
```

For four-mode comparison use the exact CI commands (including distinct testhost processes, the `DAFNY_RESEARCH_MODE` and `DAFNY_EXPERIMENTAL_CONTENT_HASH` variables, `DAFNY_RESEARCH_OUTPUT_DIR`). Merely invoking `dafny resolve` in new independent CLI processes cannot measure persistent cache reuse.

## Interpretation

The differential corpus extracts diagnostic message/code/severity/source and ranges, and selected related locations. Its successful 54/54 comparisons do **not** prove complete semantic soundness, binding/type equivalence or verification equality. No controlled latency/allocations benchmark was run; no speedup is supported.

Known untested invariants: plugin/rewriter dependencies, modified project settings, hidden name-lookup state, AST result aliasing, cross-file includes and declaration-level incremental resolution. See `research/soundness-model.md`, `research/safety-boundaries.md`, and `research/evidence-ledger.md`.
