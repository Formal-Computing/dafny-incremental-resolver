import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "nonempty_feasibility_validator", ROOT / "scripts/validate_nonempty_feasibility.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class NonemptyFeasibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads((ROOT / "research/nonempty-feasibility-2026-11-09.json").read_text())

    def test_repository_audit_valid(self):
        self.assertEqual([], validator.validate(self.audit))

    def test_go_recommendation_rejected(self):
        audit = copy.deepcopy(self.audit)
        audit["recommendation"] = "GO"
        self.assertTrue(any("NO-GO" in error for error in validator.validate(audit)))

    def test_missing_dependency_rejected(self):
        audit = copy.deepcopy(self.audit)
        audit["dependencies"].remove(25)
        self.assertTrue(any("dependencies" in error for error in validator.validate(audit)))

    def test_experiment_cannot_be_claimed_as_run(self):
        audit = copy.deepcopy(self.audit)
        audit["minimal_experiment"]["mode"] = "experiment completed"
        self.assertTrue(any("not run" in error for error in validator.validate(audit)))


if __name__ == "__main__":
    unittest.main()
