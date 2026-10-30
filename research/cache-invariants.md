# Cache invariants and failure policy

1. The standard nonexperimental upstream hashing implementation must remain unchanged. Test with original, patched baseline, experimental, fresh modes.
2. Source-origin URI, line, column and absolute offset remain in the experimental local identity; do not reuse old diagnostics after shifting source origins.
3. Dependency fingerprints include deterministic named edges to distinguish equal-hash but differently bound modules; a global module name/kind roster is hashed to reduce silent add/remove/rename errors.
4. If a module's token coverage is unsafe (multi-file/synthetic), retain upstream CloneId locally.
5. Error-bearing resolved results are never added to the experimental semantic cache; invalid revisions must not seed reusable reporter state.
6. A cache hit is only a candidate: mutable resolved AST and signatures, implicit lookup context, rewriters and compiler options remain unresolved soundness obligations.
7. Future production policy: any unknown, untracked or changed semantic context should trigger fresh resolution rather than assuming equal content is sufficient.
8. Never confuse the immutable `IncrementalCache<T>` synthetic model with persistent Dafny `ModuleResolutionResult` reuse.

Oracle coverage: code, severity, message, source field, start/end ranges, selected related diagnostic locations. Not yet: complete bindings, types, verifier results, strict source URI for diagnostic envelope, mutable graph isolation, fault injection.
