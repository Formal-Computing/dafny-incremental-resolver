# Negative control: forced collision in the immutable nonempty audit

**Status:** research-only regression, not a proposed cache optimization.

## Purpose

Prior work records nonempty names from the actual Dafny resolver but does not
establish that its candidate key contains every semantic dependency. This
negative control tests whether our audit correctly **detects** a known key
collision between different semantic observations, without allowing reuse.

## Mechanism

Patch `0007-audit-only-key-collision-negative-control.patch` adds the explicit
test-only environment variable `DAFNY_RESEARCH_AUDIT_COLLISION_PROBE=1`.
It maps all nonempty **audit dictionary buckets** to the same diagnostic
key `RESEARCH_AUDIT_COLLISION_PROBE_V1`.

Only `cache.ResearchNonemptySymbolAudits` uses that diagnostic key.
The actual module resolver's `GetHash` value is unmodified, and the separate
`ResearchAuditFingerprints` dictionary continues using the original key.
Every non-export module in `DAFNY_RESEARCH_SAFE_REVALIDATE=1` still follows
`base.ResolveModuleDeclaration`, with no reuse of mutable resolution graphs.

## Real-language-server witness

`CachingTest.ResearchNonemptyAuditDetectsForcedCollisionWithoutReuse`
opens one Dafny document containing two distinct nonempty modules
(`ResearchCollisionFirst` and `ResearchCollisionSecond`), each with
distinct datatype and function declarations. It requires:

- an audit `MISS` for the initial observation;
- at least one `DIFFERENT` observation associated with a research module
  when the same deliberately forced bucket receives a distinct result;
- no export-only summary event for those nonempty modules.

The test intentionally does not treat a `MATCH` as soundness evidence.

## Limits

A successful adversarial probe demonstrates that the *selected* immutable
symbol-name observation can detect *this* known collision. The observation is
not complete, and real key soundness, mutable graph reconstruction and nonempty
resolver-skipping remain unproven. No option, plugin or negative-lookup
completeness can be inferred.

## Reproduction

The `immutable-export-summary.yml` pinned Dafny CI workflow now applies
patches `0001`–`0007`, builds the real Dafny language server, and runs the
collision test in a distinct testhost process with both research environment
variables. Existing fresh-versus-export semantic and terminal verifier
comparisons still run independently.
