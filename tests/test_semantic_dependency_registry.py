import copy, importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('registry_validator',ROOT/'scripts/validate_semantic_dependency_registry.py')
v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
class RegistryTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.doc=json.loads((ROOT/'research/semantic-dependency-registry.json').read_text())
 def test_repository_registry_valid(self): self.assertEqual([],v.validate(self.doc))
 def test_missing_negative_lookup_category_rejected(self):
  d=copy.deepcopy(self.doc); d['entries']=[x for x in d['entries'] if x['id']!='negative-name-lookups']; self.assertTrue(any('missing categories' in x for x in v.validate(d)))
 def test_completeness_claim_rejected(self):
  d=copy.deepcopy(self.doc); d['claim_boundary']='complete and established'; self.assertTrue(any('disclaim completeness' in x for x in v.validate(d)))
 def test_missing_fail_closed_policy_rejected(self):
  d=copy.deepcopy(self.doc); d['entries'][0]['invalidation_fail_closed']=''; self.assertTrue(any('invalidation_fail_closed' in x for x in v.validate(d)))
if __name__=='__main__': unittest.main()
