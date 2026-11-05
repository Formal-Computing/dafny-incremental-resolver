// Research countermodels for incomplete resolver keys and mutable cached graphs.
// These are constructive proofs about the modeled hazards, not claims that an
// actual stale binding has been observed in the pinned Dafny implementation.

datatype Context = Context(
  tokenText: int,
  sourcePosition: int,
  dependencyHashes: seq<int>,
  moduleRoster: seq<int>,
  builtinsHash: int,
  compilerOptions: int,
  rewriterEnvironment: int,
  failedLookups: seq<int>)

// The experimentally supported components are reduced to exact structural
// values, to remove SHA-256 collision assumptions from these countermodels.
function ContentKey(c: Context): (int,int,seq<int>,seq<int>,int) {
  (c.tokenText,c.sourcePosition,c.dependencyHashes,c.moduleRoster,c.builtinsHash)
}

// Negative-lookup visibility, compiler options and pre-resolve rewriters
// can affect resolution but are not certified inputs of ContentKey.
function CompleteSemanticObservation(c: Context): (int,int,seq<int>) {
  (c.compilerOptions,c.rewriterEnvironment,c.failedLookups)
}

lemma OptionsCannotBeCertifiedByContentKey()
{
  var a := Context(8,22,[3],[9],5,0,0,[]);
  var b := Context(8,22,[3],[9],5,1,0,[]);
  assert ContentKey(a) == ContentKey(b);
  assert CompleteSemanticObservation(a) != CompleteSemanticObservation(b);
}

lemma RewritersCannotBeCertifiedByContentKey()
{
  var a := Context(8,22,[3],[9],5,0,0,[]);
  var b := Context(8,22,[3],[9],5,0,1,[]);
  assert ContentKey(a) == ContentKey(b);
  assert CompleteSemanticObservation(a) != CompleteSemanticObservation(b);
}

lemma FailedLookupsCannotBeCertifiedByContentKey()
{
  var a := Context(8,22,[3],[9],5,0,0,[]);
  var b := Context(8,22,[3],[9],5,0,0,[10]);
  assert ContentKey(a) == ContentKey(b);
  assert CompleteSemanticObservation(a) != CompleteSemanticObservation(b);
}

// Model heap references (C# object identities) separately from semantic
// values. The same address may be retained after downstream mutation.
datatype RefCache = RefCache(key: int, heapAddress: int)
function ReadCached(c: RefCache, heap: map<int,int>): int
  requires c.heapAddress in heap
{
  heap[c.heapAddress]
}

lemma MutatingAliasedResultChangesCachedObservation()
{
  var alias := RefCache(1,7);
  var oldHeap := map[7 := 42];
  var newHeap := oldHeap[7 := 99];
  assert alias.key == alias.key;
  assert ReadCached(alias,oldHeap) == 42;
  assert ReadCached(alias,newHeap) == 99;
}

// A value snapshot does not refer back to the caller's mutable heap.
datatype ValueCache = ValueCache(key: int, snapshot: int)
function ReadSnapshot(c: ValueCache): int { c.snapshot }

lemma ImmutableSnapshotUnaffectedByCallerMutation(
    snapshot: ValueCache, heap: map<int,int>, address: int, newValue: int)
  ensures ReadSnapshot(snapshot) == snapshot.snapshot
  ensures ReadSnapshot(snapshot) == ReadSnapshot(snapshot)
{
  var changedHeap := heap[address := newValue];
  assert ReadSnapshot(snapshot) == snapshot.snapshot;
}

// Proof of a restricted revalidation policy: if actual uses a fresh result
// on every would-be cache hit, it is observationally equal to fresh by
// construction (and cannot be interpreted as an optimized cache speedup).
function PureResolve(c: Context): (int,int,seq<int>) {
  CompleteSemanticObservation(c)
}
function ShadowValidation(c: Context, cached: (int,int,seq<int>)):
  (int,int,seq<int>) { PureResolve(c) }
lemma ShadowReturningFreshNeverUsesStaleResult(c: Context, stale: (int,int,seq<int>))
  ensures ShadowValidation(c,stale) == PureResolve(c)
{
}
