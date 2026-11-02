# SATLIB multi-document LSP differential experiment

Documents: 7; original clauses: 1131; revisions per document: 4; four resolver modes.

| Instance | Clauses | Original (hits/misses) | Experimental (hits/misses) |
|---|---:|---:|---:|
| random3sat-20-sat | 91 | 3/15 | 7/11 |
| random3sat-50-sat | 218 | 3/15 | 7/11 |
| random3sat-50-unsat | 218 | 3/15 | 7/11 |
| aim-50-sat | 80 | 3/15 | 7/11 |
| aim-50-unsat | 80 | 3/15 | 7/11 |
| pigeonhole-7-unsat | 204 | 3/15 | 7/11 |
| dubois-30-unsat | 240 | 3/15 | 7/11 |

Independent comparisons: 252, errors: 0.
Each comparison is a mode/revision/observable-kind pair, not an independent program.
Raw hover responses differed in 31 comparisons solely by asynchronous verification status/RU (these statuses are NOT compared).
The stable Dafny type-signature block in hover IS compared; absent or unknown output fails closed.
Fresh semantic resolution still retains the parser cache.
These are transformed CNF documents, *not* SAT-solver runs or evidence of end-to-end verifier soundness.
