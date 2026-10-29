# Research brief for the October 30 discussion

**Working title:** Toward Content-Aware Incremental Semantic Resolution in Dafny

**Team:** Dragoș-Andrei Bobu; Ștefan-Alexandru Mercaș  
**Supervisor:** Prof. Ștefan Ciobâcă

## Abstract (work-in-progress)

Interactive formal verification repeatedly analyzes successive versions of programs that often differ only locally. Dafny already implements module-level resolution caching, but its current cache keys use clone identifiers as conservative proxies for module contents. This project investigates the feasibility of more precise cache invalidation using syntax-derived fingerprints and dependency-aware analysis. We implement a small C# reference model for comparing successive module snapshots and propagating invalidation, together with an opt-in experimental modification to Dafny's language-server resolver cache. The evaluation will assess whether the modified cache retains correct resolution results and diagnostics while reducing unnecessary module resolution after edits. The work distinguishes established module-level caching from the longer-term problem of declaration-level incremental name resolution and type inference.

## Research question

Can module-local structural fingerprints and dependency-aware cache keys reduce the frequency of unnecessary resolution in Dafny's language server without compromising semantic correctness or diagnostic validity?

## Current contributions

- Source-grounded analysis of Dafny's parser/resolver caching architecture.
- A deterministic C# model of revision classification and transitive invalidation.
- Cache-key generation based on transitive dependency fingerprints and environment version.
- An experimental, opt-in upstream patch replacing `CloneId` as a module-content proxy where safe to attempt.
- Reproducible smoke checks and a safety-focused experimental protocol.

## Expected contributions (not completed)

- Real Dafny language-server tests and performance results.
- A demonstrated cache-validity argument including binding environment and negative dependencies.
- A design for true declaration-level semantic resolution reuse inside modules.

## Reviewer questions

1. Are `CloneId`-derived invalidations a sufficiently meaningful performance issue in real Dafny IDE workloads?
2. Which module resolution contexts are missing from the existing dependency graph hash?
3. What data structure could safely carry resolved declarations between AST versions?
4. Should the first paper target safer module-level optimization or the harder declaration-level architecture?
5. What existing Dafny benchmark suites and editing traces best evaluate this hypothesis?
