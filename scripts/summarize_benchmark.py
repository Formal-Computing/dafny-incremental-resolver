#!/usr/bin/env python3
"""Summarize exploratory persistent-LSP update times without speedup claims."""
import json
import pathlib
import statistics
import sys

source = pathlib.Path(sys.argv[1])
modes = ("original", "patched-baseline", "experimental", "fresh")
summary = {"schema": "dafny-exploratory-lsp-benchmark-v1",
           "metric": "wall-clock milliseconds from edit submission through completed LSP notification",
           "warning": "Not resolver-only timing; modes run in separate CI testhost processes; one runner and trace. No causal speedup claim.",
           "modes": {}}
for mode in modes:
    file = source / f"{mode}-benchmark.json"
    if not file.is_file():
        raise SystemExit(f"Missing required measurement {file}")
    obj = json.loads(file.read_text())
    all_samples = obj["samples"]
    measured = [s for s in all_samples if not s["warmup"]]
    if len(measured) < 10:
        raise SystemExit(f"Insufficient samples for {mode}")
    values = [float(s["milliseconds"]) for s in measured]
    if min(values) <= 0:
        raise SystemExit(f"Invalid nonpositive sample {mode}")
    summary["modes"][mode] = {
        "warmups": len(all_samples)-len(measured),
        "n": len(values),
        "median_ms": round(statistics.median(values), 4),
        "mean_ms": round(statistics.mean(values), 4),
        "stdev_ms": round(statistics.stdev(values), 4),
        "min_ms": round(min(values), 4),
        "max_ms": round(max(values), 4),
        "alpha_hits": sum(bool(x["alphaHit"]) for x in measured),
        "alpha_misses": sum(bool(x["alphaMiss"]) for x in measured),
        "beta_misses": sum(bool(x["betaMiss"]) for x in measured),
    }
(source/"benchmark-summary.json").write_text(json.dumps(summary,indent=2))
print(json.dumps(summary, indent=2))
