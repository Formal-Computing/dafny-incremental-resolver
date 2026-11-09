# Semantic dependency registry

`semantic-dependency-registry.json` records the resolver inputs that a reusable result may depend on, with pinned C# anchors, key obligations, fail-closed rules, counterexamples, and evidence labels. The inventory is deliberately incomplete. “Measured” denotes finite selected tests/audit evidence, not proof of a complete key. “Abstract” denotes properties of formal models only; “unverified” denotes a source/refinement obligation without adequate behavioral evidence.

The operational rule is simple: if any dependency is missing, unknown, changed, or cannot be fingerprinted reliably, discard the candidate and run fresh resolution. In particular, a complete key is an obligation, not an established property. This registry makes no claim that the current cache key satisfies it and does not justify changing caching implementation.

Validate with `python scripts/validate_semantic_dependency_registry.py` and `python -m unittest tests/test_semantic_dependency_registry.py`.
