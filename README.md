# Incremental Resolution for Dafny — Research Prototype v0.2

**Research team (proposed):** Dragoș-Andrei Bobu and Ștefan-Alexandru Mercaș  
**Supervision:** Prof. Ștefan Ciobâcă

## Research premise

Dafny already has **module-level resolution caching** in its language server. The present implementation keys cached modules using `ModuleDecl.CloneId`, a defensive proxy for source content. `CachingResolver.cs` explicitly notes that this is a substitute for a true content hash.

This repository investigates whether dependency-aware, position-sensitive *content hashes* can reduce conservative cache misses caused by edits in the same source file without returning stale resolver results.

### Contents

| Path | Purpose | Status |
| --- | --- | --- |
| `src/IncrementalResolver.Core` | Pure C# dependency-graph, revision-diff and cache-key reference model | Implemented; independent of Dafny |
| `tests/IncrementalResolver.SmokeTests` | Zero-NuGet executable checks for adds, changes, invalidation and reuse | **11/11 checks passed** on Paradis Windows (.NET SDK 9, October 29, 2026) |
| `patches/0001-experimental-module-token-hashing.patch` | Experimental opt-in patch for Dafny `CachingResolver` | **Built and tested** on pinned Dafny commit; safety still under investigation |
| `examples/two-modules.dfy` | Two modules in one file, for IDE testing | Prepared |
| `docs/architecture.md` | Architectural analysis, threat model and acceptance criteria | Prepared |
| `docs/research-brief.md` | Suggested paper/project framing | Prepared |
| `docs/ci-results-2026-10-29.md` | Reproducible upstream build and test evidence | **PASS:** 2 targeted experiments; 8 upstream tests; 1 skipped upstream |
| `docs/code-review-guide.md` | Source-reading route and review questions | Prepared |

The pure C# cache **does not contain Dafny's parser or semantic resolver** and must not be reported as a working full incremental Dafny resolver. The patch is a genuine integration candidate against Dafny's existing module-level caching; it is **experimental and not proven safe**. This separation is deliberate for review.

## Reproduce the reference-model checks

```shell
dotnet run --project tests/IncrementalResolver.SmokeTests/IncrementalResolver.SmokeTests.csproj
```

.NET 8+ is sufficient. No NuGet packages, web services or database are required for these checks.

## Integrate the patch in a Dafny checkout

Use a throwaway or dedicated branch, and pin the exact inspected Dafny source version for reproducibility:

```shell
git clone https://github.com/dafny-lang/dafny.git --recurse-submodules
cd dafny
git checkout de36f2ec1f9c530080eff7929ae28229f45da069
git switch -c research/incremental-resolver
# Copy the patch into this repository's parent, or supply its full path:
git apply --check ../dafny-incremental-resolver/patches/0001-experimental-module-token-hashing.patch
git apply ../dafny-incremental-resolver/patches/0001-experimental-module-token-hashing.patch
```

Build Dafny following its **current** developer instructions; SDK and submodule requirements may change between commits. Run with normal caching first, then start the language server in an environment with `DAFNY_EXPERIMENTAL_CONTENT_HASH=1` and repeat identical edits. This variable enables the research-only hashing branch; otherwise the original CloneId-based caching behavior remains active.

**Important:** `dafny resolve` launched separately for each revision does not exercise the persistent language-server cache. Cache-hit measurements must be made within a long-running language-server session or dedicated integration-test harness, not independent CLI processes.

## Research hypothesis and no-go conditions

Hypothesis: In the language-server workflow, using declaration-local token content plus source-origin positions and transitive module-dependency hashes can avoid some module-cache misses after same-file edits.

This is *not* equivalent to declaration-level incremental resolution inside a module. That is a later, harder research stage requiring intra-module semantic dependencies.

Do **not** claim performance gains or semantic correctness before executing controlled long-running IDE tests, including errors, import changes, renames, shifted source locations, shadowing, module exports and changed resolver options. A single observed stale result disqualifies the optimization until corrected.

## Upstream source reviewed

- [CachingResolver.cs](https://github.com/dafny-lang/dafny/blob/de36f2ec1f9c530080eff7929ae28229f45da069/Source/DafnyLanguageServer/Language/CachingResolver.cs)
- [CachingParser.cs](https://github.com/dafny-lang/dafny/blob/de36f2ec1f9c530080eff7929ae28229f45da069/Source/DafnyLanguageServer/Language/CachingParser.cs)
- [ProgramResolver.cs](https://github.com/dafny-lang/dafny/blob/de36f2ec1f9c530080eff7929ae28229f45da069/Source/DafnyCore/Resolver/ProgramResolver.cs)
- [ModuleDecl.cs](https://github.com/dafny-lang/dafny/blob/de36f2ec1f9c530080eff7929ae28229f45da069/Source/DafnyCore/AST/Modules/ModuleDecl.cs)
- [DafnyLangSymbolResolver.cs](https://github.com/dafny-lang/dafny/blob/de36f2ec1f9c530080eff7929ae28229f45da069/Source/DafnyLanguageServer/Language/Symbols/DafnyLangSymbolResolver.cs)


## Automated Dafny integration checks

A separate workflow, `.github/workflows/dafny-integration.yml`, does **not** run automatically on each push. Launch it explicitly from GitHub Actions (`Dafny resolver integration`) or with:

```sh
gh workflow run 'Dafny resolver integration' --ref main
```

The job clones a pinned upstream Dafny revision, applies the experimental patch, injects an xUnit regression method into upstream `CachingTest`, and runs the same edit sequence twice in separate testhost processes (baseline and experimental). The existing upstream cache regression suite is also run.

This targets a documented upstream limitation: `CachingTest.ResolutionInSingleFileIsCached` is currently skipped with the reason *need hashing on modules to work*. Our new test uses valid Dafny function declarations and verifies the independent same-file module scenario before attempting a larger optimization.

See `docs/evaluation-protocol.md` for the acceptance criteria. An upstream patch compiling successfully is not itself evidence of correct incremental semantic resolution.
