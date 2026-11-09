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
                "records": ([{
                    "revision": i, "source": f"module X {{ // {i} }}",
                    "diagnostics": ([{"message": "unresolved", "severity": "Error",
                                      "code": "R", "source": "dafny",
                                      "from": [0, 0], "to": [0, 1], "related": []}
                                     ] if i in (0, 2) else []),
                    "semantic": ({"hover": "```dafny\nfunction Missing(): int\n```",
                                  "definitions": [{"uri": "file:///provider.dfy"}]}
                                 if i in (1, 3) else {"hover": None, "definitions": []})
                } for i in range(4)] if scenario in ("negative", "negative_alias") else [{
                    "revision": 0, "source": "module X {}",
                    "diagnostics": [],
                    "semantic": {"hover": "int", "definitions": []}
                    if scenario in QUERIED else None
                }])
            }
            if corrupt == ("diagnostic", mode, scenario):
                value["records"][0]["diagnostics"] = [{"message": "stale"}]
            if corrupt == ("semantic", mode, scenario):
                value["records"][0]["semantic"] = {"hover": "bool"}
            if corrupt == ("absent_semantic", mode, scenario):
                value["records"] = [{**record, "semantic": None}
                                    for record in value["records"]]
            if corrupt == ("negative_diagnostic", mode, scenario):
                value["records"][0]["diagnostics"] = []
            if corrupt == ("absent_semantic", mode, scenario):
                value["records"] = [{**record, "semantic": None}
                                    for record in value["records"]]
            if corrupt == ("stale_alias_positive", mode, scenario):
                value["records"][2]["diagnostics"] = [{"message": "stale positive"}]
                value["records"][2]["semantic"] = {
                    "hover": "```dafny\nfunction Missing(): int\n```",
                    "definitions": [{"uri": "file:///provider.dfy"}]}
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
        for fault in (
            ("absent_semantic", "fresh-semantic", "negative"),
            ("negative_diagnostic", "fresh-semantic", "negative"),
        ):
            write_traces(path, fault)
            assert any(x["status"].startswith(("UNEXPECTED_NEGATIVE_", "NONINFORMATIVE_"))
                       for x in compare(path)["comparison"]), fault
        # An unresolved query is still an explicit semantic response object.
        write_traces(path, ("absent_semantic", "fresh-semantic", "negative_alias"),
                     scenarios=EXTENDED_SCENARIOS)
        assert any(x["status"] == "MISSING_NEGATIVE_SEMANTIC_QUERY"
                   for x in compare(path, ("negative_alias",))["comparison"])
        write_traces(path, scenarios=EXTENDED_SCENARIOS)
        assert all(x["status"] == "MATCH" for x in compare(path, ("negative_alias",))["comparison"])
        write_traces(path, ("stale_alias_positive", "experimental", "negative_alias"),
                     scenarios=EXTENDED_SCENARIOS)
        assert any(x["status"] == "DIFFERENCE"
                   for x in compare(path, ("negative_alias",))["comparison"])
        write_traces(path)
        (path / "original-stress_scope.json").unlink()
        assert any(x["status"] == "MISSING" for x in compare(path)["comparison"])
        # Verification-progress strings are asynchronous. When the Dafny
        # signature/type code block is identical, only the volatile status
        # text is excluded. An actual typed signature change must still fail.
        write_traces(path)
        for mode in MODES:
            f = path / f"{mode}-stress_graph.json"
            obj = json.loads(f.read_text())
            progress = "Verification not started yet" if mode != "fresh-semantic" else "Success"
            obj["records"][0]["semantic"]["hover"] = (
                progress + "\n" + "```dafny\nfunction ValueA(): int\n```")
            f.write_text(json.dumps(obj))
        result = compare(path)
        assert all(x["status"] == "MATCH" for x in result["comparison"]), result
        assert result["volatileVerificationHoverCount"] >= 1
        f = path / "experimental-stress_graph.json"
        obj = json.loads(f.read_text())
        obj["records"][0]["semantic"]["hover"] = obj["records"][0]["semantic"]["hover"].replace(
            "function ValueA(): int", "function ValueA(): bool")
        f.write_text(json.dumps(obj))
        assert any(x["status"] == "DIFFERENCE" for x in compare(path)["comparison"])

        write_traces(path, scenarios=EXTENDED_SCENARIOS)
        assert all(x["status"] == "MATCH" for x in compare(path, ("air_semantic_662",))["comparison"])
        write_traces(path, ("semantic", "experimental", "air_semantic_662"),
                     scenarios=EXTENDED_SCENARIOS)
        assert any(x["status"] == "DIFFERENCE"
                   for x in compare(path, ("air_semantic_662",))["comparison"])
    print("Oracle self-test: clean, corrupt diagnostic/semantic, negative stale-positive calibration, parser mismatch, missing traces, isolated 662 -> PASS")


if __name__ == "__main__":
    run()
