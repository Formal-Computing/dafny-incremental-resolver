# Research stack integration into main (2026-11-05)

## Included work

This integrates the previously stacked research PRs #1–#14 into one reviewable
repository history, including experimental cache-key patches, differential LSP
oracles, SATLIB corpora, immutable export-summary optimization, formal proof
models, and nonempty immutable observation audits.

**This is integration of a research prototype, not deployment into the upstream
Dafny product.** This repository stores patch files; it does not replace or
deploy the upstream `dafny-lang/dafny` codebase.

## Execution and safety matrix

| Configuration | Result | Scope |
| --- | --- | --- |
| Default flags | Original language-server resolver behavior | No new general semantic reuse |
| `DAFNY_RESEARCH_SAFE_REVALIDATE=1` | Fresh resolution; candidate key used for audit | Conservative experimental oracle |
| `DAFNY_RESEARCH_SAFE_REVALIDATE=1` plus `DAFNY_RESEARCH_IMMUTABLE_EXPORT_SUMMARY=1` | Fresh nonexport modules; genuine skip only in pinned `ModuleExportDecl` no-op dispatch | Limited source-pinned optimization |
| `DAFNY_EXPERIMENTAL_CONTENT_HASH=1` alone | Does not enable unsafe cross-revision hash reuse | Not a standalone optimizer |
| Both `DAFNY_EXPERIMENTAL_CONTENT_HASH=1` and `DAFNY_RESEARCH_UNSAFE_CROSS_REVISION_REUSE=1` | Enables explicitly **unsafe** cross-revision content reuse | Research-only; never production |
| The unsafe flags plus `DAFNY_RESEARCH_SAFE_REVALIDATE=1` | Safe-revalidation branch wins for module resolution | Always fresh for nonexport modules |

A candidate key match, immutable symbol-name audit MATCH, or abstract Dafny
proof theorem cannot establish whole-resolver semantic soundness. There remains
no safe nonempty `ModuleResolutionResult` reconstruction or general speedup
claim. The audit holds only value-only strings, never AST graphs.

## Verification expectations for main integration

- `formal-proof.yml` now verifies `NonemptyImmutableSummaryRefinement.dfy`
  alongside the earlier conditional models.
- `immutable-export-summary.yml` runs against PRs targeting main and main
  changes to integration inputs. It builds pinned upstream Dafny, applies
  patches 0001-0006, checks source-contract anchors, verifies the restricted
  export MISS/HIT, tests nonempty fresh fallback and its audit observations,
  and runs strict semantic/terminal verifier comparisons.
- Reference-model and smoke-test workflows continue to cover independent
  executions. Green checks are evidence of the stated finite scenarios, not
  proof about arbitrary Dafny source programs.

## Scientific obligations still open

1. Identify a nonempty production module subset with a complete semantic
   dependency contract, including imports, options, plugins, scope and failed
   lookups.
2. Specify and implement a current-compilation graph reconstruction algorithm
   preserving binding, diagnostics and verifier outcomes, not only symbol names.
3. Refine the actual C# implementation to the verified model and test negative
   dependencies, cross-revision object identity and cancellation.
4. Demonstrate a real resolver-skipping nonempty HIT and measure end-to-end
   resource savings with controlled methodology.

The repository research patches and archived data should remain reproducible
and version pinned. No claims of production readiness or universal semantic
soundness are authorized by this merge.
