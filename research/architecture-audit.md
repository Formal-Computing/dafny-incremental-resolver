# Architecture audit — Dafny de36f2ec1f9c530080eff7929ae28229f45da069

Source references below target the exact pinned upstream revision; the experiment source is in `patches/0001-experimental-module-token-hashing.patch`.

## Observed source path

- `Source/DafnyLanguageServer/Language/Symbols/DafnyLangSymbolResolver.cs:34-61`: `resolutionCache` survives document updates, `ResolveSymbols` serializes invocations by `resolverMutex`, and `UseCaching` selects `CachingResolver` or the uncached `ProgramResolver`.
- `Source/DafnyLanguageServer/Language/CachingParser.cs:32-55`: parse results are keyed by URI and source hash. ASTs are cloned on return because parsed module structures are mutable. The parse cache and module-resolution cache are distinct.
- `Source/DafnyCore/Resolver/ProgramResolver.cs:29-84`: reset type scopes, process prefix modules, construct module bindings/dependency graph, check cycles, topologically resolve, run rewriters and recompose resolved results. A cache HIT still performs graph construction, rewrite framework setup and result composition.
- `Source/DafnyCore/Resolver/ProgramResolver.cs:91-106`: returned `ModuleResolutionResult` installs resolved declarations, module signatures, member mappings and cached reporter messages into the current program.
- `Source/DafnyCore/Resolver/ProgramResolver.cs:111-134,243-326`: module graph includes explicit dependency binding for imports/refinement and cycle handling. Its completeness for implicit/failed lookups, exported views and plugins is *not* established.
- `Source/DafnyCore/Resolver/ModuleResolver.cs:19-24,205`: `ModuleResolutionResult` contains a resolved `ModuleDecl`, `BatchErrorReporter`, signatures and member dictionaries. These are not immutable semantic summaries.
- `Source/DafnyLanguageServer/Language/CachingResolver.cs:15-18,59-99`: a persistent module cache stores `ModuleResolutionResult`; `GetHash` hashes successor module hashes (ordered by CloneId), built-in environment hash and module CloneId. On hit `base.ResolveModuleDeclaration` is skipped.
- `Source/DafnyCore/AST/Modules/ModuleDecl.cs:23,40-61`: CloneId is a GUID and cloning carries the same identity. Exhaustive CloneId transitions for all synthetic module types still require audit.

## Branch implementation

In disabled-experiment mode the upstream GetHash body is preserved verbatim. Experimental mode hashes a deterministic module-roster of name/kind, dependency identities plus hashes, built-in state, and covered token text/trivia/URI/absolute positions; unsupported token coverage falls back locally to CloneId. Results carrying diagnostics are not stored under experimental caching. This is a **mitigation**, not a complete soundness guarantee.

## Remaining source-level obligations

Full negative-lookup tracking; name-binding changes across opened imports; resolution-affecting option and plugin state; rewrite side effects; safe aliasing of resolved AST/signatures; correct diagnostic source origins; include/nested/synthetic module behavior; cache lifecycle across project/environment updates. Until these are discharged, do not deploy the optimization as a production-safe replacement.

## Detailed LSP update and cache lifecycle (verified source chain)

1. `Source/DafnyLanguageServer/Handlers/DafnyTextDocumentHandler.cs:93-100` receives `DidChangeTextDocumentParams` and calls `projects.UpdateDocument`.
2. `Source/DafnyLanguageServer/Workspace/ProjectManagerDatabase.cs:54-65` updates the in-memory filesystem then dispatches to the owning `ProjectManager`.
3. `Source/DafnyLanguageServer/Workspace/ProjectManager.cs:130-163` begins a new compilation: increments version, migrates current IDE state, disposes old `Compilation`, creates and starts a new one, throttles state notifications and triggers verification. This is *not* a new language-server instance or newly allocated semantic cache.
4. `Source/DafnyCore/Pipeline/TextDocumentLoader.cs:34-56` parses and then resolves on the large-stack scheduler; parse errors abort semantic resolution in `ResolveInternal`; this is why error-recovery traces must distinguish parse from resolution failures.
5. `Source/DafnyLanguageServer/Language/DafnyLangParser.cs:27-49` chooses `CachingParser` vs `ProgramParser` based on `UseCaching`, and parses root files; `CachingParser.cs:32-55` applies file-level parse caching and defensive cloning.
6. `Source/DafnyLanguageServer/Language/Symbols/DafnyLangSymbolResolver.cs:34-61` serializes semantic resolution behind a mutex and retains the `ResolutionCache` field; its resolver-selection option is used for the no-cache fresh oracle.
7. `Source/DafnyLanguageServer/Caching/PruneIfNotUsedSinceLastPruneCache.cs:39-84` has a per-cache semaphore, marks accessed entries, and prunes entries unused during the last use/prune interval. It does *not* implement semantic-option-aware cache-key invalidation. `CacheExtensions.cs:12-21` wraps profiling and telemetry.
8. `Source/DafnyCore/Pipeline/TextDocumentLoader.cs:62-84` derives verifiable symbols only after successful resolution, illustrating why diagnostic-only equivalence is weaker than verification-scope equivalence.

**Important result-sharing hazard:** the cached `ModuleResolutionResult` is inserted into a new `Program` by `ProgramResolver.ProcessDeclarationResolutionResult`; reattached dictionaries, resolved syntax and reporter messages need a deliberate aliasing and provenance analysis. The current position-sensitive token hash addresses some source-origin shifts but not arbitrary rewriter or plugin mutations.

**Configuration caveat:** `UseCaching=false` disables both the caching parser and caching resolver in the oracle (see `DafnyLangParser.cs:33-35` and `DafnyLangSymbolResolver.cs:51-54`). Therefore the current A/B/C versus fresh comparison is observationally useful but includes a different parse-cache policy. A future oracle could retain parse caching while forcing fresh semantic resolution to isolate the resolver boundary.
