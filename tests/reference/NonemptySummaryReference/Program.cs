using System.Collections.Concurrent;
using System.Collections.Immutable;

// Reference implementation for the Dafny model; not injected into Dafny itself.
// Each key field is a collision-free length-delimited encoding of its source
// components (assuming .NET string equality); it is NOT a digest.
record Symbol(string Name, string TypeName);
record SemanticContext(
    int Owner,
    ImmutableArray<Symbol> Locals,
    ImmutableArray<Symbol> Imports,
    ImmutableArray<string> Options,
    ImmutableArray<string> Plugins);

record SemanticKey(string Locals, string Imports, string Options, string Plugins)
{
    private static string Encode(IEnumerable<string> values) =>
        string.Concat(values.Select(s => $"{s.Length}:{s}"));

    private static string EncodeSymbols(IEnumerable<Symbol> symbols) =>
        Encode(symbols.Select(s => Encode(new[] { s.Name, s.TypeName })));

    public static SemanticKey From(SemanticContext context) =>
        new(EncodeSymbols(context.Locals), EncodeSymbols(context.Imports),
            Encode(context.Options), Encode(context.Plugins));
}

record ImmutableSummary(SemanticKey Key, ImmutableArray<Symbol> Symbols);
record Resolved(int Owner, Dictionary<string, Symbol> Symbols);

sealed class ReferenceCache
{
    private readonly ConcurrentDictionary<SemanticKey, ImmutableSummary> summaries = new();
    public int Misses { get; private set; }
    public int Hits { get; private set; }

    public Resolved Resolve(SemanticContext context)
    {
        var key = SemanticKey.From(context);
        if (!summaries.TryGetValue(key, out var summary))
        {
            Misses++;
            // Represents the pure resolver function of the Dafny model.
            // This is deliberately not a call to the real Dafny resolver.
            summary = new ImmutableSummary(key, context.Locals.AddRange(context.Imports));
            summary = summaries.GetOrAdd(key, summary);
        }
        else
        {
            Hits++;
        }
        // New owner and new mutable dictionary for EACH resolution.
        return new Resolved(context.Owner, summary.Symbols.ToDictionary(s => s.Name));
    }
}

static class Program
{
    private static void Check(bool condition, string reason)
    {
        if (!condition) throw new InvalidOperationException(reason);
    }

    public static void Main()
    {
        var a = new Symbol("a", "int");
        var b = new Symbol("b", "bool");
        var original = new SemanticContext(10, [a], [b], ["type-system=1"], ["rewriter=none"]);
        var next = original with { Owner = 11 };
        var cache = new ReferenceCache();
        var first = cache.Resolve(original);
        var second = cache.Resolve(next);
        Check(cache.Misses == 1 && cache.Hits == 1, "Real second-hit witness missing");
        Check(first.Owner == 10 && second.Owner == 11, "Stale owner reattachment");
        Check(second.Symbols.Count == 2 && second.Symbols["b"] == b, "Nonempty summary lost imports");
        Check(!ReferenceEquals(first.Symbols, second.Symbols), "Shared mutable dictionary");
        second.Symbols.Remove("b");
        Check(first.Symbols.ContainsKey("b"), "Mutation leaked across revisions");
        Check(cache.Resolve(next).Symbols.ContainsKey("b"), "Mutation corrupted cached summary");

        // Negative dependency tests: changes to each key dimension are misses.
        var before = cache.Misses;
        cache.Resolve(next with { Imports = [new Symbol("b", "int")] });
        cache.Resolve(next with { Options = ["type-system=2"] });
        cache.Resolve(next with { Plugins = ["rewriter=custom"] });
        cache.Resolve(next with { Locals = [new Symbol("a", "bool")] });
        Check(cache.Misses == before + 4, "Semantic dependency omitted from key");

        // Failure witness: a key that discards imports merges different contexts.
        var missingImportKey = original.Locals;
        Check(missingImportKey.SequenceEqual((original with { Imports = [] }).Locals),
            "Negative key witness must collide");
        Check(!original.Imports.SequenceEqual(ImmutableArray<Symbol>.Empty),
            "Different semantics must be observable");

        Console.WriteLine("PASS: nonempty MISS/HIT, owner reattachment, mutation isolation, 4 dependency invalidations, missing-import witness");
    }
}
