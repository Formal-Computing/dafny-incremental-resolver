# Prior art and novelty boundary

- K. Rustan M. Leino, *Dafny: An Automatic Program Verifier for Functional Correctness*, LPAR 2010, DOI 10.1007/978-3-642-17511-4_20: target verification language, not incremental module-result caching.
- Hammer, Phang, Hicks, Foster, *Adapton: Composable, Demand-Driven Incremental Computation*, PLDI 2014, DOI 10.1145/2594291.2594324: dynamic demand-driven dependency tracking for incremental computation.
- Hammer et al., *Incremental Computation with Names* (Nominal Adapton), OOPSLA 2015, DOI 10.1145/2814270.2814305: formal from-scratch-consistent named incremental computation under its own calculus; cannot transfer theorem to mutable Dafny ASTs without proof.
- Mokhov, Mitchell, Peyton Jones, *Build Systems à la Carte*, ICFP 2018, DOI 10.1145/3236774: task dependency tracking and rebuild semantics, rather than semantic origin-sensitive AST results.
- Salsa (https://docs.rs/salsa/latest/salsa/): tracked memoized queries; future direction for structural Dafny resolver refactoring, not an existing implementation in this repository.
- Acar, Blelloch, Harper, *Adaptive Functional Programming*, TOPLAS 2006: foundational automatic change propagation.

No originality claim is made for content hashing, transitive invalidation or memoization per se. The emerging contribution is a Dafny-specific, source-audited caching boundary, controlled four-mode LSP differential diagnostics, transparent fallback restrictions and reproducible artifacts. A final novelty claim depends on broader soundness testing and performance measurements. See BibTeX in the manuscript archive.

## Direct prior art: Mercaș undergraduate thesis (July 2026)

Ștefan-Alexandru Mercaș, *Incremental Resolution and Interactive Proof Mode Support for Dafny*, UAIC bachelor thesis defense presentation, supervised by Ștefan Ciobâcă. [Primary source](https://profs.info.uaic.ro/stefan.ciobaca/bsc-theses/bsc-defense-stefan-mercas.pdf).

The thesis already studies incremental resolution with reuse subject to dependency reuse and moves DIPS proof obligations into generated modules to localize invalidation. It identifies finer per-module incremental resolution as future work. Our experimental patch targets existing Language Server CachingResolver module keys and position-sensitive diagnostic observables. This is a narrower engineering and validation research boundary, not a claim that incremental Dafny resolution was previously absent. Compare implementation code before asserting algorithmic novelty.
