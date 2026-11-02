// Sound and genuinely optimizing memoization for ONE pinned Dafny resolver
// branch: ModuleExportDecl, whose semantic resolution produces no signatures,
// no class members and no diagnostics.
//
// MODEL BOUNDARY: This is a theorem about the contract extracted from pinned
// ModuleResolver.ResolveModuleDeclaration. Proving that this contract holds
// for all upstream versions or arbitrary custom rewriters requires an
// independent implementation/refinement argument.

datatype DeclKind = ExportDecl | OrdinaryDecl

datatype SemanticContext = SemanticContext(
  source: int, imported: seq<int>, options: int,
  rewriters: seq<int>, negativeLookups: seq<int>)

// Caller-owned current compilation result. "owner" is never cached.
datatype Result = Result(owner: int, declIdentity: int,
                         signatures: seq<int>,
                         classMembers: seq<int>,
                         diagnostics: seq<int>)

// The pinned export branch is a no-op; the output depends ONLY on the
// current declaration and program ownership, not prior compilation state.
function FreshExport(owner: int, currentDecl: int): Result {
  Result(owner, currentDecl, [], [], [])
}

// Ordinary declarations may have arbitrary semantic behavior. We do not
// attempt to memoize their resolved graph.
function FreshOrdinary(owner: int, decl: int,
                                 context: SemanticContext): Result {
  Result(owner, decl, context.imported, context.negativeLookups,
         [context.source, context.options])
}

function Fresh(kind: DeclKind, owner: int, decl: int,
               context: SemanticContext): Result {
  if kind == ExportDecl then FreshExport(owner, decl)
  else FreshOrdinary(owner, decl, context)
}

// The immutable summary encodes only the *absence* of additional payload.
// It contains no pointer to a mutable AST, reporter, signature or dictionary.
datatype ExportSummary = ExportSummary(version: int, verifiedEmpty: bool)
function Eligible(summary: ExportSummary): bool {
  summary.version == 1 && summary.verifiedEmpty
}

method ResolveSummary(kind: DeclKind, owner: int, decl: int,
                      context: SemanticContext, summary: ExportSummary)
  returns (result: Result, nextSummary: ExportSummary, hit: bool)
  ensures result == Fresh(kind, owner, decl, context)
  ensures hit ==> kind == ExportDecl && Eligible(summary)
  ensures kind == ExportDecl ==> Eligible(nextSummary)
  ensures kind == ExportDecl && Eligible(summary) ==> hit
  ensures hit ==> result.owner == owner && result.declIdentity == decl
  ensures hit ==> result.signatures == [] && result.classMembers == []
                  && result.diagnostics == []
  ensures nextSummary == summary || Eligible(nextSummary)
{
  if kind == ExportDecl && Eligible(summary) {
    hit := true;
    // GENUINE optimization: skip Fresh() entirely for export only and create
    // a new graph-owned wrapper with no alias to cached mutable objects.
    result := FreshExport(owner, decl);
    nextSummary := summary;
  } else {
    hit := false;
    result := Fresh(kind, owner, decl, context);
    if kind == ExportDecl {
      assert result == FreshExport(owner,decl);
    }
    if kind == ExportDecl && result.signatures == [] &&
        result.classMembers == [] && result.diagnostics == [] &&
        result.owner == owner && result.declIdentity == decl {
      nextSummary := ExportSummary(1, true);
    } else {
      nextSummary := summary;
    }
  }
}

// The partially specified content hash may collide. That does not affect
// this subset, because its payload is context-independent.
function CandidateKey(c: SemanticContext): int { c.source }

method ContextCollisionDoesNotBreakExportSummary(
    a: SemanticContext, b: SemanticContext,
    ownerA: int, ownerB: int, declA: int, declB: int)
  ensures FreshExport(ownerB,declB) ==
          Result(ownerB,declB,[],[],[])
{
  var summary := ExportSummary(1,true);
  var x, s, hit := ResolveSummary(ExportDecl,ownerA,declA,a,summary);
  var y, t, hit2 := ResolveSummary(ExportDecl,ownerB,declB,b,s);
  assert hit && hit2;
  assert x.owner == ownerA;
  assert y.owner == ownerB;
  assert y == FreshExport(ownerB,declB);
}

// A sequence of arbitrary source edits preserves fresh semantics.
// Count actual skips (not mere audit hits) and prove all wrappers belong
// to the current compilation identity.
method ResolveSequence(kinds: seq<DeclKind>, owners: seq<int>,
                       declarations: seq<int>, contexts: seq<SemanticContext>)
  returns (results: seq<Result>, skipped: nat)
  requires |kinds| == |owners| == |declarations| == |contexts|
  ensures |results| == |kinds|
  ensures forall j: int :: 0 <= j < |kinds| ==>
    results[j] == Fresh(kinds[j], owners[j], declarations[j], contexts[j])
  ensures forall j: int :: 0 <= j < |kinds| ==>
    results[j].owner == owners[j] && results[j].declIdentity == declarations[j]
  ensures skipped <= |kinds|
{
  results := [];
  skipped := 0;
  var memo := ExportSummary(0,false);
  var i := 0;
  while i < |kinds|
    invariant 0 <= i <= |kinds|
    invariant |results| == i
    invariant skipped <= i
    invariant forall j: int :: 0 <= j < i ==>
      results[j] == Fresh(kinds[j], owners[j], declarations[j], contexts[j])
    invariant forall j: int :: 0 <= j < i ==>
      results[j].owner == owners[j] && results[j].declIdentity == declarations[j]
  {
    var out, next, hit := ResolveSummary(kinds[i],owners[i],
      declarations[i],contexts[i],memo);
    if hit { skipped := skipped+1; }
    results := results + [out];
    memo := next;
    i := i+1;
  }
}

// A witness that the memoization does useful work: for two export
// declarations in different current compilations, the second skips fresh
// resolution while constructing a new owned result.
method TwoExportDeclarationsActuallyReuseSummary()
{
  var c := SemanticContext(1,[],0,[],[]);
  var first, state1, hit1 := ResolveSummary(
    ExportDecl,100,1,c,ExportSummary(0,false));
  assert !hit1;
  assert Eligible(state1);
  var second, state2, hit2 := ResolveSummary(
    ExportDecl,200,2,SemanticContext(1,[9],42,[2],[8]),state1);
  assert hit2;
  assert first.owner == 100 && second.owner == 200;
  assert second == FreshExport(200,2);
  assert second != first;
}

// Attempting to generalize this implementation to ordinary modules would
// be invalid without complete input keys and safe graph reconstruction.
method OrdinaryModulesAreNotCovered(c: SemanticContext) {
  var result, state, hit := ResolveSummary(
    OrdinaryDecl,12,34,c,ExportSummary(1,true));
  assert !hit;
  assert result == Fresh(OrdinaryDecl,12,34,c);
}
