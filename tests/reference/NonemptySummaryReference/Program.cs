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

// Synthetic shape used to demonstrate the C# record-copy rule. It is not the
// upstream Dafny type and does not execute the production resolver.
record MutableResolutionResult(
    int Owner,
    Dictionary<string, Dictionary<string, Symbol>> ClassMembers);

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

        // A C# record with-expression is a shallow memberwise copy. The
        // synthetic result below contains the nested mutable dictionary shape
        // noted in the pinned upstream ModuleResolutionResult declaration.
        var nested = new Dictionary<string, Dictionary<string, Symbol>> {
            ["C"] = new Dictionary<string, Symbol> { ["m"] = a }
        };
        var sourceResult = new MutableResolutionResult(20, nested);
        var shallowCopy = sourceResult with { Owner = 21 };
        Check(!ReferenceEquals(sourceResult, shallowCopy), "Record with-expression must create a new outer record");
        Check(ReferenceEquals(sourceResult.ClassMembers, shallowCopy.ClassMembers),
            "Shallow record copy unexpectedly copied outer dictionary");
        Check(ReferenceEquals(sourceResult.ClassMembers["C"], shallowCopy.ClassMembers["C"]),
            "Shallow record copy unexpectedly copied nested dictionary");
        shallowCopy.ClassMembers["C"].Remove("m");
        Check(!sourceResult.ClassMembers["C"].ContainsKey("m"),
            "Mutation through shallow copy must be visible through source alias");

        // Positive ownership case: reconstruct the mutable graph for each
        // owner from immutable semantic values instead of reattaching it.
        MutableResolutionResult Reconstruct(int owner, Symbol member) =>
            new(owner, new Dictionary<string, Dictionary<string, Symbol>> {
                ["C"] = new Dictionary<string, Symbol> { ["m"] = member }
            });

        var reconstructedFirst = Reconstruct(30, a);
        var reconstructedSecond = Reconstruct(31, a);
        Check(reconstructedFirst.Owner == 30 && reconstructedSecond.Owner == 31,
            "Fresh reconstruction must attach each current owner");
        Check(!ReferenceEquals(reconstructedFirst.ClassMembers, reconstructedSecond.ClassMembers),
            "Fresh reconstruction shared outer dictionary");
        Check(!ReferenceEquals(reconstructedFirst.ClassMembers["C"], reconstructedSecond.ClassMembers["C"]),
            "Fresh reconstruction shared nested dictionary");
        reconstructedSecond.ClassMembers["C"].Remove("m");
        Check(reconstructedFirst.ClassMembers["C"].ContainsKey("m"),
            "Mutation leaked between independently reconstructed graphs");

        Console.WriteLine("PASS: cache reference checks; synthetic shallow nested-dictionary alias; fresh-owner graph reconstruction isolation");
    }
}
