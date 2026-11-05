// Restricted, value-only model. Not a proof of Dafny's C# resolver.
// Keys here are exact structural semantic inputs, never truncated hashes.
datatype Symbol = Symbol(name: string, typeName: string)
datatype SemanticKey = SemanticKey(
  localSymbols: seq<Symbol>,
  importedSymbols: seq<Symbol>,
  optionFingerprint: seq<int>,
  pluginFingerprint: seq<int>)
datatype Context = Context(owner: nat, key: SemanticKey)
datatype Summary = Summary(key: SemanticKey, symbols: seq<Symbol>)
datatype Resolved = Resolved(owner: nat, symbols: seq<Symbol>)
datatype Lookup = Missing | Found(summary: Summary)

function ResolveSymbols(k: SemanticKey): seq<Symbol> {
  k.localSymbols + k.importedSymbols
}

function Fresh(c: Context): Resolved {
  Resolved(c.owner, ResolveSymbols(c.key))
}

predicate Valid(cache: seq<Summary>) {
  forall i :: 0 <= i < |cache| ==> cache[i].symbols == ResolveSymbols(cache[i].key)
}

function Find(cache: seq<Summary>, key: SemanticKey): Lookup
  decreases |cache|
{
  if |cache| == 0 then Missing
  else if cache[0].key == key then Found(cache[0])
  else Find(cache[1..], key)
}

lemma FindValid(cache: seq<Summary>, key: SemanticKey)
  requires Valid(cache)
  ensures Find(cache, key).Found? ==> Find(cache, key).summary.symbols == ResolveSymbols(key)
  decreases |cache|
{
  if |cache| > 0 {
    if cache[0].key == key {
      assert cache[0].symbols == ResolveSymbols(cache[0].key);
    } else {
      assert Valid(cache[1..]);
      FindValid(cache[1..], key);
    }
  }
}

function Incremental(c: Context, cache: seq<Summary>): Resolved {
  match Find(cache, c.key)
  case Missing => Fresh(c)
  case Found(s) => Resolved(c.owner, s.symbols)
}

lemma NonemptySummarySound(c: Context, cache: seq<Summary>)
  requires Valid(cache)
  ensures Incremental(c, cache) == Fresh(c)
{
  FindValid(cache, c.key);
  match Find(cache, c.key)
  case Missing =>
  case Found(s) =>
    assert s.symbols == ResolveSymbols(c.key);
}

lemma InsertPreservesValid(cache: seq<Summary>, key: SemanticKey)
  requires Valid(cache)
  ensures Valid(cache + [Summary(key, ResolveSymbols(key))])
{
  forall i | 0 <= i < |cache + [Summary(key, ResolveSymbols(key))]|
    ensures (cache + [Summary(key, ResolveSymbols(key))])[i].symbols ==
      ResolveSymbols((cache + [Summary(key, ResolveSymbols(key))])[i].key)
  {
    if i < |cache| {
      assert (cache + [Summary(key, ResolveSymbols(key))])[i] == cache[i];
    }
  }
}

lemma NonemptyHitWithFreshOwner()
{
  var a := Symbol("a", "int");
  var b := Symbol("b", "bool");
  var k := SemanticKey([a], [b], [1], [2]);
  var previous := Context(10, k);
  var current := Context(11, k);
  var cache := [Summary(k, ResolveSymbols(k))];
  assert Valid(cache);
  assert Find(cache, current.key).Found?;
  assert |Find(cache, current.key).summary.symbols| == 2;
  NonemptySummarySound(current, cache);
  assert Incremental(current, cache) == Resolved(11, [a,b]);
  assert Incremental(current, cache).owner != previous.owner;
}

lemma MissingImportInKeyIsUnsound()
{
  var a := Symbol("a", "int");
  var b := Symbol("b", "bool");
  var empty := SemanticKey([a], [], [], []);
  var imported := SemanticKey([a], [b], [], []);
  assert empty.localSymbols == imported.localSymbols;
  assert Fresh(Context(1, empty)).symbols != Fresh(Context(2, imported)).symbols;
}
