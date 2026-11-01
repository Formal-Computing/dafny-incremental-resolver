# AIR SATLIB mixed-edit experiment

Five controlled modifications to a 298-clause Dafny program. Cache results are observations, not proofs of safe reuse.

| Edit | Original hits/misses | Experimental hits/misses | Named module effect in experimental |
|---|---:|---:|---|
| provider-value-changed | 1/8 | 5/4 | AirUF50:MISS, AirAIM50:HIT, AIR_Inspector:MISS |
| provider-value-restored | 1/8 | 5/4 | AirUF50:MISS, AirAIM50:HIT, AIR_Inspector:MISS |
| independent-suffix-insertion | 1/8 | 7/2 | AirUF50:HIT, AirAIM50:HIT, AIR_Inspector:HIT |
| independent-suffix-restoration | 1/8 | 7/2 | AirUF50:HIT, AirAIM50:HIT, AIR_Inspector:HIT |
| prefix-position-shift | 1/8 | 1/8 | AirUF50:MISS, AirAIM50:MISS, AIR_Inspector:MISS |

Interpretation: provider-value edits should invalidate AirUF50 and its dependent AIR_Inspector, but allow unrelated AirAIM50 reuse. Independent suffix-length edits should leave earlier module positions unchanged. A prefix insertion shifts earlier module coordinates and should fail closed. Actual behavior must be checked above.

Test data: original AIR SATLIB CNFs, not representative hand-written Dafny. Resolver-only CPU and peak RSS are not measured.
