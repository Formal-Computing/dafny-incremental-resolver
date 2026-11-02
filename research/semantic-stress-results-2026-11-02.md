# Semantic stress experiment: measured observational equivalence

**Research date:** 2 November 2026
**Pinned Dafny:** de36f2ec1f9c530080eff7929ae28229f45da069
**Original GitHub Actions evidence:** 41449269625, prototype head caa58b5
**Reanalysis:** strict comparator v3, archived JSON and SHA-256 manifest in
\`experiments/results/2026-11-02-semantic-stress-41449269625/\`.

## Core result

Ten deliberately constructed edit traces contain **75 source revisions**.
Each is executed in five independent modes: original upstream; patched
baseline; experimental content/position caching under explicit unsafe research
opt-in; fresh *semantic resolution* while retaining the parser cache; and
fully uncached parser plus semantic resolution.

For each revision, compare three cached modes and the fully uncached mode to
the fresh-semantic resolver. Exact source strings must agree.

| Nontrivial comparison | Matches | Divergences |
| --- | ---: | ---: |
| Diagnostic snapshots (code, severity, text, source, ranges, related origins) | **300 / 300** | 0 |
| Selected symbol definition targets and stable typed Dafny hover signatures | **256 / 256** | 0 |
| **Total informative checks** | **556 / 556** | **0** |

All 75 revisions yield diagnostics, but only **64 revisions** select a
definition/hover query; four comparisons per queried revision produce 256
selected semantic comparisons. The other 11 revisions have no selected query.
The earlier raw 600-check comparator counted 44 \`None==None\` optional-query
checks; these are now deliberately excluded from the informative denominator.

## Observed hover nondeterminism and corrected analysis

**The initial comparator run failed**, reporting 16 exact-hover differences
on revisions 2–5 of the 298-clause AIR/SATLIB case study. Inspecting the
archived JSON reveals that all original/experimental/patched-baseline and
fully-uncached modes agree on the *same code declaration and definition
target*. The fresh-semantic/no-resolver-cache mode sometimes reported
\`Success\` while other modes reported \`Verification not started yet\`,
or vice versa. These strings come from asynchronous verification progress
shown above the fenced Dafny signature in hover.

The v3 comparator preserves **exact diagnostics and definition locations**
and every fenced Dafny code signature/type block (or exact hover if there
is no such block). It records the 16 excluded volatile verification-hover
differences *separately*; none is treated as proof that verifier outcomes
are equivalent. The comparator's self-test deliberately changes a Dafny
signature from \`int\` to \`bool\` inside a fenced code block and **rejects**
that case. Corrupted diagnostic and parser-oracle mismatch controls are
also rejected.

Raw unnormalized traces are retained; this is a scoped, documented
interpretation change, not deletion of failed observations.

## Larger SATLIB workload

The primary experiment contains 298 original SATLIB-derived typed clauses
in 359 Dafny lines. Provider changes, independent suffix changes, origin
shifts and a deliberately ill-typed clause were exercised.

A separate 662-clause / 768-line source combines three SATLIB examples.
It is **not included in the 556 checks above**. The large LSP
go-to-definition request times out even with upstream Dafny and with
an extended test timeout; therefore its isolated comparison is deliberately
diagnostic-only, with a separate CI and separate qualification decision.
Local Dafny \`resolve\` accepts both original corpora and rejects a
deliberately ill-typed \`seq<int>\` element (\`true\`), as expected.

## What these results establish (and what they do not)

- There are **no observed differences in these sampled stable semantic
  observations** among the four modes compared to fresh semantic resolution.
- The negative-control cache corruption is detected by the end-to-end
  differential harness.
- This is **not** a theorem about full Dafny semantic soundness or
  mutable \`ModuleResolutionResult\` reuse, and is not exhaustive over
  symbol binding maps, type inference, compiler/project options, plugins,
  files included across project boundaries, or verification outcomes.
- Verification-progress differences remain unresolved for full
  verification-result equivalence. A correctly synchronized explicit
  verifier-outcome oracle is the next distinct validation obligation.
- The workload is controlled and nonrandomized, and this run makes
  **no claim** of general speedup or production readiness.

## Reproduce archived evidence

\`\`\`bash
python3 scripts/test_compare_differential.py
python3 scripts/compare_differential.py experiments/results/2026-11-02-semantic-stress-41449269625
\`\`\`

The archive stores all 50 five-mode scenario trace JSON files, the
fault-injection trace, the v3 normalized comparison report, and a manifest
with SHA-256 for each retained file. The GitHub Actions artifact also
preserves the raw source observations and the initial failed comparator
output. Use the pinned revision and the originally declared sources when
replicating, not the latest upstream Dafny without pinning.
