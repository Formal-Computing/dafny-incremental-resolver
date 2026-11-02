from pathlib import Path
import difflib
root=Path.home()/'research'
up=root/'dafny-upstream'
repo=root/'dafny-incremental-resolver'
original=(up/'Source/DafnyLanguageServer/Language/CachingResolver.cs').read_text()
assert 'private byte[] GetHash(ModuleDecl moduleDeclaration)' in original
changed=original.replace('  private readonly ResolutionCache cache;', '  private readonly ResolutionCache cache;\n  private byte[]? moduleRosterHash;')
changed=changed.replace('      cache.Modules.Set(hash, result);', '''      // In experimental mode do not reuse resolution results carrying diagnostics.
      if (!ExperimentalContentHash || !result.ErrorReporter.AllMessages.Any()) {
        cache.Modules.Set(hash, result);
      }''')
changed=changed.replace('  private byte[] GetHash(ModuleDecl moduleDeclaration) {', '''  // Opt-in research mode; the upstream baseline branch is unchanged.
  private static readonly bool ExperimentalContentHash =
    Environment.GetEnvironmentVariable("DAFNY_EXPERIMENTAL_CONTENT_HASH") == "1";

  private byte[] GetHash(ModuleDecl moduleDeclaration) {
    if (ExperimentalContentHash) {
      return GetExperimentalHash(moduleDeclaration);
    }
    // Verbatim upstream implementation below.''')
changed=changed[:-2]+'''
  private byte[] GetExperimentalHash(ModuleDecl decl) {
    if (hashes.TryGetValue(decl, out var existing)) {
      return existing;
    }
    // Invalidate all cached module results if the global module roster changes.
    // This guards module add/remove/rename; not all hidden dependencies.
    moduleRosterHash ??= ComputeModuleRosterHash();
    using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
    AppendText(hash, "dafny-experimental-module-cache-v2");
    hash.AppendData(moduleRosterHash);
    var vertex = dependencies.FindVertex(decl);
    var ordered = vertex.Successors
      .Select(s => (Identity: s.N.FullName, Hash: GetHash(s.N)))
      .OrderBy(p => p.Identity, StringComparer.Ordinal)
      .ThenBy(p => Convert.ToHexString(p.Hash), StringComparer.Ordinal);
    foreach (var dependency in ordered) {
      AppendText(hash, dependency.Identity);
      hash.AppendData(dependency.Hash);
    }
    hash.AppendData(cache.Builtins!.MyHash);
    hash.AppendData(ComputePositionSensitiveSourceHash(decl));
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

  private static byte[] ComputePositionSensitiveSourceHash(ModuleDecl decl) {
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
    var data = System.Text.Encoding.UTF8.GetBytes(value ?? string.Empty);
    hash.AppendData(BitConverter.GetBytes(data.Length));
    hash.AppendData(data);
  }
}
'''
assert changed!=original
patch=''.join(difflib.unified_diff(original.splitlines(keepends=True),changed.splitlines(keepends=True),fromfile='a/Source/DafnyLanguageServer/Language/CachingResolver.cs',tofile='b/Source/DafnyLanguageServer/Language/CachingResolver.cs',n=3))
(repo/'patches/0001-experimental-module-token-hashing.patch').write_text(patch)
print('Generated patch:',len(patch),'bytes')
