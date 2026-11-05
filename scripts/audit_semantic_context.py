#!/usr/bin/env python3
"""Fail-closed source audit of the pinned Dafny cache implementation.

Records facts about source code. A passed audit NEVER certifies semantic
completeness, deep cloning, production readiness, or soundness.
"""
import argparse
import hashlib
import json
from pathlib import Path

PINNED = "de36f2ec1f9c530080eff7929ae28229f45da069"

def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()

def collect(repo, research):
    files = {
      "cache": "Source/DafnyLanguageServer/Language/CachingResolver.cs",
      "resolver": "Source/DafnyCore/Resolver/ProgramResolver.cs",
      "module": "Source/DafnyCore/Resolver/ModuleResolver.cs"
    }
    texts = {key:(repo / path).read_text() for key,path in files.items()}
    cache,resolver,module = [texts[k] for k in ("cache","resolver","module")]
    patch = (research / "patches/0001-experimental-module-token-hashing.patch").read_text()
    assert "public record ModuleResolutionResult(" in module
    assert "Dictionary<ModuleDefinition, ModuleSignature> Signatures" in module
    assert "Dictionary<TopLevelDeclWithMembers, Dictionary<string, MemberDecl>> ClassMembers" in module
    assert "if (!cache.Modules.TryGet(hash, out var result))" in cache
    assert "return result!;" in cache
    assert "moduleDeclarationPointers[decl](moduleResolutionResult.ResolvedDeclaration)" in resolver
    assert "Program.ModuleSigs[sig.Key] = sig.Value;" in resolver
    assert "classMembers[moduleClassMembers.Key] = moduleClassMembers.Value;" in resolver
    assert "RewriterCollection.GetRewriters" in resolver
    assert "rewriter.PreResolve(Program)" in resolver
    assert "rewriter.PostResolve(Program)" in resolver
    assert "PositionSensitiveSourceHash" in patch
    assert "ComputeModuleRosterHash()" in patch
    assert "cache.Builtins!.MyHash" in patch
    assert "dependencies.FindVertex(decl).Successors" in patch
    assert "UnsafeResearchCrossRevisionReuse" in patch

    # Source-inspection facts, not dynamic semantic observations:
    excerpt=patch[patch.index("+  private byte[] GetExperimentalHash("):]
    source_key_inputs = {
      "source_tokens_including_position_origin_trivia": "PositionSensitiveSourceHash(decl)" in excerpt,
      "transitive_module_dependency_hashes": "dependencies.FindVertex(decl).Successors" in excerpt,
      "current_module_roster": "moduleRosterHash" in excerpt,
      "builtin_hash": "cache.Builtins!.MyHash" in excerpt,
      "explicit_negative_lookup_fingerprint": "failedLookups" in excerpt or "NegativeLookup" in excerpt,
      "explicit_options_fingerprint": "Options" in excerpt and ("AppendText(hash, Options" in excerpt or "hash.AppendData(Options" in excerpt),
      "explicit_rewriter_environment_fingerprint": "rewriters" in excerpt or "RewriterCollection" in excerpt
    }
    assert all(source_key_inputs[k] for k in list(source_key_inputs)[:4])
    assert not any(source_key_inputs[k] for k in list(source_key_inputs)[4:])
    return {
      "pinned_dafny_revision": PINNED,
      "source_sha256": {k:sha(v) for k,v in texts.items()},
      "patch_sha256": sha(patch),
      "cache_hit_returns_cached_reference_without_deep_clone":True,
      "cached_result_contains_mutable_dictionaries":True,
      "replay_links_resolved_declaration_signatures_and_member_dictionaries":True,
      "module_resolution_calls_pre_and_post_rewriters":True,
      "experimental_key_input_presence":source_key_inputs,
      "certifies_complete_context":False,
      "certifies_safe_object_reattachment":False,
      "limitations":[
        "Absence of explicit fields is not proof of an actual input collision; dynamic experiments required.",
        "File inspection is pinned-source-specific; changing the upstream commit invalidates these anchors.",
        "Even a complete key would not prove safe reuse of mutable AST, reporter, signature, and member dictionary objects.",
        "The test remains an opt-in unsafe research experiment."
      ]
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--dafny", type=Path, required=True)
    parser.add_argument("--research",type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=collect(args.dafny,args.research)
    out=json.dumps(result,indent=2)
    print(out)
    if args.output:
        args.output.parent.mkdir(exist_ok=True,parents=True)
        args.output.write_text(out+"\n")

if __name__=="__main__":
    main()
