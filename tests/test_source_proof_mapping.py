import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_source_proof_mapping", ROOT / "scripts/validate_source_proof_mapping.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class MappingValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapping = json.loads((ROOT / "research/source-to-proof-mapping.json").read_text())

    def test_repository_mapping_is_valid(self):
        self.assertEqual([], validator.validate(self.mapping, ROOT))

    def test_missing_upstream_anchor_is_rejected(self):
        doc = copy.deepcopy(self.mapping)
        del doc["mappings"][0]["upstream"]
        self.assertTrue(any("upstream: missing anchors" in e for e in validator.validate(doc, ROOT)))

    def test_malformed_source_path_is_rejected(self):
        doc = copy.deepcopy(self.mapping)
        doc["mappings"][0]["upstream"][0]["path"] = "https://example.invalid/Fake.cs"
        self.assertTrue(any("malformed pinned upstream source path" in e for e in validator.validate(doc, ROOT)))

    def test_line_number_anchor_is_rejected(self):
        doc = copy.deepcopy(self.mapping)
        doc["mappings"][0]["upstream"][0]["path"] = "Source/DafnyCore/Resolver/ModuleResolver.cs:18"
        self.assertTrue(any("line-number anchors are forbidden" in e for e in validator.validate(doc, ROOT)))


if __name__ == "__main__":
    unittest.main()
