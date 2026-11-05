// A small, mechanically verified cache contract, not a verification of Dafny's LSP.
// The key models a COMPLETE semantic context. Its equality is structural, not SHA-256.
// All resolved observations are immutable, and PureResolve is deterministic.
// Therefore the theorem intentionally does NOT claim real Dafny's key is complete,
// that mutable ModuleResolutionResult is safe to reattach, or that hash collisions cannot occur.

datatype SemanticKey = SemanticKey(
  moduleId: int,
  localContent: int,
  sourceOrigins: int,
  environment: int,
  dependencyFingerprints: seq<int>,
  namesInScope: seq<int>,
  moduleRoster: seq<int>,
  pluginAndRewriterState: int)

datatype Observation = Observation(
  diagnosticCodes: seq<int>,
  symbolBindings: seq<int>,
  verifierInputs: seq<int>)

// An arbitrary pure resolver represented as an opaque function.
// The cache proof does NOT unfold or depend on this particular example body.
function {:opaque} PureResolve(k: SemanticKey): Observation {
  Observation([k.localContent, k.sourceOrigins],
              k.dependencyFingerprints + k.namesInScope,
              [k.environment, k.pluginAndRewriterState])
}

predicate ValidCache(cache: map<SemanticKey, Observation>) {
  forall k: SemanticKey :: k in cache ==> cache[k] == PureResolve(k)
}

lemma ExtendValidCache(cache: map<SemanticKey, Observation>,
                       k: SemanticKey, v: Observation)
  requires ValidCache(cache)
  requires v == PureResolve(k)
  ensures ValidCache(cache[k := v])
{
  forall other: SemanticKey | other in cache[k := v]
    ensures cache[k := v][other] == PureResolve(other)
  {
    if other != k {
      assert other in cache;
    }
  }
}

// One revision of an incremental resolver. The cache may be warm from ANY
// previous set of revisions provided that the invariant ValidCache holds.
method ResolveIncrementally(keys: seq<SemanticKey>,
                            previous: map<SemanticKey, Observation>)
  returns (observed: seq<Observation>,
           next: map<SemanticKey, Observation>)
  requires ValidCache(previous)
  ensures |observed| == |keys|
  ensures forall i: int :: 0 <= i < |keys| ==> observed[i] == PureResolve(keys[i])
  ensures ValidCache(next)
{
  observed := [];
  next := previous;
  var i := 0;
  while i < |keys|
    invariant 0 <= i <= |keys|
    invariant |observed| == i
    invariant forall j: int :: 0 <= j < i ==> observed[j] == PureResolve(keys[j])
    invariant ValidCache(next)
  {
    var k := keys[i];
    var value: Observation;
    if k in next {
      value := next[k];
      assert value == PureResolve(k);
    } else {
      value := PureResolve(k);
      ExtendValidCache(next, k, value);
      next := next[k := value];
    }
    assert value == PureResolve(keys[i]);
    observed := observed + [value];
    i := i + 1;
  }
}

// A constructive counterexample to a source-only cache key:
// the source stays unchanged but a formerly absent name becomes available.
function NaiveKey(k: SemanticKey): int { k.localContent }
function LookupObservation(k: SemanticKey): bool { 7 in k.namesInScope }

lemma MissingLookupContextBreaksSourceOnlyCaching()
{
  var a := SemanticKey(1, 42, 0, 0, [], [], [], 0);
  var b := SemanticKey(1, 42, 0, 0, [], [7], [], 0);
  assert NaiveKey(a) == NaiveKey(b);
  assert LookupObservation(a) == false;
  assert LookupObservation(b) == true;
}

// Even with identical semantic results, a larger hash overhead can dominate.
// This disproves any UNCONDITIONAL speedup claim in a simple cost model.
lemma GeneralSpeedupCannotBeGuaranteed()
{
  var resolutionCost := 10;
  var baselineHashCost := 1;
  var experimentalHashCost := 5;
  assert resolutionCost + experimentalHashCost >
         resolutionCost + baselineHashCost;
}

// Explicitly compose two document revisions using the cache left by revision 1.
method ResolveTwoRevisions(first: seq<SemanticKey>,
                           second: seq<SemanticKey>,
                           initially: map<SemanticKey, Observation>)
  returns (secondObservations: seq<Observation>)
  requires ValidCache(initially)
  ensures |secondObservations| == |second|
  ensures forall i: int :: 0 <= i < |second| ==>
                           secondObservations[i] == PureResolve(second[i])
{
  var firstObservations, intermediate := ResolveIncrementally(first, initially);
  var finalCache: map<SemanticKey, Observation>;
  secondObservations, finalCache := ResolveIncrementally(second, intermediate);
}
