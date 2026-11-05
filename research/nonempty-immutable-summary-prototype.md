# Nonempty immutable summary: scoped refinement prototype

This is a research extension of PR #11, not a replacement for the real Dafny resolver.
The upstream pinned Dafny core has a no-op `ModuleExportDecl` branch, whereas
`LiteralModuleDecl`, `AliasModuleDecl` and abstract module branches perform
actual semantic work. It would be incorrect to skip any of them merely because
the current experimental SHA-256 fingerprint matches.

## Results

- `tests/formal/NonemptyImmutableSummaryRefinement.dfy` is a machine-checked
  **abstract** model of an immutable nonempty symbol summary.
- `tests/reference/NonemptySummaryReference` is a small independent .NET 8
  executable reference implementation. Its summary contains immutable symbols,
  and each lookup allocates a fresh mutable dictionary bound to the current owner.
- The key explicitly encodes locals, imports, options and plugins with
  length-delimited component boundaries; this is a collision-free encoding of
  the model's finite strings, not a hash of Dafny ASTs.
- The reference test exercises a first miss, a second hit, independent dictionary
  ownership, four dependency invalidations and a deliberately incomplete key.

## Proof contract

For a pure deterministic resolver `R`, a cache entry `(K, R(K))` and a
structural key `K` containing ALL relevant semantic inputs, reconstructing
`(currentOwner, cachedSymbols)` is observationally equivalent to a fresh
`(currentOwner, R(K))`. Valid-cache insertion preserves the invariant.

This proves the scoped **model**, not a refinement of the real C# resolver.
The model uses a simple concatenation of local and imported symbols. Actual
Dafny name resolution depends on scopes, declarations, plugins, visibility,
rewriters, options, token origins, negative lookups and other mutable state.

## Status and nonclaims

The present branch does NOT enable nonempty cross-revision caching in Dafny.
All real modules outside PR #11's restricted export no-op branch must continue
through fresh resolution. We have NOT proven that the production
`ModuleResolutionResult` graph can be reconstructed from a nonempty value-only
summary, nor that the real implementation's keys capture all semantic inputs.

The next C# integration milestone requires mapping a *specific* nonempty
module kind to a fully audited serialization/reconstruction contract, with
differential LSP + terminal verifier oracle, real HIT/MISS instrumentation,
negative dependency controls, mutable-graph isolation and a source-pinned audit.
Until then, fail closed.

## Reproduction

```text
dafny verify tests/formal/NonemptyImmutableSummaryRefinement.dfy
dotnet run --project tests/reference/NonemptySummaryReference/NonemptySummaryReference.csproj -c Release
```
