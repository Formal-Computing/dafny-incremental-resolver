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
