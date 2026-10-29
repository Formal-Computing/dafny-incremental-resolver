using System.Collections.Immutable;

namespace IncrementalResolver.Core;

/// <summary>
/// Reference model of a cache for immutable synthetic resolution results.
/// This does NOT cache Dafny ModuleResolutionResult objects, which contain mutable AST state.
/// It is a testable policy model to validate hashing, invalidation, and dependency propagation.
/// Dafny's own CachingResolver is the place to integrate real resolution reuse.
/// </summary>
public sealed class IncrementalCache<T> {
  private sealed record Entry(string Fingerprint, T Value);
  private readonly Dictionary<string, Entry> cache = new(StringComparer.Ordinal);
  public sealed record ResolutionRun(
    ImmutableDictionary<string, T> Results,
    ImmutableArray<string> Hits,
    ImmutableArray<string> Misses,
    ImmutableDictionary<string, string> SemanticFingerprints);

  public ResolutionRun Resolve(
    IEnumerable<ModuleSnapshot> modules,
    string environmentFingerprint,
    Func<ModuleSnapshot, IReadOnlyDictionary<string, T>, T> resolveModule) {
    var map = RevisionPlanner.MapByIdentity(modules);
    var state = new Dictionary<string, byte>(StringComparer.Ordinal);
    var hashes = new Dictionary<string, string>(StringComparer.Ordinal);
    var results = new Dictionary<string, T>(StringComparer.Ordinal);
    var hits = new List<string>();
    var misses = new List<string>();

    string CalculateAndResolve(string id) {
      if (state.GetValueOrDefault(id) == 1) {
        throw new InvalidOperationException($"Dependency cycle involving {id}; refusing cached resolution");
      }
      if (state.GetValueOrDefault(id) == 2) {
        return hashes[id];
      }
      if (!map.TryGetValue(id, out var module)) {
        throw new InvalidOperationException($"Missing dependency {id}; refusing cached resolution");
      }
      state[id] = 1;
      var dependencyFingerprints = module.Dependencies.Select(dep => (dep, hash: CalculateAndResolve(dep))).ToList();
      var parts = new List<string> { "incremental-resolver-schema-1", environmentFingerprint, id, module.SourceFingerprint };
      foreach (var (dependency, hash) in dependencyFingerprints) {
        parts.Add(dependency);
        parts.Add(hash);
      }
      var semanticFingerprint = ModuleSnapshot.HashParts(parts);
      hashes[id] = semanticFingerprint;
      if (cache.TryGetValue(id, out var entry) && entry.Fingerprint == semanticFingerprint) {
        results[id] = entry.Value;
        hits.Add(id);
      } else {
        var dependencies = dependencyFingerprints.ToDictionary(pair => pair.dep,
          pair => results[pair.dep], StringComparer.Ordinal);
        var value = resolveModule(module, dependencies);
        results[id] = value;
        cache[id] = new Entry(semanticFingerprint, value);
        misses.Add(id);
      }
      state[id] = 2;
      return semanticFingerprint;
    }

    foreach (var id in map.Keys.OrderBy(x => x, StringComparer.Ordinal)) {
      CalculateAndResolve(id);
    }
    foreach (var stale in cache.Keys.Except(map.Keys, StringComparer.Ordinal).ToArray()) {
      cache.Remove(stale);
    }
    return new ResolutionRun(
      results.ToImmutableDictionary(StringComparer.Ordinal),
      hits.OrderBy(x => x, StringComparer.Ordinal).ToImmutableArray(),
      misses.OrderBy(x => x, StringComparer.Ordinal).ToImmutableArray(),
      hashes.ToImmutableDictionary(StringComparer.Ordinal));
  }
}
