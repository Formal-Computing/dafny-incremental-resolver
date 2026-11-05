# Conditional soundness contract

Define `Resolve(M,E,D,O) -> R`. M is source AST plus exact token URI/ranges; E contains namespace and positive **and failed** symbol lookups; D contains dependent module signatures, identities and visibility; O contains builtins, options, tool and language version, project, plugin, rewriter and mutable global context.

For revisions `P_i`, a correctness condition is
`Obs(Incremental(P_i, S_(i-1))) = Obs(Fresh(P_i))`.
`Obs` includes resolved bindings up to justified identity isomorphism, types and module signatures, import/export visibility, diagnostic code/severity/message/URI/exact range/related locations, failures and verification-relevant consequences.

**Conditional proposition (not a Dafny soundness theorem).** Assume deterministic resolution modulo explicitly enumerated nondeterminism; equal keys imply equivalent *complete* semantic context, including absent-name lookups; cache results are isolated from harmful mutations and stale origins; and pre/post rewriters, cancellation/error recovery and global state have equivalent effects. Then equal keys imply equal observables by extensionality. These premises are not established for complete Dafny.

**Restricted standalone model.** For a finite DAG, complete dependency edges, immutable synthetic resolution values, collision-free fingerprinting and a deterministic resolver, transitive fingerprints support reuse by induction on topological order. The standalone 11 passing checks test particular cases; they are not a formal machine-checked proof and do not prove Dafny soundness.

**Empirical evidence.** CI 41069722625 checked diagnostics only: 54 comparisons across five traces and 18 revisions matched fresh uncached resolution. No binding equivalence theorem, plugin/configuration test coverage or downstream verification equivalence is asserted.
