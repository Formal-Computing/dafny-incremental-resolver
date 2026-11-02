// Implementation-oriented refinement contract for the pinned Dafny cache patch.
// "Baseline" is Dafny's unchanged CloneId-based cache-key computation, modeled
// extensionally. This file proves relative cache-DECISION parity for the guarded
// branch; it cannot prove upstream baseline correctness or real AST reuse safety.

datatype ResolverContext = ResolverContext(
  cloneId: int,
  moduleKind: int,
  text: int,
  origin: int,
  dependencyHashes: seq<int>,
  builtins: int,
  moduleRoster: seq<int>,
  failedLookups: seq<int>,
  options: int,
  plugins: int,
  tokensComplete: bool)

// Structural model; SHA-256 byte arrays and collisions are not formalized.
function UpstreamKey(s: ResolverContext): seq<int> {
  [s.cloneId, s.builtins] + s.dependencyHashes
}

function ResearchKey(s: ResolverContext): seq<int> {
  [2026, s.moduleKind, s.text, s.origin, s.builtins]
  + s.moduleRoster + s.dependencyHashes
}

// This is the actual two-flag policy added to CachingResolver.GetHash:
// if not explicitly enabled, or lacking complete token coverage, use upstream.
function SelectedKey(s: ResolverContext, experimental: bool, unsafeOptIn: bool): seq<int> {
  if experimental && unsafeOptIn && s.tokensComplete then
    ResearchKey(s)
  else
    UpstreamKey(s)
}

lemma DefaultRefinesUpstream(s: ResolverContext, experimental: bool, unsafeOptIn: bool)
  requires !experimental || !unsafeOptIn
  ensures SelectedKey(s, experimental, unsafeOptIn) == UpstreamKey(s)
{
}

lemma UnsupportedModuleRefinesUpstream(s: ResolverContext)
  requires !s.tokensComplete
  ensures SelectedKey(s, true, true) == UpstreamKey(s)
{
}

// For all prior/new states in guarded mode, a hit is made exactly when
// upstream would choose the same key. No extra reuse is introduced.
lemma GuardedReuseDecisionsMatchUpstream(prior: ResolverContext, now: ResolverContext,
                                         experimental: bool, unsafeOptIn: bool)
  requires !experimental || !unsafeOptIn
  ensures (SelectedKey(prior, experimental, unsafeOptIn) ==
           SelectedKey(now, experimental, unsafeOptIn)) ==
          (UpstreamKey(prior) == UpstreamKey(now))
{
  DefaultRefinesUpstream(prior, experimental, unsafeOptIn);
  DefaultRefinesUpstream(now, experimental, unsafeOptIn);
}

lemma UnsupportedModuleReuseDecisionsMatchUpstream(prior: ResolverContext,
                                                    now: ResolverContext)
  requires !prior.tokensComplete && !now.tokensComplete
  ensures (SelectedKey(prior, true, true) == SelectedKey(now, true, true)) ==
          (UpstreamKey(prior) == UpstreamKey(now))
{
  UnsupportedModuleRefinesUpstream(prior);
  UnsupportedModuleRefinesUpstream(now);
}

// A *counterexample* to semantic soundness of the content-aware research key:
// the key misses the negative-lookup context. Same content, origins, dependencies
// and builtins can coexist with different previously failed lookups.
function FullSemanticContext(s: ResolverContext): seq<int> {
  [s.cloneId, s.text, s.origin, s.builtins, s.options, s.plugins]
  + s.dependencyHashes + s.failedLookups
}

lemma UnsafeResearchKeyIsNotComplete()
{
  var original := ResolverContext(91, 1, 42, 0, [10], 7, [1], [], 0, 0, true);
  var altered  := ResolverContext(92, 1, 42, 0, [10], 7, [1], [88], 0, 0, true);
  assert ResearchKey(original) == ResearchKey(altered);
  assert FullSemanticContext(original) != FullSemanticContext(altered);
}

// Consequently, a production gate may not label a content-aware key as
// "certified" merely because token coverage is complete.
lemma TokenCoverageDoesNotCertifySemanticCompleteness()
{
  var a := ResolverContext(91, 1, 42, 0, [10], 7, [1], [], 0, 0, true);
  var b := ResolverContext(92, 1, 42, 0, [10], 7, [1], [88], 0, 0, true);
  assert a.tokensComplete && b.tokensComplete;
  assert SelectedKey(a, true, true) == SelectedKey(b, true, true);
  assert FullSemanticContext(a) != FullSemanticContext(b);
}

// The real implementation must calculate fallback hashes recursively through
// GetUpstreamHash rather than invoking the potentially experimental GetHash.
// This models the dependency-mixing bug identified during source review.
function UpstreamDependentKey(parent: ResolverContext, provider: ResolverContext): seq<int> {
  [parent.cloneId, parent.builtins] + UpstreamKey(provider)
}

function SelectedDependentKey(parent: ResolverContext, provider: ResolverContext,
                              experimental: bool, unsafeOptIn: bool): seq<int> {
  if experimental && unsafeOptIn && parent.tokensComplete then
    ResearchKey(parent) + SelectedKey(provider, experimental, unsafeOptIn)
  else
    UpstreamDependentKey(parent, provider)
}

lemma UnsupportedParentUsesPureUpstreamChain(parent: ResolverContext,
                                               provider: ResolverContext)
  requires !parent.tokensComplete
  ensures SelectedDependentKey(parent, provider, true, true)
          == UpstreamDependentKey(parent, provider)
{
}

lemma GuardedParentUsesPureUpstreamChain(parent: ResolverContext,
                                          provider: ResolverContext,
                                          experimental: bool, unsafeOptIn: bool)
  requires !experimental || !unsafeOptIn
  ensures SelectedDependentKey(parent, provider, experimental, unsafeOptIn)
          == UpstreamDependentKey(parent, provider)
{
}
