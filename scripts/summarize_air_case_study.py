#!/usr/bin/env python3
"""Summarize paired AIR-derived Dafny LSP benchmark. No causal speedup claims."""
from pathlib import Path
import collections, json, statistics, sys
root=Path(sys.argv[1])
modes=["original","fresh","patched-baseline","experimental"]
traces={m:json.loads((root/f"{m}-air-satlib.json").read_text()) for m in modes}
assert len({str(x["input"]) for x in traces.values()})==1
summary={"kind":"AIR-SATLIB typed-Dafny-LSP-case-study-v1",
         "input":traces["fresh"]["input"],
         "source":traces["fresh"]["source"],
         "modes":{},"limitations":["Same-length edit class favors position-sensitive caching.",
         "Time is end-to-end notification latency, not resolver CPU.",
         "GC allocated bytes are entire in-process client+server; not isolated resolver memory.",
         "Sequential modes on one CI runner are not randomized or independent speedup evidence.",
         "Dafny semantic resolver is tested, not CNF satisfiability.",
         "The no-resolution-cache mode still uses Dafny's parser cache."]}
for mode in modes:
    x=traces[mode]["samples"]
    assert len(x)==7 and all(v["edit"]=="same-length-RevisionTag" for v in x[:6])
    measured=[v for v in x[:6] if not v["warmup"]]
    assert len(measured)==4
    def count(field):
        return sum(v[field] for v in measured)
    per=collections.defaultdict(lambda:collections.Counter())
    for v in measured:
        for item in v["trackedModules"]:
            per[item["name"]].update(hit=int(item["hit"]),miss=int(item["miss"]))
    profiles=[entry for edit in measured for entry in edit.get("profile",[])]
    profile_misses=[e for e in profiles if e["disposition"]=="MISS"]
    profile_hits=[e for e in profiles if e["disposition"]=="HIT"]
    profile_stats={
       "events":len(profiles),
       "misses":len(profile_misses),
       "hits":len(profile_hits),
       "inclusiveResolveBodyWallMicroseconds":round(sum(e["resolutionBodyMicroseconds"] for e in profile_misses),3),
       "inclusiveResolveBodyThreadAllocatedBytes":sum(e["resolutionBodyThreadAllocatedBytes"] for e in profile_misses),
       "hashWallMicroseconds":round(sum(e["hashMicroseconds"] for e in profiles),3),
       "hashThreadAllocatedBytes":sum(e["hashThreadAllocatedBytes"] for e in profiles)
    } if profiles else None
    summary["modes"][mode]={
       "iterations":len(measured),
       "resolverProfile":profile_stats,
       "medianUpdateMs":round(statistics.median(v["milliseconds"] for v in measured),3),
       "minUpdateMs":round(min(v["milliseconds"] for v in measured),3),
       "maxUpdateMs":round(max(v["milliseconds"] for v in measured),3),
       "medianProcessAllocatedBytes":int(statistics.median(v["allocationsAllProcessBytes"] for v in measured)),
       "resolutionCacheHits":count("resolutionHits"),
       "resolutionCacheMisses":count("resolutionMisses"),
       "trackedModules":{k:dict(v) for k,v in per.items()},
       "prefixInsertion":x[-1]
    }
(root/"air-satlib-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
lines=["# AIR SATLIB to Dafny incremental resolution case study","",
"Generated from Formal-Computing/cdcl-sat-solver at 88247ab: 298 real clauses, "
"two source benchmark instances, converted into typed Dafny constants and a dependent summary module. "
"This measures incremental semantic resolution of the generated Dafny program, not CDCL runtime.","",
"## Results (one Ubuntu CI runner; 2 warmup + 4 measured edits per mode)","",
"| Resolver mode | Median LSP ms | Cache hits | Cache misses | Median total process allocations (bytes) |",
"|---|---:|---:|---:|---:|"]
for k in modes:
    s=summary["modes"][k]
    lines.append(f"| {k} | {s['medianUpdateMs']:.3f} | {s['resolutionCacheHits']} | {s['resolutionCacheMisses']} | {s['medianProcessAllocatedBytes']:,} |")
lines+=["","## Tracked clause data modules (4 measured revisions)","",
         "| Mode | Module | Hits | Misses |","|---|---|---:|---:|"]
for k in modes:
    for m,x in summary["modes"][k]["trackedModules"].items():
        lines.append(f"| {k} | {m} | {x['hit']} | {x['miss']} |")
if all(summary["modes"][k]["resolverProfile"] for k in ("patched-baseline","experimental")):
    lines+=["","## Synchronous resolver regions (instrumented patch, 4 edits)","",
      "| Mode | Profiled hits/misses | Inclusive resolution body (ms) | Inclusive thread allocations (MiB) | Hash work (ms) |",
      "|---|---:|---:|---:|---:|"]
    for k in ("patched-baseline","experimental"):
        s=summary["modes"][k]["resolverProfile"]
        lines.append(f"| {k} | {s['hits']} / {s['misses']} | {s['inclusiveResolveBodyWallMicroseconds']/1000:.2f} | {s['inclusiveResolveBodyThreadAllocatedBytes']/1048576:.2f} | {s['hashWallMicroseconds']/1000:.2f} |")
    lines+=["","**These are synchronous wall-clock regions, not CPU samples.** Body times/allocations are inclusive and can double count nested work. Both modes used the same opt-in measurement patch; absolute values include instrumentation overhead. Source positions must be identical for reuse."]

lines+=["",
"## Worked edit trace",
"1. The LSP opens a single generated Dafny file containing 298 original SATLIB clauses as typed declarations.",
"2. A small function AIR_WorkingEdit.RevisionTag() follows the large unchanged source modules.",
"3. Four measured revisions alternate only 10 and 11 (equal source length); unchanged module source tokens/positions remain identical.",
"4. The upstream clone-identifier-based key conservatively misses after a fresh parse. The experimental content-aware key may reuse unchanged modules; the table records actual log entries for each.",
"5. A final prefix insertion shifts all module source positions and is expected to conservatively invalidate them. Prefix-insertion diagnostics are captured separately in air-satlib-summary.json.",
"",
"## Limitations"]
lines += ["- "+lim for lim in summary["limitations"]]
lines += ["","The primary resource-saving quantity is the observed number of module resolutions avoided, not a defensible standalone CPU/memory speedup. "
          "Repeat on independent runners with counterbalanced modes and isolated resolver timing before drawing speedup conclusions."]
(root/"air-satlib-report.md").write_text("\n".join(lines)+"\n")
print("Prepared summary and Markdown report at",root)
for k in modes:
 s=summary["modes"][k];print(k,s["medianUpdateMs"],s["resolutionCacheHits"],s["resolutionCacheMisses"])
