using System.Collections.Immutable;

namespace IncrementalResolver.Core;

/// <summary>
/// Reports invalidations without touching or mutating Dafny's resolved AST.
/// Directions are: module -> modules that it depends on.
/// An updated dependency can invalidate any of its dependents.
/// </summary>
public static class RevisionPlanner {
  public sealed record RevisionPlan(
    ImmutableArray<string> Added,
    ImmutableArray<string> Removed,
    ImmutableArray<string> DirectlyModified,
    ImmutableArray<string> TransitivelyInvalidated,
    ImmutableArray<string> Reusable);

  public static RevisionPlan Analyze(
    IEnumerable<ModuleSnapshot> oldModules,
    IEnumerable<ModuleSnapshot> newModules) {
    var oldMap = MapByIdentity(oldModules);
    var newMap = MapByIdentity(newModules);
    var added = newMap.Keys.Except(oldMap.Keys, StringComparer.Ordinal).ToHashSet(StringComparer.Ordinal);
    var removed = oldMap.Keys.Except(newMap.Keys, StringComparer.Ordinal).ToHashSet(StringComparer.Ordinal);
    var modified = newMap.Keys.Intersect(oldMap.Keys, StringComparer.Ordinal)
      .Where(id => oldMap[id].SourceFingerprint != newMap[id].SourceFingerprint ||
                   !oldMap[id].Dependencies.SequenceEqual(newMap[id].Dependencies))
      .ToHashSet(StringComparer.Ordinal);
    var seeds = new HashSet<string>(added, StringComparer.Ordinal);
    seeds.UnionWith(removed);
    seeds.UnionWith(modified);

    // Include edges from BOTH versions: a deleted import or symbol must invalidate
    // its previous dependents even though the edge no longer exists in the new AST.
    var reverse = new Dictionary<string, HashSet<string>>(StringComparer.Ordinal);
    foreach (var module in oldMap.Values.Concat(newMap.Values)) {
      foreach (var dependency in module.Dependencies) {
        if (!reverse.TryGetValue(dependency, out var dependents)) {
          reverse[dependency] = dependents = new HashSet<string>(StringComparer.Ordinal);
        }
        dependents.Add(module.Identity);
      }
    }
    var visited = new HashSet<string>(seeds, StringComparer.Ordinal);
    var pending = new Queue<string>(seeds);
    while (pending.TryDequeue(out var changed)) {
      if (!reverse.TryGetValue(changed, out var dependents)) {
        continue;
      }
      foreach (var dependent in dependents) {
        if (visited.Add(dependent)) {
          pending.Enqueue(dependent);
        }
      }
    }
    var impacted = visited.Where(newMap.ContainsKey).ToHashSet(StringComparer.Ordinal);
    return new RevisionPlan(
      Sort(added), Sort(removed), Sort(modified),
      Sort(impacted.Except(seeds, StringComparer.Ordinal)),
      Sort(newMap.Keys.Except(impacted, StringComparer.Ordinal)));
  }

  internal static Dictionary<string, ModuleSnapshot> MapByIdentity(IEnumerable<ModuleSnapshot> modules) {
    var result = new Dictionary<string, ModuleSnapshot>(StringComparer.Ordinal);
    foreach (var module in modules) {
      if (!result.TryAdd(module.Identity, module)) {
        throw new InvalidOperationException($"Duplicate module identity: {module.Identity}");
      }
    }
    return result;
  }

  private static ImmutableArray<string> Sort(IEnumerable<string> values) =>
    values.OrderBy(x => x, StringComparer.Ordinal).ToImmutableArray();
}
