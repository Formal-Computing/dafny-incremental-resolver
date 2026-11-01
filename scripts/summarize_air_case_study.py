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
    assert len(x)==13 and all(v["edit"]=="same-length-RevisionTag" for v in x[:12])
    measured=[v for v in x[:12] if not v["warmup"]]
    assert len(measured)==10
    def count(field):
        return sum(v[field] for v in measured)
    per=collections.defaultdict(lambda:collections.Counter())
    for v in measured:
        for item in v["trackedModules"]:
            per[item["name"]].update(hit=int(item["hit"]),miss=int(item["miss"]))
    summary["modes"][mode]={
       "iterations":len(measured),
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
"Generated from Formal-Computing/cdcl-sat-solver at 88247ab: 662 real clauses, "
"three source benchmark instances, converted into typed Dafny constants and a dependent summary module. "
"This measures incremental semantic resolution of the generated Dafny program, not CDCL runtime.","",
"## Results (one Ubuntu CI runner; 2 warmup + 10 measured edits per mode)","",
"| Resolver mode | Median LSP ms | Cache hits | Cache misses | Median total process allocations (bytes) |",
"|---|---:|---:|---:|---:|"]
for k in modes:
    s=summary["modes"][k]
    lines.append(f"| {k} | {s['medianUpdateMs']:.3f} | {s['resolutionCacheHits']} | {s['resolutionCacheMisses']} | {s['medianProcessAllocatedBytes']:,} |")
lines+=["","## Tracked clause data modules (10 measured revisions)","",
         "| Mode | Module | Hits | Misses |","|---|---|---:|---:|"]
for k in modes:
    for m,x in summary["modes"][k]["trackedModules"].items():
        lines.append(f"| {k} | {m} | {x['hit']} | {x['miss']} |")
lines+=["",
"## Worked edit trace",
"1. The LSP opens a single 768-line Dafny file containing 662 original SATLIB clauses as typed declarations.",
"2. A small function AIR_WorkingEdit.RevisionTag() follows the large unchanged source modules.",
"3. Ten measured revisions alternate only 10 and 11 (equal source length); unchanged module source tokens/positions remain identical.",
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
