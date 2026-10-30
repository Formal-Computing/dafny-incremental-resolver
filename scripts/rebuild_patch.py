#!/usr/bin/env python3
from pathlib import Path
import difflib
root=Path("/home/admin/projects/research")
repo=root/"dafny-incremental-resolver"
up=root/"dafny-pinned/Source/DafnyLanguageServer/Language/CachingResolver.cs"
orig=up.read_text()
assert "private byte[] GetHash(ModuleDecl moduleDeclaration)" in orig
new=orig.replace("  private readonly ResolutionCache cache;", "  private readonly ResolutionCache cache;\n  private byte[]? moduleRosterHash;")
new=new.replace("      cache.Modules.Set(hash, result);", """      // An error-bearing result is not safe to retain across revisions
      // without tracking failed name lookups and diagnostic origins.
      if (!ExperimentalContentHash || !result.ErrorReporter.AllMessages.Any()) {
        cache.Modules.Set(hash, result);
      }""")
new=new.replace("  private byte[] GetHash(ModuleDecl moduleDeclaration) {", """  private static readonly bool ExperimentalContentHash =
    Environment.GetEnvironmentVariable("DAFNY_EXPERIMENTAL_CONTENT_HASH") == "1";

  private byte[] GetHash(ModuleDecl moduleDeclaration) {
    if (ExperimentalContentHash) {
      return GetExperimentalHash(moduleDeclaration);
    }
    // Original upstream implementation intentionally unchanged.""")
assert new.endswith("}\n")
new=new[:-2]+"""
  private byte[] GetExperimentalHash(ModuleDecl decl) {
    if (hashes.TryGetValue(decl, out var existing)) {
      return existing;
    }
    moduleRosterHash ??= ComputeModuleRosterHash();
    using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
    AppendText(hash, "dafny-experimental-v2");
    hash.AppendData(moduleRosterHash);
    foreach (var dependency in dependencies.FindVertex(decl).Successors
      .Select(s => (Identity: s.N.FullName, Hash: GetHash(s.N)))
      .OrderBy(p => p.Identity, StringComparer.Ordinal)
      .ThenBy(p => Convert.ToHexString(p.Hash), StringComparer.Ordinal)) {
      AppendText(hash, dependency.Identity);
      hash.AppendData(dependency.Hash);
    }
    hash.AppendData(cache.Builtins!.MyHash);
    hash.AppendData(PositionSensitiveSourceHash(decl));
    return hashes[decl] = hash.GetHashAndReset();
  }

  private byte[] ComputeModuleRosterHash() {
    using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
    AppendText(hash, "module-roster-v1");
    foreach (var decl in dependencies.TopologicallySortedComponents()
      .OrderBy(d => d.FullName, StringComparer.Ordinal)
      .ThenBy(d => d.GetType().FullName, StringComparer.Ordinal)) {
      AppendText(hash, decl.FullName);
      AppendText(hash, decl.GetType().FullName);
    }
    return hash.GetHashAndReset();
  }

  private static byte[] PositionSensitiveSourceHash(ModuleDecl decl) {
    if (!decl.SingleFileToken || decl.StartToken?.Uri == null || decl.EndToken?.Uri == null) {
      return decl.CloneId.ToByteArray();
    }
    using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
    AppendText(hash, decl.GetType().FullName);
    AppendText(hash, decl.FullName);
    var count = 0;
    foreach (var token in decl.CoveredTokens) {
      if (!Equals(token.Uri, decl.StartToken.Uri)) {
        return decl.CloneId.ToByteArray();
      }
      count++;
      AppendText(hash, token.Uri?.ToString());
      AppendText(hash, token.val);
      AppendText(hash, token.LeadingTrivia);
      AppendText(hash, token.TrailingTrivia);
      hash.AppendData(BitConverter.GetBytes(token.pos));
      hash.AppendData(BitConverter.GetBytes(token.line));
      hash.AppendData(BitConverter.GetBytes(token.col));
    }
    return count == 0 ? decl.CloneId.ToByteArray() : hash.GetHashAndReset();
  }

  private static void AppendText(IncrementalHash hash, string? value) {
    var bytes = System.Text.Encoding.UTF8.GetBytes(value ?? string.Empty);
    hash.AppendData(BitConverter.GetBytes(bytes.Length));
    hash.AppendData(bytes);
  }
}
"""
patch=''.join(difflib.unified_diff(orig.splitlines(keepends=True),new.splitlines(keepends=True),fromfile="a/Source/DafnyLanguageServer/Language/CachingResolver.cs",tofile="b/Source/DafnyLanguageServer/Language/CachingResolver.cs"))
(repo/"patches/0001-experimental-module-token-hashing.patch").write_text(patch)
print("PATCH BYTES",len(patch))
