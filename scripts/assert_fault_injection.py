#!/usr/bin/env python3
import json,sys
from pathlib import Path
f=Path(sys.argv[1])/"fresh-fault_probe.json"
x=Path(sys.argv[2])/"faulty-cache-fault_probe.json"
assert f.exists() and x.exists(), "Missing fault probe traces"
a=json.loads(f.read_text())["records"]
b=json.loads(x.read_text())["records"]
assert [r["source"] for r in a]==[r["source"] for r in b], "Sources differ"
diff=[i for i,(p,q) in enumerate(zip(a,b))
      if p["diagnostics"]!=q["diagnostics"] or p.get("semantic")!=q.get("semantic")]
assert diff, "Fault not detected by differential oracle"
print("End-to-end stale resolver cache detected on revisions",diff)
