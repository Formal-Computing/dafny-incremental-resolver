# Architecture and safety review

## 1. Existing upstream design

`DafnyLangSymbolResolver` selects either `CachingResolver` or `ProgramResolver`. The persistent `ResolutionCache` stores resolved `ModuleResolutionResult` objects. `CachingResolver` overrides `ResolveModuleDeclaration(...)`, computes a cache key for the requested module, returns an existing result on a hit, or invokes the base resolver on a miss. `ProgramResolver` builds the module-dependency graph and recomposes the full program from individual `ModuleResolutionResult` values.

`CachingParser` separately caches parse results by URI/content and clones ASTs because they are mutable. The resolver is also stateful, with type scopes, diagnostic objects, module signatures and rewriter hooks. Therefore a cached semantic result cannot simply be substituted based on text alone without a conservative validity argument.

### Current cache key

SHA-256 of: recursively hashed successor modules (sorted using `CloneId`), system module hash, and module `CloneId`. `CloneId` remains unchanged for a file that has not changed. This can cause avoidable invalidation of unrelated modules when two modules share an edited source file.

### Experimental cache key

SHA-256 of: recursively hashed module dependencies (sorted by dependency *hash*, not `CloneId`), system-module hash, and the module's source-token fingerprint. The fingerprint includes module identity/type, token text, source URI, token positions, and leading/trailing trivia. Multi-file and synthetic/uncertain AST regions conservatively retain `CloneId`.

This is intentionally **position sensitive** to avoid returning diagnostics with old line/column offsets. Edits that shift later modules will therefore still invalidate them. This is a safety-related constraint, not a performance bug.

## 2. Current implementation boundary

The core project's `RevisionPlanner` and `IncrementalCache<T>` are pure algorithmic models. They test topological evaluation, transitive fingerprinting, conservative invalidation and cache-hit/miss behavior. Inputs are `ModuleSnapshot` objects, not parsed Dafny source.

The patch in `patches/` modifies the real upstream `CachingResolver` but has not been compiled in the full Dafny repository. It must be treated as integration work in progress. No measured speedups are claimed.

## 3. Correctness hazards for review

1. **Negative name dependencies:** a new declaration elsewhere may change name lookup in an unchanged module without a visible import edge.
2. **Rewriters/visibility:** a plugin or exported view may alter semantic context not represented in the module graph hash.
3. **Mutable ASTs:** a cached `ModuleResolutionResult` may reference AST nodes and signatures from a previous parse.
4. **Diagnostics:** old source locations, warnings or error messages can be stale even when lexical tokens are unchanged.
5. **Options/versions:** resolver options, language version and library state must participate in cache validity.
6. **Cross-file syntax:** prefix modules, includes and synthetic modules must be handled conservatively.
7. **Non-semantic edits:** whitespace/comment changes currently invalidate, because trivia and positions are included to preserve diagnostic fidelity.
8. **Error recovery:** an invalid old or new program can change resolution behavior in ways not captured by normal dependency edges.

**Approval gate:** Until differential tests cover these, keep `DAFNY_EXPERIMENTAL_CONTENT_HASH` disabled in ordinary use.

## 4. Experiments for the professor/colleague review

1. Two independent modules in one file, same-length edit to one module; compare baseline/experimental cache logs and full diagnostics.
2. Insert a line before an unchanged module; prove that the position-sensitive hash invalidates it.
3. Change an exported function signature used by another module; verify transitive invalidation.
4. Rename or delete a symbol and confirm that both modes report the correct resolver diagnostic.
5. Add a colliding declaration in a shared scope; check for stale lookup (especially missing/negative dependencies).
6. Change an import, export set, refinement or opened module; verify cache invalidation.
7. Change Dafny options during a persistent session, ensuring cache correctness.
8. Run the unchanged version twice with a persistent server to measure control-case cache hits.

**Measurement:** report number of module hits/misses and median resolution latency across repeated edit sequences; record Dafny commit, SDK version, warmup policy, module size and how tests drove the persistent language server. Count correctness mismatches before claiming performance.

## 5. Future declaration-level resolver

A distinct follow-up would cache resolution below module granularity: `TopLevelDecl`, `MemberDecl`, type constraints, module visibility contexts, resolution ordering, implicit dependencies and symbol-table snapshots. Defining a reusable boundary will likely require refactoring `ModuleResolver` to expose isolated, context-aware result objects rather than holding on to mutable resolved nodes. This is the more substantial research problem.
