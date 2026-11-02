# Seven-source SATLIB/Dafny LSP experiment: archived raw evidence

Run: https://github.com/Formal-Computing/dafny-incremental-resolver/actions/runs/41441398022
Commit: c4f7904edba77954c7f87f558e8a718b566d35d2.
Seven separate source files, 1,131 checksum-verified SATLIB clauses
converted to typed Dafny declarations (not a SAT-solving benchmark).
Four resolver modes each produce seven raw traces, so 28 JSON documents.
Three post-open revisions: independent suffix value, provider value, prefix shift.

**Original workflow outcome: FAIL in the strict composite hover comparator.**
All 84 fresh-oracle diagnostic and all 84 go-to-definition comparisons
matched, but 30/84 raw hovers differed by asynchronous verifier status:
"not started", "still verifying", or "success" with resource usage.
They retained identical displayed Dafny declaration signatures.

The revised, narrower comparator preserves exact diagnostic fields,
definition locations, and a unique fenced Dafny type signature per hover;
it does NOT compare verification-progress state or resource counts. It
fails closed on an absent/unfamiliar hover response. Post-hoc replay:
252/252 stable comparisons matched; 30 raw hovers still differ.
This normalization was chosen after inspecting a failed strict comparison,
and should be validated again on an independent execution.

Cache counts across seven documents and three edits:
- Original upstream: 21 hits and 105 misses.
- Experimental: 49 hits and 77 misses.
- 28 avoided misses, with uniform graph shape across documents.
No CPU-time speedup, retained-memory saving or soundness theorem follows.

The archive includes satlib-matrix-report.json, report Markdown, and raw traces.
