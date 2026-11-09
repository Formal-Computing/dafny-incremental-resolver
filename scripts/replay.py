#!/usr/bin/env python3
"""Explicit, reproducible replays of repository evidence workflows.

Pinned Dafny stages require a separately prepared checkout. See --help for the
exact preparation sequence; this script never edits that checkout.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_SHA = "de36f2ec1f9c530080eff7929ae28229f45da069"
PROJECT = "Source/DafnyLanguageServer.Test/DafnyLanguageServer.Test.csproj"
DLL = "Source/DafnyLanguageServer.Test/bin/Debug/net8.0/DafnyLanguageServer.Test.dll"
SAFE = "FullyQualifiedName~VerificationStatusTest.ResearchVerificationOutcomeTrace"
SEMANTIC = "FullyQualifiedName~CachingTest.ResearchDifferentialTrace"
EXPORT_DIFF = "FullyQualifiedName~CachingTest.ResearchExportSummaryDifferentialTrace"
EXPORT_PROOF = "FullyQualifiedName~VerificationStatusTest.ResearchExportProofOutcomeTrace"
ENV_ALLOW = {
    "DAFNY_RESEARCH_MODE", "DAFNY_EXPERIMENTAL_CONTENT_HASH",
    "DAFNY_RESEARCH_DISABLE_SEMANTIC_CACHE", "DAFNY_RESEARCH_SAFE_REVALIDATE",
    "DAFNY_RESEARCH_IMMUTABLE_EXPORT_SUMMARY", "DAFNY_RESEARCH_AUDIT_COLLISION_PROBE",
    "DAFNY_RESEARCH_OUTPUT_DIR", "DAFNY_RESEARCH_PROFILE_RESOLVER",
}
STAGES = {
    "smoke": "local smoke suite; synthetic checks",
    "reference": "C# nonempty immutable-summary reference model",
    "formal": "six abstract Dafny proof files",
    "lsp-differential": "UNAVAILABLE: correctness replay would require an unsafe experimental mode",
    "safe-revalidation": "pinned controlled-revalidation workflow, independent fresh oracle and comparator",
    "restricted-export": "pinned immutable-export workflow, fresh oracle and comparator",
    "terminal-verifier": "pinned terminal verifier outcomes with fresh oracle and comparator",
    "archived-evidence": "read-only archived AIR evidence consistency checker",
}

def parser():
    p = argparse.ArgumentParser(description=__doc__, epilog=(
        "Prepare pinned Dafny manually: checkout dafny-lang/dafny at " + UPSTREAM_SHA +
        " with recursive submodules; install tests using scripts/install_verifier_outcome_test.py "
        "and scripts/install_differential_test.py; apply patches 0001 through 0007 in order; "
        "dotnet tool restore; build Source/DafnyLanguageServer.Test in Debug. See the matching "
        ".github/workflows/controlled-revalidation.yml and immutable-export-summary.yml. "
        "No upstream checkout is modified by replay.py."))
    sub=p.add_subparsers(dest="command",required=True)
    sub.add_parser("list",help="list evidence stages")
    for cmd in ("dry-run","execute"):
        q=sub.add_parser(cmd); q.add_argument("stage",choices=STAGES)
        q.add_argument("--dafny",type=Path,help="prepatched pinned Dafny checkout")
        q.add_argument("--output",type=Path,default=ROOT/"replay-runs")
        q.add_argument("--allow-experimental-unsafe",action="store_true",help=argparse.SUPPRESS)
    return p

def stamp(): return dt.datetime.now(dt.timezone.utc).isoformat()

def git(path,*args):
    return subprocess.run(["git","-C",str(path),*args],capture_output=True,text=True,check=False)

def preflight(dafny):
    if dafny is None: raise ValueError("--dafny is required; see --help for explicit pinned checkout preparation")
    if git(dafny,"rev-parse","--show-toplevel").returncode: raise ValueError(f"{dafny} is not a Git checkout")
    sha=git(dafny,"rev-parse","HEAD").stdout.strip()
    if sha != UPSTREAM_SHA: raise ValueError(f"pinned Dafny checkout required: expected {UPSTREAM_SHA}, got {sha}")
    patches=sorted((ROOT/"patches").glob("000[1-7]-*.patch"))
    if len(patches)!=7: raise ValueError("expected research patch chain 0001 through 0007")
    status=git(dafny,"status","--porcelain","--untracked-files=no")
    if status.returncode: raise ValueError("cannot inspect Dafny patch state")
    modified={line[3:] for line in status.stdout.splitlines() if len(line)>3}
    patch_targets=set()
    for patch in patches:
        for line in patch.read_text(encoding="utf-8").splitlines():
            if line.startswith("+++ b/"): patch_targets.add(line[6:])
    if not patch_targets<=modified:
        absent=sorted(patch_targets-modified)
        raise ValueError("patch chain appears incomplete; unmodified patched paths: "+", ".join(absent[:8]))
    applied=[p.name for p in patches]
    if not (dafny/"Source/DafnyLanguageServer.Test/Synchronization/CachingTest.cs").is_file() or not (dafny/"Source/DafnyLanguageServer.Test/Synchronization/VerificationStatusTest.cs").is_file():
        raise ValueError("test harness source files missing; run both install_*_test.py setup commands (see --help)")
    if not (dafny/DLL).is_file(): raise ValueError("built Debug test harness DLL missing; run dotnet build Source/DafnyLanguageServer.Test/DafnyLanguageServer.Test.csproj -c Debug --nologo")
    if not shutil.which("dotnet"): raise ValueError("dotnet is required")
    return applied

def test(dafny, run_dir, filter_, mode, flags):
    env={"DAFNY_RESEARCH_MODE":mode,"DAFNY_EXPERIMENTAL_CONTENT_HASH":"0",
         "DAFNY_RESEARCH_OUTPUT_DIR":"{run_dir}/research-results",**flags}
    if not set(env)<=ENV_ALLOW or any("UNSAFE" in k for k in env): raise ValueError("unsafe or unapproved environment flag")
    argv=[shutil.which("dotnet"),"test",PROJECT,"--no-build","-c","Debug","--nologo","--filter",filter_]
    return {"cwd":str(dafny),"argv":argv,"environment":env}

def plan(stage,dafny=None):
    if stage=="lsp-differential": raise ValueError("UNAVAILABLE: correctness replay would launch the unsafe experimental mode; no unsafe opt-in is supported")
    if stage in ("smoke","reference"):
        if not shutil.which("dotnet"): raise ValueError("dotnet is required")
        project="tests/IncrementalResolver.SmokeTests/IncrementalResolver.SmokeTests.csproj" if stage=="smoke" else "tests/reference/NonemptySummaryReference/NonemptySummaryReference.csproj"
        argv=[shutil.which("dotnet"),"run","--project",project]+([] if stage=="smoke" else ["-c","Release"])
        return [{"cwd":str(ROOT),"argv":argv,"environment":{}}]
    if stage=="archived-evidence": return [{"cwd":str(ROOT),"argv":[sys.executable,"scripts/check_archived_evidence.py"],"environment":{}}]
    if stage=="formal":
        cli=shutil.which("dafny"); z3=shutil.which("z3")
        if not cli or not z3: raise ValueError("Dafny 4.11.0 and Z3 required")
        v=subprocess.run([cli,"--version"],capture_output=True,text=True)
        if v.returncode or "4.11.0" not in v.stdout+v.stderr: raise ValueError("formal stage requires Dafny 4.11.0")
        names=["CacheSoundness","CacheRefinement","MutableReuseAndKeyCompleteness","ControlledRevalidationRefinement","ImmutableExportSummaryRefinement","NonemptyImmutableSummaryRefinement"]
        return [{"cwd":str(ROOT),"argv":[cli,"verify",f"tests/formal/{n}.dfy","--solver-path",z3],"environment":{}} for n in names]
    applied=preflight(dafny)
    if stage=="safe-revalidation":
        return [test(dafny,"{run_dir}",SEMANTIC,"fresh-semantic",{"DAFNY_RESEARCH_DISABLE_SEMANTIC_CACHE":"1"}),
                test(dafny,"{run_dir}",SAFE,"fresh-semantic",{"DAFNY_RESEARCH_DISABLE_SEMANTIC_CACHE":"1"}),
                test(dafny,"{run_dir}",SEMANTIC,"safe-audit",{"DAFNY_RESEARCH_SAFE_REVALIDATE":"1","DAFNY_EXPERIMENTAL_CONTENT_HASH":"1"}),
                test(dafny,"{run_dir}",SAFE,"safe-audit",{"DAFNY_RESEARCH_SAFE_REVALIDATE":"1","DAFNY_EXPERIMENTAL_CONTENT_HASH":"1"}),
                {"cwd":str(ROOT),"argv":[sys.executable,"scripts/compare_safe_revalidation.py","{run_dir}/research-results"],"environment":{}}]
    if stage=="restricted-export":
        steps=[test(dafny,"{run_dir}","FullyQualifiedName~CachingTest.ResearchImmutableExportSummaryActuallySkipsResolver","immutable-export",{"DAFNY_RESEARCH_IMMUTABLE_EXPORT_SUMMARY":"1","DAFNY_RESEARCH_SAFE_REVALIDATE":"1"}),
        test(dafny,"{run_dir}","FullyQualifiedName~CachingTest.ResearchNonemptyModulesNeverUseExportSummary","immutable-export",{"DAFNY_RESEARCH_IMMUTABLE_EXPORT_SUMMARY":"1","DAFNY_RESEARCH_SAFE_REVALIDATE":"1"}),
        test(dafny,"{run_dir}","FullyQualifiedName~CachingTest.ResearchNonemptyAuditDetectsForcedCollisionWithoutReuse","immutable-export",{"DAFNY_RESEARCH_SAFE_REVALIDATE":"1","DAFNY_RESEARCH_AUDIT_COLLISION_PROBE":"1"}),
        test(dafny,"{run_dir}",EXPORT_DIFF,"fresh-semantic",{"DAFNY_RESEARCH_DISABLE_SEMANTIC_CACHE":"1"}),
        test(dafny,"{run_dir}",EXPORT_DIFF,"immutable-export",{"DAFNY_RESEARCH_IMMUTABLE_EXPORT_SUMMARY":"1","DAFNY_RESEARCH_SAFE_REVALIDATE":"1"}),
        test(dafny,"{run_dir}",EXPORT_PROOF,"fresh-semantic",{"DAFNY_RESEARCH_DISABLE_SEMANTIC_CACHE":"1"}),
        test(dafny,"{run_dir}",EXPORT_PROOF,"immutable-export",{"DAFNY_RESEARCH_IMMUTABLE_EXPORT_SUMMARY":"1","DAFNY_RESEARCH_SAFE_REVALIDATE":"1"}),
        {"cwd":str(ROOT),"argv":[sys.executable,"scripts/compare_immutable_export.py","{run_dir}/research-results"],"environment":{}},
        {"cwd":str(ROOT),"argv":[sys.executable,"scripts/assert_export_contract.py","{dafny}","{run_dir}/research-results"],"environment":{}}]
        return steps
    if stage=="terminal-verifier":
        return [test(dafny,"{run_dir}",SAFE,"fresh-semantic",{"DAFNY_RESEARCH_DISABLE_SEMANTIC_CACHE":"1"}),
                test(dafny,"{run_dir}",SAFE,"safe-audit",{"DAFNY_RESEARCH_SAFE_REVALIDATE":"1","DAFNY_EXPERIMENTAL_CONTENT_HASH":"1"}),
                {"cwd":str(ROOT),"argv":[sys.executable,"scripts/compare_verification_outcomes.py","{run_dir}/research-results"],"environment":{}}]
    raise ValueError(f"unsupported stage: {stage}")

def main(argv=None):
    args=parser().parse_args(argv)
    if args.command=="list":
        for k,v in STAGES.items(): print(f"{k}: {v}")
        return 0
    out=None
    try:
        if args.allow_experimental_unsafe: raise ValueError("--allow-experimental-unsafe is removed; unsafe mode is never correctness evidence")
        dafny=args.dafny.resolve() if args.dafny else None
        # Allocate execute evidence directory before preflight so failures are recorded too.
        if args.command=="execute":
            run_id=f"{dt.datetime.now().strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
            out=args.output.resolve()/run_id; out.mkdir(parents=True,exist_ok=False)
        stages=plan(args.stage,dafny)
        for s in stages:
            s["cwd"]=s["cwd"].replace("{run_dir}",str(out or args.output.resolve())).replace("{dafny}",str(dafny or ""))
            s["argv"]=[a.replace("{run_dir}",str(out or args.output.resolve())).replace("{dafny}",str(dafny or "")) for a in s["argv"]]
            s["environment"]={k:v.replace("{run_dir}",str(out or args.output.resolve())) for k,v in s["environment"].items()}
            print(json.dumps(s))
        if args.command=="dry-run": return 0
        manifest={"schema":"dafny-replay-run-v2","run_id":run_id,"started_at":stamp(),"stage":args.stage,"upstream_sha":UPSTREAM_SHA if dafny else None,"commands":[],"exit_code":None}
        code=0
        with (out/"stdout.log").open("w") as stdout,(out/"stderr.log").open("w") as stderr:
            for s in stages:
                # Child environment contains only explicit allowlisted values plus required PATH/system defaults; never serialize ambient env.
                manifest["commands"].append({"cwd":s["cwd"],"argv":s["argv"],"environment":s["environment"]})
                try: code=subprocess.run(s["argv"],cwd=s["cwd"],env={"PATH":os.environ.get("PATH",""),"HOME":os.environ.get("HOME",""),"DOTNET_CLI_HOME":os.environ.get("DOTNET_CLI_HOME",""),**s["environment"]},stdout=stdout,stderr=stderr,check=False).returncode
                except OSError as e: stderr.write(f"launch error: {e}\n"); code=127
                if code: break
        manifest.update(exit_code=code,finished_at=stamp())
        (out/"run-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
        print(f"run directory: {out}"); return code
    except (ValueError,OSError,subprocess.CalledProcessError) as e:
        print(f"replay: {e}",file=sys.stderr)
        if out:
            manifest={"schema":"dafny-replay-run-v2","run_id":out.name,"started_at":stamp(),"finished_at":stamp(),"stage":args.stage,"upstream_sha":UPSTREAM_SHA if args.dafny else None,"commands":[],"exit_code":2,"preflight_error":str(e)}
            (out/"stdout.log").touch(); (out/"stderr.log").write_text(str(e)+"\n"); (out/"run-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
            print(f"run directory: {out}")
        return 2

def self_test():
    with mock.patch.object(shutil,"which",return_value="/mock/dotnet"):
        assert main(["dry-run","smoke"])==0
    assert main(["dry-run","lsp-differential"])==2
    assert main(["dry-run","lsp-differential","--allow-experimental-unsafe"])==2
    print("PASS: replay CLI safety checks")
    return 0

if __name__=="__main__":
    raise SystemExit(self_test() if sys.argv[1:]==["--self-test"] else main())
