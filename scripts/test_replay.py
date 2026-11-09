"""Stdlib contract tests for replay planning and process safety."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

PATH=Path(__file__).with_name("replay.py")
SPEC=importlib.util.spec_from_file_location("replay",PATH)
replay=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(replay)

class ReplayTests(unittest.TestCase):
    def test_lsp_is_unavailable_and_unsafe_flag_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNAVAILABLE"):
            replay.plan("lsp-differential")
        self.assertEqual(2,replay.main(["dry-run","lsp-differential","--allow-experimental-unsafe"]))

    def test_stage_environment_contract(self):
        with mock.patch.object(replay,"preflight",return_value=["patch"]):
            for stage in ("safe-revalidation","restricted-export","terminal-verifier"):
                steps=replay.plan(stage,Path("/fake"))
                tests=[s for s in steps if s["argv"][1:2]==["test"]]
                self.assertTrue(tests,stage)
                for step in tests:
                    env=step["environment"]
                    if "dotnet" not in step["argv"]: continue
                    self.assertIn("DAFNY_RESEARCH_MODE",env)
                    self.assertIn("DAFNY_RESEARCH_OUTPUT_DIR",env)
                    self.assertNotIn("DAFNY_RESEARCH_UNSAFE_CROSS_REVISION_REUSE",env)
                    self.assertFalse(any("UNSAFE" in k for k in env))
            safe=replay.plan("safe-revalidation",Path("/fake"))
            self.assertTrue(any("compare_safe_revalidation.py" in s["argv"][1] for s in safe))
            export=replay.plan("restricted-export",Path("/fake"))
            self.assertTrue(any("compare_immutable_export.py" in s["argv"][1] for s in export))
            self.assertTrue(any("assert_export_contract.py" in s["argv"][1] for s in export))

    def test_exact_workflow_filters(self):
        with mock.patch.object(replay,"preflight",return_value=[]):
            plans={s:replay.plan(s,Path("/fake")) for s in ("safe-revalidation","restricted-export","terminal-verifier")}
        filters=[a[-1] for ps in plans.values() for p in ps for a in [p["argv"]] if "--filter" in a]
        self.assertIn("FullyQualifiedName~CachingTest.ResearchDifferentialTrace",filters)
        self.assertIn("FullyQualifiedName~VerificationStatusTest.ResearchVerificationOutcomeTrace",filters)
        self.assertIn("FullyQualifiedName~CachingTest.ResearchExportSummaryDifferentialTrace",filters)
        self.assertNotIn("FullyQualifiedName~CachingTest.ResearchExportSummaryActuallySkipsResolver",filters)
        self.assertNotIn("FullyQualifiedName~VerificationStatusTest.ResearchVerificationOutcomeTrace|FullyQualifiedName~CachingTest.ResearchDifferentialTrace",filters)

    def test_wrong_sha_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(replay,"git",side_effect=[mock.Mock(returncode=0),mock.Mock(stdout="wrong\n")]):
                with self.assertRaisesRegex(ValueError,"pinned Dafny checkout"):
                    replay.preflight(Path(d))

    def test_missing_binary_creates_failure_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(replay,"plan",side_effect=ValueError("test DLL missing")):
                code=replay.main(["execute","safe-revalidation","--dafny",d,"--output",d])
            self.assertEqual(2,code)
            manifests=list(Path(d).glob("*/run-manifest.json")); self.assertEqual(1,len(manifests))
            m=json.loads(manifests[0].read_text())
            self.assertEqual(2,m["exit_code"]); self.assertIn("test DLL missing",m["preflight_error"])
            self.assertTrue((manifests[0].parent/"stdout.log").exists())
            self.assertTrue((manifests[0].parent/"stderr.log").exists())
            self.assertNotIn("TOKEN",manifests[0].read_text())

    def test_dry_run_never_launches_processes(self):
        with mock.patch.object(replay.shutil,"which",return_value="/mock/dotnet"), mock.patch.object(replay.subprocess,"run",side_effect=AssertionError("process launched")):
            self.assertEqual(0,replay.main(["dry-run","smoke"]))

if __name__=="__main__": unittest.main()
