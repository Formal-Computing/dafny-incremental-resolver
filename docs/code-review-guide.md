# Code review guide

This repository has two intentionally distinct components: (1) a standalone
model of change detection/dependency-based invalidation, and (2) an opt-in
patch to the existing Dafny language server's module-level resolution cache.

## Suggested reading order (15–20 minutes)

1. `README.md`: research question, boundaries, build and experiment commands.
2. `src/IncrementalResolver.Core/ModuleSnapshot.cs`: description of an input module revision.
3. `src/IncrementalResolver.Core/RevisionPlanner.cs`: transitive dependency closure,
   change classification and work plan across two revisions.
4. `src/IncrementalResolver.Core/IncrementalCache.cs`: reference cache behavior.
5. `tests/IncrementalResolver.SmokeTests/Program.cs`: 11 executable invariants.
6. `patches/0001-experimental-module-token-hashing.patch`: the direct upstream modification.
7. `tests/dafny/SameFileCachingMethod.txt`: Dafny AST/LSP integration experiment.
8. `docs/evaluation-protocol.md`: correctness gates and controlled comparisons.

## Upstream Dafny entry points

- `Source/DafnyLanguageServer/Language/CachingParser.cs`:
  file-grained parse hashing, mutable AST cloning.
- `Source/DafnyLanguageServer/Language/CachingResolver.cs`:
  module-resolution result cache and current `CloneId`-based key.
- `Source/DafnyCore/Resolver/ProgramResolver.cs`:
  module dependency graph construction and composition of cached results.
- `Source/DafnyCore/Resolver/ModuleResolver.cs`:
  underlying semantic resolution of individual modules.
- `Source/DafnyLanguageServer.Test/Synchronization/CachingTest.cs`:
  upstream tests; includes a skipped same-file-module test.

## Questions for reviewers

- Does the transitive module dependency graph capture all relevant changes in
  name lookup, imports, exports, refinements and visibility?
- Can resolved AST nodes, signatures or reporter messages safely be shared
  across reparsed programs when every token position is unchanged?
- Do plugin rewriters and resolver options create implicit dependencies not
  captured by the candidate cache key?
- Is scanning all tokens to avoid resolution work cheaper on representative
  projects than performing full resolution?
- Which resolver phases would need refactoring to support true declaration-
  or member-level incremental resolution?

## Evidence standard

Passing unit and LSP tests supports the specific tested edits only. It is
not a soundness proof. Do not claim a generally correct incremental resolver,
declaration-level reuse, or measured performance improvements from these
tests alone.
