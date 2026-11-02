# Handwritten and seven-SATLIB differential test: second archived CI run

CI: https://github.com/Formal-Computing/dafny-incremental-resolver/actions/runs/41443941786
Code commit: 063bfca17122ad9b32f50d234ec89869732aa16f.

Original CI outcome: failed at the handwritten hover comparator due to an
overstrict accepted-prefix condition; unlike the SATLIB hovers, the selected
handwritten function hover contains only the fenced Dafny type signature.
The comparator was corrected to accept precisely this additional shape.

Post-hoc verification against archived, unmodified per-mode JSON:
- Seven SATLIB docs: 252/252 exact diagnostics, definition locations and
  stable displayed Dafny type signature comparisons; raw hover includes 44
  asynchronous verification status differences, deliberately not compared.
- Handwritten project: 45/45 comparisons of the same stable observable kinds;
  raw handwritten hover status differences: 0.
- Handwritten post-open cache events: original 4 hits / 36 misses; content-aware
  15 hits / 25 misses. Eleven avoided misses in a four-edit, fixed five-module
  trace; no causal speedup or proof of soundness.
- Fresh CLI on five handwritten revisions separately verifies 12,12,10,12,12
  obligations, with expected error counts 0,0,2,0,0. This is not the LSP
  cached-verifier oracle; LSP diagnostics are resolver hints and unchanged
  across the five versions, so we do **not** claim LSP verifier-equivalence.

The comparator fix was made AFTER inspecting the failing CI. This archive is
research evidence, not an independently green production release.
