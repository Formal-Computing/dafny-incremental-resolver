"""Standard-library tests for the archived evidence completeness gate."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_evidence_bundle import stable_hover, validate


class EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config_path = self.root / "config.json"
        self.config = {
            "bundle_id": "test", "bundle_root": ".", "group_glob": "*.json",
            "ignore_files": ["config.json", "report.json"], "known_incomplete": [], "caveats": [],
            "observations": [], "comparisons": [],
            "minimum_comparisons": {"diagnostics": 1, "definition_typed_hover": 1, "terminal_verification": 1},
        }
        for mode in ("oracle", "candidate"):
            for scenario, field, val in (
                ("diff", "diagnostics", []),
                ("diff", "semantic", {"definitions": [{"uri": "file:///x"}], "hover": "```dafny\nmethod M()\n```"}),
                ("proof", "verification", [{"outcome": "Correct", "from": [0, 0], "to": [0, 4]}]),
            ):
                name = f"{mode}-{scenario}-{field}.json"
                record = {"revision": 0, "source": "program"}
                record[field] = copy.deepcopy(val)
                self.write(name, {"mode": mode, "scenario": scenario, "records": [record]})
                self.config["observations"].append({"path": name, "mode": mode, "scenario": scenario, "revisions": 1})
        for field, scenario in (("diagnostics", "diff"), ("semantic", "diff"), ("verification", "proof")):
            left, right = f"oracle-{scenario}-{field}.json", f"candidate-{scenario}-{field}.json"
            kind = {"diagnostics":"diagnostics", "semantic":"definition_typed_hover", "verification":"terminal_verification"}[field]
            self.config["comparisons"].append({"left":left,"right":right,"kind":kind})
        self.save_config()

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, data):
        (self.root / name).write_text(json.dumps(data), encoding="utf-8")

    def save_config(self):
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")

    def test_complete_informative_bundle_passes(self):
        report = validate(self.config_path)
        self.assertEqual("PASS", report["status"])
        self.assertFalse(report["bundle"].startswith("/"), "Report exposed machine-specific absolute path")
        self.assertEqual({"diagnostics":1,"definition_typed_hover":1,"terminal_verification":1}, report["comparison_counts"])

    def test_missing_observation_and_untracked_file_fail(self):
        (self.root / "candidate-proof-verification.json").unlink()
        (self.root / "omitted-result-group.json").write_text("{}")
        self.assertEqual("FAIL", validate(self.config_path)["status"])

    def test_empty_semantic_hover_fails_informativeness(self):
        path = self.root / "candidate-diff-semantic.json"
        obj = json.loads(path.read_text())
        obj["records"][0]["semantic"]["hover"] = ""
        self.write(path.name, obj)
        self.assertIn("NONINFORMATIVE_SEMANTIC", {e["status"] for e in validate(self.config_path)["errors"]})

    def test_corrupted_terminal_outcome_is_not_misdiagnosed_as_resolver_error(self):
        path = self.root / "candidate-proof-verification.json"
        obj = json.loads(path.read_text())
        obj["records"][0]["verification"][0]["outcome"] = "Error"
        self.write(path.name, obj)
        # Deliberate corruption of an otherwise passing fixture must be detected.
        report = validate(self.config_path)
        self.assertIn("VERIFICATION_DIFFERENCE", {e["status"] for e in report["errors"]})

    def test_raw_progress_changes_are_preserved_but_stable_metric_ignores_progress(self):
        raw_a = "```dafny\nmethod M()\n```\nVerified at 1/2"
        raw_b = "```dafny\nmethod M()\n```\nVerified at 2/2"
        self.assertNotEqual(raw_a, raw_b)
        self.assertEqual(stable_hover(raw_a), stable_hover(raw_b))


if __name__ == "__main__":
    unittest.main()
