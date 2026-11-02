# Independent complete pinned-Dafny integration: green, 2 November 2026

Workflow: https://github.com/Formal-Computing/dafny-incremental-resolver/actions/runs/41445712712
Input revision: af55f558487002e7e2f75f302f6056799d46ff20

The complete pinned language-server CI pipeline succeeded with four resolver
modes, seven SATLIB-source-derived Dafny documents, the five-edit handwritten
Dafny program, short semantic differential oracle, fault injection, existing
upstream caching regression suite, and reference-model checks.

Per exact source/observation comparator:
- 7 SATLIB documents, 4 revisions/doc, 3 cached modes compared to a fresh
  semantic-resolver oracle: **252/252 matching** exact diagnostic tuples,
  go-to-definition locations, and fenced Dafny type signatures.
- The 84 raw SATLIB hover responses from cached modes differ from fresh in
  **31** comparisons due to transient verifier status and resource-usage text.
  These volatile fields are deliberately EXCLUDED from stable comparison.
- 5 revisions of handwritten proof-bearing program in four modes:
  **45/45 matching** same stable observable classes; zero raw hover differences
  in this sample; underlying upstream/experimental cache events **4/36**
  versus **15/25** hits/misses over four post-open revisions.
- Across 7 SATLIB programs: upstream **21/105** vs experimental **49/77**
  hits/misses over three post-open revisions per source (28 fewer misses).
- Separate five-revision *fresh CLI verifier* checks:
  12/0, 12/0, 10/2, 12/0, 12/0 verified/errors, with expected dependent
  postcondition failure and restoration. The LSP diagnostic observations were
  resolver/rewriter hints, not the CLI proof errors. This does NOT prove full
  cached-LSP verifier outcome equivalence.

The first two LSP workflow runs were originally red from overly strict
hover comparisons; raw traces and failure explanations are preserved in
earlier experiment archives. This third independent workflow is successful
after defining a narrower and explicit semantic observation contract.

No general resolver soundness theorem, end-to-end speedup or retained-memory
saving is claimed. Actual source SHA and source DIMACS checksums are in
tests/air/corpus/manifest.json. Four-mode fresh condition disables semantic
resolver caching, not Dafny's parser cache. See the raw JSON and report files.
