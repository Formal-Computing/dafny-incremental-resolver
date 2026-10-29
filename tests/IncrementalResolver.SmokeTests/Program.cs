using IncrementalResolver.Core;

static void Assert(bool predicate, string description) {
  if (!predicate) throw new Exception($"FAIL: {description}");
  Console.WriteLine($"PASS: {description}");
}

static int Resolve(ModuleSnapshot module, IReadOnlyDictionary<string, int> dependencies) =>
  module.SourceFingerprint.Length + dependencies.Values.Sum();

var first = new[] {
  ModuleSnapshot.Create("A", "initial-A"),
  ModuleSnapshot.Create("B", "initial-B", "A"),
  ModuleSnapshot.Create("C", "initial-C")
};
var changed = new[] {
  ModuleSnapshot.Create("A", "revised-A"),
  ModuleSnapshot.Create("B", "initial-B", "A"),
  ModuleSnapshot.Create("C", "initial-C")
};
var planner = RevisionPlanner.Analyze(first, changed);
Assert(planner.DirectlyModified.SequenceEqual(["A"]), "modification of A detected");
Assert(planner.TransitivelyInvalidated.SequenceEqual(["B"]), "dependent B invalidated");
Assert(planner.Reusable.SequenceEqual(["C"]), "independent C reusable");

var cache = new IncrementalCache<int>();
var cold = cache.Resolve(first, "options-v1", Resolve);
Assert(cold.Misses.Length == 3 && cold.Hits.Length == 0, "cold run resolves all modules");
var warm = cache.Resolve(first, "options-v1", Resolve);
Assert(warm.Hits.Length == 3 && warm.Misses.Length == 0, "unchanged run reuses all modules");
var edited = cache.Resolve(changed, "options-v1", Resolve);
Assert(edited.Misses.SequenceEqual(["A", "B"]) && edited.Hits.SequenceEqual(["C"]),
  "edit recomputes A and B but reuses C");
var changedOptions = cache.Resolve(changed, "options-v2", Resolve);
Assert(changedOptions.Misses.Length == 3, "resolver option changes invalidate all entries");

var deleted = new[] { ModuleSnapshot.Create("B", "initial-B"), ModuleSnapshot.Create("C", "initial-C") };
var deletionPlan = RevisionPlanner.Analyze(changed, deleted);
Assert(deletionPlan.Removed.SequenceEqual(["A"]), "deleted module detected");
Assert(deletionPlan.DirectlyModified.SequenceEqual(["B"]), "deleted import changes B dependencies");

var cyclic = new[] { ModuleSnapshot.Create("A", "a", "B"), ModuleSnapshot.Create("B", "b", "A") };
try {
  cache.Resolve(cyclic, "options-v1", Resolve);
  throw new Exception("FAIL: cycle must be rejected");
} catch (InvalidOperationException ex) when (ex.Message.Contains("cycle")) {
  Console.WriteLine("PASS: dependency cycle rejected");
}
try {
  cache.Resolve([ModuleSnapshot.Create("A", "a", "missing")], "options-v1", Resolve);
  throw new Exception("FAIL: missing dependency must be rejected");
} catch (InvalidOperationException ex) when (ex.Message.Contains("Missing dependency")) {
  Console.WriteLine("PASS: missing dependency rejected");
}

Console.WriteLine("All 11 checks passed.");
