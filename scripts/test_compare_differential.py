"""Self-test the oracle with independent corruption of each observable type."""
import json
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from compare_differential import EXTENDED_SCENARIOS, MODES, QUERIED, SCENARIOS, compare


def write_traces(root, corrupt=None, scenarios=SCENARIOS):
    for scenario in scenarios:
        for mode in MODES:
            value = {
                "mode": mode, "scenario": scenario,
                "records": [{
                    "revision": 0, "source": "module X {}",
                    "diagnostics": [],
                    "semantic": {"hover": "int", "definitions": []}
                    if scenario in QUERIED else None
                }]
            }
            if corrupt == ("diagnostic", mode, scenario):
                value["records"][0]["diagnostics"] = [{"message": "stale"}]
            if corrupt == ("semantic", mode, scenario):
                value["records"][0]["semantic"] = {"hover": "bool"}
            with open(root / f"{mode}-{scenario}.json", "w") as stream:
                json.dump(value, stream)


def run():
    with tempfile.TemporaryDirectory() as dirname:
        path = pathlib.Path(dirname)
        write_traces(path)
        assert all(x["status"] == "MATCH" for x in compare(path)["comparison"])
        for fault in (
            ("diagnostic", "experimental", "dependency"),
            ("semantic", "experimental", "stress_graph"),
            ("semantic", "fresh", "air_semantic"),
        ):
            write_traces(path, fault)
            assert any(x["status"] == "DIFFERENCE" for x in compare(path)["comparison"]), fault
        write_traces(path)
        (path / "original-stress_scope.json").unlink()
        assert any(x["status"] == "MISSING" for x in compare(path)["comparison"])
        write_traces(path, scenarios=EXTENDED_SCENARIOS)
        assert all(x["status"] == "MATCH" for x in compare(path, ("air_semantic_662",))["comparison"])
        write_traces(path, ("semantic", "experimental", "air_semantic_662"),
                     scenarios=EXTENDED_SCENARIOS)
        assert any(x["status"] == "DIFFERENCE"
                   for x in compare(path, ("air_semantic_662",))["comparison"])
    print("Oracle self-test: clean, corrupt diagnostic/semantic, parser mismatch, missing traces, isolated 662 -> PASS")


if __name__ == "__main__":
    run()
