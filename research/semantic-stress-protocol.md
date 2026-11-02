# Semantic differential stress-testing protocol · 2 November 2026

## Research question

For a sequence of source edits, does the experimental Dafny language-server
resolver produce the same *observed diagnostics, go-to-definition targets, and
hover information* as a resolver with its semantic cache explicitly disabled?

This is an observational test, **not** a complete semantic soundness theorem.
In particular, it does not inspect every symbol binding, type, resolved AST
object, verification output or all plugin/option states. The experimental reuse
requires the two explicitly unsafe research flags; normal execution remains
guarded.

## New experimental controls

The upstream \`UseCaching=false\` setting disables **both** parsing and semantic
caching. A research-only, separately applied patch
(\`patches/0003-research-fresh-semantic-oracle.patch\`) introduces
\`DAFNY_RESEARCH_DISABLE_SEMANTIC_CACHE=1\` into the language server resolver
selector while leaving the parser's \`UseCaching\` option unchanged.

There are now five modes:

| Mode | Parser cache | Semantic cache |
| --- | --- | --- |
| Original upstream | enabled | upstream |
| Patched baseline | enabled | upstream-compatible |
| Experimental | enabled | content/position, *unsafe research opt-in* |
| Fresh semantic | enabled | disabled, via independent research switch |
| Fully uncached | disabled | disabled, using upstream UseCaching=false |

Every mode uses the same exact source strings for every revision. Compare the
three cached modes to *fresh semantic* and compare *fresh semantic* to *fully
uncached*. If these two no-semantic-cache oracle modes diverge, do not make
a resolver-soundness conclusion from the trace.

## Scenarios

In addition to seven existing short deterministic traces (25 revisions):

- **stress_graph** (24 revisions): edits to provider and secondary signatures,
  renamed declarations, introduction of an unrelated module, source-position
  shifts, and suffix-only edits; go-to-definition and hover on a consumer call.
- **stress_scope** (18 revisions): opened-import choices, local shadowing,
  ambiguous/duplicate opened imports, missing declarations, and independent
  changes; go-to-definition and hover on the resulting call.
- **air_semantic** (8 revisions): the 298-clause AIR/SATLIB generated Dafny
  source (359 lines); provider clause changes/restores, independent suffix
  length edits, prefix position shifts, a deliberately invalid typed clause,
  and recovery; semantic query on the AIR inspector's imported Clauses.
- **air_semantic_662** (7 revisions): the 662-clause, 768-line generated Dafny
  source from three SATLIB instances; a similarly varied dependency/edit/recovery
  sequence. This is a different, larger corpus, not merely another repeat of
  the 298-clause file.

**Total: 82 revisions in 11 scenarios** per execution mode. These are not 82
independent real-world projects and are not a representative random sample of
editing behavior. The two SATLIB-derived test programs encode CNF clauses into
typed Dafny constants; they are *resolver workloads*, not SAT-solver or
verification benchmarks.

The stress trace metadata contains source text, revision index, normalized
diagnostics (including code, severity, messages, related locations and ranges),
and the selected symbol query's definitions and hover text.

## Fail-closed comparator

\`scripts/compare_differential.py\` requires a complete set of five-mode traces
for all 11 named scenarios, matching revision counts, matching source text, and
non-null semantic observations for the queried scenarios. It rejects missing
observables, mismatched diagnostics and mismatched selected hover/definition
snapshots, and it tests parser/no-parser fresh-oracle parity.

\`scripts/test_compare_differential.py\` validates that the comparator rejects
deliberately corrupted diagnostics, altered semantic snapshots, differences
between the two oracle modes, and missing traces. The existing integration
test also runs a deliberately unsound real cache-key branch as a negative
control.

## Reproduction

Run the pinned-source workflow \`dafny-integration.yml\` with
\`workflow_dispatch\` on the research branch. It installs test methods and all
three patches onto Dafny commit
\`de36f2ec1f9c530080eff7929ae28229f45da069\`, compiles the language server
tests, and collects per-mode JSON and the strict differential report.
The workflow requires .NET 8 and Z3; local \`paradis\` with only .NET 10 cannot
directly run the pinned .NET 8 integration project without a separate SDK.

For a local comparator validation (does not execute Dafny):
\`python3 scripts/test_compare_differential.py\`.

## Correctness gates / next obligations

1. A passing 82-revision run is *positive evidence for sampled observables*
   only. Do not infer soundness for unqueried symbols or for verification.
2. Make the LSP oracle collect verifier results and complete resolved binding
   and type maps before claiming verification-observable equivalence.
3. Add multi-file include/refinement tests and option/plugin/rewriter lifecycle
   changes; the token hash still fails to encode all such context.
4. Audit mutable \`ModuleResolutionResult\` reattachment and transition toward
   immutable semantic summaries or safe cloning.
5. When reporting speedup, separately use randomized independent workloads,
   repeated paired end-to-end measurements, CPU time, and memory statistics.
6. If any counterexample occurs, preserve the exact sources and revision
   pair and diagnose whether it stems from parser behavior, missing dependency
   fingerprints, stale mutable state, or test synchronization.
