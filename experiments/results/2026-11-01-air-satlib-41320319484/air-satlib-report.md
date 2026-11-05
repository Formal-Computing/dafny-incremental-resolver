# AIR SATLIB to Dafny incremental resolution case study

Generated from Formal-Computing/cdcl-sat-solver at 88247ab: 298 real clauses, two source benchmark instances, converted into typed Dafny constants and a dependent summary module. This measures incremental semantic resolution of the generated Dafny program, not CDCL runtime.

## Results (one Ubuntu CI runner; 2 warmup + 4 measured edits per mode)

| Resolver mode | Median LSP ms | Cache hits | Cache misses | Median total process allocations (bytes) |
|---|---:|---:|---:|---:|
| original | 6677.434 | 4 | 32 | 2,275,706,840 |
| fresh | 5817.637 | 0 | 0 | 2,274,184,076 |
| patched-baseline | 6036.497 | 4 | 32 | 2,275,769,036 |
| experimental | 6225.327 | 28 | 8 | 2,259,711,200 |

## Tracked clause data modules (4 measured revisions)

| Mode | Module | Hits | Misses |
|---|---|---:|---:|
| original | AirUF50 | 0 | 4 |
| original | AirAIM50 | 0 | 4 |
| original | AIR_Inspector | 0 | 4 |
| fresh | AirUF50 | 0 | 0 |
| fresh | AirAIM50 | 0 | 0 |
| fresh | AIR_Inspector | 0 | 0 |
| patched-baseline | AirUF50 | 0 | 4 |
| patched-baseline | AirAIM50 | 0 | 4 |
| patched-baseline | AIR_Inspector | 0 | 4 |
| experimental | AirUF50 | 4 | 0 |
| experimental | AirAIM50 | 4 | 0 |
| experimental | AIR_Inspector | 4 | 0 |

## Worked edit trace
1. The LSP opens a single generated Dafny file containing 298 original SATLIB clauses as typed declarations.
2. A small function AIR_WorkingEdit.RevisionTag() follows the large unchanged source modules.
3. Four measured revisions alternate only 10 and 11 (equal source length); unchanged module source tokens/positions remain identical.
4. The upstream clone-identifier-based key conservatively misses after a fresh parse. The experimental content-aware key may reuse unchanged modules; the table records actual log entries for each.
5. A final prefix insertion shifts all module source positions and is expected to conservatively invalidate them. Prefix-insertion diagnostics are captured separately in air-satlib-summary.json.

## Limitations
- Same-length edit class favors position-sensitive caching.
- Time is end-to-end notification latency, not resolver CPU.
- GC allocated bytes are entire in-process client+server; not isolated resolver memory.
- Sequential modes on one CI runner are not randomized or independent speedup evidence.
- Dafny semantic resolver is tested, not CNF satisfiability.
- The no-resolution-cache mode still uses Dafny's parser cache.

The primary resource-saving quantity is the observed number of module resolutions avoided, not a defensible standalone CPU/memory speedup. Repeat on independent runners with counterbalanced modes and isolated resolver timing before drawing speedup conclusions.
