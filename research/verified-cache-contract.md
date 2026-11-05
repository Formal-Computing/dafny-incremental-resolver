# Mechanically checked abstract cache contract (2 November 2026)

Proof file: `tests/formal/CacheSoundness.dfy`.

## Result

Verified on `paradis-workstation` under Dafny 4.11.0:
```
dafny verify tests/formal/CacheSoundness.dfy
Dafny program verifier finished with 8 verified, 0 errors
```

## Exactly what was verified

- `ValidCache` is inductive: a cache populated with values equal to fresh `PureResolve` observations remains valid after an arbitrary revision's lookups/insertions.
- `ResolveIncrementally` yields the same observation sequence as fresh resolution for arbitrary keys and any initially valid cache.
- `ResolveTwoRevisions` composes the invariant across two revisions, including reused results.
- A local-content-only fingerprint can miss a newly available name, yielding different lookup observations with identical unsafe keys.
- There is a counterexample to universal speedup when experimental hash overhead exceeds avoided resolution work.

`PureResolve` is opaque in the proof: the cache theorem does not assume its example implementation. Keys are exact immutable data values. The formal proof establishes the usual memoization correctness theorem **conditional on complete context encoding**, not that Dafny's resolver is pure or that its actual cache key is complete.

## Limitations / Dafny source-level proof obligations

1. **Complete semantic context.** Actual key includes content, token origin, dependency fingerprints, builtins, and module roster. It does NOT demonstrably cover every negative lookup, compiler/project option, plugin, rewriter and contextual namespace effect.
2. **Mutable results.** Dafny caches `ModuleResolutionResult` holding AST, reporter and signature structures. Establish clone/immutability and safe reattachment across compilations, including symbol identity.
3. **Cryptographic key.** SHA-256 is modeled as collision-free structural equality. Real key equality has only a computational assumption, not mathematical injectivity.
4. **Pipeline behavior.** Verify invariance of parse recovery, pre/post rewriters, cancellation and downstream verification. The model isolates semantic resolution.
5. **Oracle and coverage.** Compare complete resolved binding and verification observations for many edit traces, including the AIR mixed-edit sequence, not only diagnostics/selected hover/definition.

## Stronger goals

The next formal step is a refinement relation `ImplState ~ AbstractState` for the pinned Dafny LSP revision. Each actual cache hit would need to establish `CompleteKey` and `SafeReuse`; without those facts the soundness theorem must not be applied. Default to a miss whenever those conditions cannot be proved.

## Performance and readiness

No cache optimization can promise a universal runtime speedup: equal or absent hit opportunities plus additional hashing overhead produce a counterexample. Establish a workload distribution, use randomized paired runs across different Dafny projects and edit traces, measure cold/warm end-to-end latency and CPU/memory, report confidence intervals and negative cases.

Production readiness is a release decision based on gates, not a single theorem. Require the refinement audit, differential verifier-output oracle, fault injection, option/plugin/URI/recovery changes, cancellation/concurrency stress, memory-boundedness, feature-flag rollback, and independent upstream maintainer review. Current experiment remains opt-in and not production-qualified.

## Correction to manuscript fresh-oracle description

At pinned Dafny commit de36f2e, `DafnyLangParser` checks `UseCaching` when choosing `CachingParser` versus `ProgramParser`, and `DafnyLangSymbolResolver` checks the same option when choosing `CachingResolver` versus `ProgramResolver`. Consequently `UseCaching=false` disables **both** caches; the manuscript sentence claiming the parser cache remains active in the fresh-semantic mode is incorrect. A resolver-only fresh oracle needs a separate switch.
