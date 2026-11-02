// Controlled revalidation refinement: no reused mutable result is ever returned.
// This verifies the strongest *unconditional* guarantee available without
// proving completeness of the candidate key or safe AST graph reattachment.
//
// Model abstractions:
//   * FreshResolve is pure/deterministic for a complete context.
//   * Audit records only value observations, never object references.
//   * Every revision returns FreshResolve(context).
// Actual C# correspondence is separately audited/tested in pinned Dafny CI.

datatype CompleteContext = CompleteContext(
    source: int, importedNames: seq<int>, options: int,
    rewriters: seq<int>, negativeLookups: seq<int>, builtins: int)

datatype SemanticResult = SemanticResult(
    bindings: seq<int>, verificationOutcomes: seq<int>)

// An opaque resolver is arbitrary but pure over the complete context.
function {:opaque} FreshResolve(c: CompleteContext): SemanticResult {
  SemanticResult(c.importedNames + c.negativeLookups,
                 [c.source, c.options, c.builtins])
}

// Deliberately incomplete speculative key. Soundness must NOT depend on it.
function CandidateKey(c: CompleteContext): int { c.source }

// Cached objects carry aliases to a mutable heap.
datatype MutableCandidate = MutableCandidate(address: int, key: int)
function CachedValue(m: MutableCandidate, heap: map<int, SemanticResult>): SemanticResult
  requires m.address in heap
{
  heap[m.address]
}

// Immutable audit snapshots hold VALUES only. The sequence models a bounded
// history of primitive observation digests (not ModuleResolutionResult graphs).
datatype AuditEntry = AuditEntry(key: int, observation: SemanticResult)

method ControlledRevalidate(c: CompleteContext, heap: map<int, SemanticResult>,
                            candidate: MutableCandidate,
                            audit: seq<AuditEntry>)
    returns (result: SemanticResult, auditAfter: seq<AuditEntry>)
    ensures result == FreshResolve(c)
    ensures |auditAfter| <= 32
    ensures forall i: int :: 0 <= i < |auditAfter| ==>
      auditAfter[i].observation == FreshResolve(c) ||
      (exists j: int :: 0 <= j < |audit| &&
          auditAfter[i] == audit[j])
{
  // CandidateKey and heap intentionally NEVER influence returned semantics.
  result := FreshResolve(c);
  var entry := AuditEntry(CandidateKey(c), result);
  if |audit| >= 32 {
    auditAfter := [entry];
  } else {
    auditAfter := audit + [entry];
  }
}

// Universal equivalence to fresh resolution, regardless of any cached heap,
// faulty candidate key or stale object content.
method SafeModeRefinesFresh(c: CompleteContext, previous: SemanticResult,
                          candidate: MutableCandidate,
                          heapBefore: map<int, SemanticResult>,
                          heapAfter: map<int, SemanticResult>)
  ensures FreshResolve(c) == FreshResolve(c)
{
  var result1, log1 := ControlledRevalidate(c, heapBefore, candidate, []);
  var result2, log2 := ControlledRevalidate(c, heapAfter, candidate, []);
  assert result1 == FreshResolve(c);
  assert result2 == FreshResolve(c);
  assert result1 == result2;
}

method RevalidateTrace(contexts: seq<CompleteContext>,
                       mutableHeap: map<int, SemanticResult>,
                       stale: MutableCandidate)
    returns (observed: seq<SemanticResult>)
    ensures |observed| == |contexts|
    ensures forall i: int :: 0 <= i < |contexts| ==>
      observed[i] == FreshResolve(contexts[i])
{
  observed := [];
  var audit: seq<AuditEntry> := [];
  var index := 0;
  while index < |contexts|
    invariant 0 <= index <= |contexts|
    invariant |observed| == index
    invariant forall j: int :: 0 <= j < index ==>
      observed[j] == FreshResolve(contexts[j])
    invariant |audit| <= 32
  {
    var result, next := ControlledRevalidate(contexts[index], mutableHeap, stale, audit);
    assert result == FreshResolve(contexts[index]);
    observed := observed + [result];
    audit := next;
    index := index + 1;
  }
}

// Explicit witness: same candidate key, different complete contexts.
// Returning the cached result would be unsound; revalidation is not.
method IncompleteKeyCannotLicenseMutableReuse() {
  var a := CompleteContext(42, [1], 0, [], [], 7);
  var b := CompleteContext(42, [2], 1, [3], [99], 7);
  assert CandidateKey(a) == CandidateKey(b);
  assert a != b;
  reveal FreshResolve();
  assert FreshResolve(a) != FreshResolve(b);
  var oldValue := FreshResolve(a);
  var candidate := MutableCandidate(4, CandidateKey(a));
  var heap := map[4 := oldValue];
  var result, audit := ControlledRevalidate(b, heap, candidate, []);
  assert result == FreshResolve(b);
  assert result != heap[4];
}

// No conditional speedup is claimed: the "hit" computes FreshResolve.
// A future optimizing refinement must prove a complete context key AND
// reattachment safety before removing the fresh-resolution branch.

// A specification for future OPTIMIZING caching. This is NOT the current C#
// hash: all semantic inputs must be represented, and equality is structural.
datatype FullContextKey = FullContextKey(
  source: int, importedNames: seq<int>, options: int,
  rewriters: seq<int>, negativeLookups: seq<int>, builtins: int)

function CompleteKeySpec(c: CompleteContext): FullContextKey {
  FullContextKey(c.source, c.importedNames, c.options,
                 c.rewriters, c.negativeLookups, c.builtins)
}

// Formal refinement obligation: a *genuinely complete*, injective
// structural key licenses equivalence of any deterministic fresh resolver.
// This theorem MUST NOT be applied to CandidateKey or real SHA-256 until
// the mapping from all Dafny resolver inputs to this specification is proved.
lemma CompleteKeyEqualityImpliesFreshEquivalence(a: CompleteContext,
                                                   b: CompleteContext)
  requires CompleteKeySpec(a) == CompleteKeySpec(b)
  ensures a == b
  ensures FreshResolve(a) == FreshResolve(b)
{
  assert a.source == b.source;
  assert a.importedNames == b.importedNames;
  assert a.options == b.options;
  assert a.rewriters == b.rewriters;
  assert a.negativeLookups == b.negativeLookups;
  assert a.builtins == b.builtins;
}
