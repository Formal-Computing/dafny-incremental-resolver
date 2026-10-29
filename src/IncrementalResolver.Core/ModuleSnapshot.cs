using System.Collections.Immutable;
using System.Security.Cryptography;
using System.Text;

namespace IncrementalResolver.Core;

/// <summary>
/// Immutable data extracted from an *unresolved* Dafny module AST.
/// SourceFingerprint must include the tokens, positions, and relevant resolver options.
/// A fingerprint of a resolved AST is invalid as a cache key: resolution mutates the AST.
/// </summary>
public sealed record ModuleSnapshot(
  string Identity,
  string SourceFingerprint,
  ImmutableArray<string> Dependencies) {

  public static ModuleSnapshot Create(string identity, string fingerprint, params string[] dependencies) {
    if (string.IsNullOrWhiteSpace(identity)) {
      throw new ArgumentException("Module identity cannot be empty", nameof(identity));
    }
    if (string.IsNullOrWhiteSpace(fingerprint)) {
      throw new ArgumentException("A source fingerprint is required", nameof(fingerprint));
    }
    return new(identity, fingerprint, dependencies.Distinct(StringComparer.Ordinal)
      .OrderBy(x => x, StringComparer.Ordinal).ToImmutableArray());
  }

  public static string HashParts(IEnumerable<string> values) {
    // Length prefixes prevent ambiguity between ["a", "bc"] and ["ab", "c"].
    using var stream = new MemoryStream();
    using var writer = new BinaryWriter(stream, Encoding.UTF8, leaveOpen: true);
    foreach (var value in values) {
      var bytes = Encoding.UTF8.GetBytes(value);
      writer.Write(bytes.Length);
      writer.Write(bytes);
    }
    writer.Flush();
    return Convert.ToHexString(SHA256.HashData(stream.ToArray()));
  }
}
