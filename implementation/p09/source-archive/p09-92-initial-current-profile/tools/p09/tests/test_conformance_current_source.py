from __future__ import annotations

from contextlib import contextmanager
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/p09"))

import conformance_current_source as current
import reference_conformance as matrix_module
import validate_reference_conformance_contract as validator


class ConformanceCurrentSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qualification = json.loads((ROOT / current.QUALIFICATION).read_bytes())
        cls.temporary = tempfile.TemporaryDirectory(prefix="hwpx-agent-p09-92-")
        cls.root = Path(cls.temporary.name)
        paths = [p["path"] for p in cls.qualification["raw_pins"]]
        paths.extend([current.QUALIFICATION, "tools/p09/conformance_current_source.py"])
        for relative in paths:
            target = cls.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    @contextmanager
    def changed(self, relative, change):
        target = self.root / relative
        original = target.read_bytes()
        try:
            replacement = change(original)
            if replacement is None:
                target.unlink()
            else:
                target.write_bytes(replacement)
            yield
        finally:
            target.write_bytes(original)

    def assert_bundle_rejected(self):
        with self.assertRaisesRegex(matrix_module.ConformanceError, "current_source_v2_qualification"):
            current.verify_bundle(self.root)

    def test_actual_original_pipeline_runs_all_fifteen_current_upstreams_without_green(self):
        value = validator.validate(source_profile=current.PROFILE)
        self.assertEqual(value["state"], "pass")
        self.assertEqual(value["upstream_validators_verified"], 15)
        self.assertEqual(value["required_rows"], 53)
        self.assertEqual(value["p09_owned_rows"], 46)
        self.assertEqual(value["p11_deferred_rows"], 7)
        self.assertEqual(value["component_stage_counts"], {"cataloged":7,"unit_passed":35,"integration_passed":11,"oracle_verified":0})
        self.assertEqual(value["green_rows"], 0)
        self.assertEqual(value["actual_hangul"], "not_run")
        self.assertFalse(value["product_complete"])
        self.assertEqual(value["P09_gate"], "OPEN")
        self.assertFalse(value["P10_new_implementation"])

    def test_complete_test_owned_clone_can_run_the_same_cli_pipeline(self):
        run = subprocess.run([sys.executable, "tools/p09/validate_reference_conformance_contract.py", "--current-source-v2"],
                             cwd=self.root, capture_output=True, text=True, check=False, timeout=90)
        self.assertEqual(run.returncode, 0, run.stdout)
        value = json.loads(run.stdout)
        self.assertEqual(value["upstream_validators_verified"], 15)
        self.assertEqual(value["green_rows"], 0)
        self.assertFalse(value["product_complete"])

    def test_original_default_failure_matches_complete_preserved_original(self):
        path = ROOT / "implementation/p09/source-archive/p09-92-pre-conformance-current-source/tools/p09/validate_reference_conformance_contract.py"
        spec = importlib.util.spec_from_file_location("p92_preserved_conformance", path)
        old = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old)
        for module in [old, validator]:
            with self.subTest(module=module.__name__), self.assertRaisesRegex(matrix_module.ConformanceError, "^matrix_drift$"):
                module.validate(run_upstream=False)

    def test_current_pipeline_refuses_upstream_skip(self):
        with self.assertRaisesRegex(matrix_module.ConformanceError, "current_source_upstream_required"):
            validator.validate(source_profile=current.PROFILE, run_upstream=False)

    def test_current_pipeline_refuses_contract_and_matrix_override(self):
        for key in ["contract_override", "matrix_override"]:
            with self.subTest(key=key), self.assertRaisesRegex(matrix_module.ConformanceError, "current_source_overrides_not_admitted"):
                validator.validate(source_profile=current.PROFILE, **{key:{}})

    def test_unknown_profile_and_extra_cli_arguments_fail_closed(self):
        with self.assertRaisesRegex(matrix_module.ConformanceError, "source_profile_unknown"):
            validator.validate(source_profile="current_source_v3")
        for arguments in [["--current-source-v3"], ["--current-source-v2", "--skip-upstream"]]:
            with self.subTest(arguments=arguments):
                run = subprocess.run([sys.executable,"tools/p09/validate_reference_conformance_contract.py",*arguments],
                                     cwd=ROOT,capture_output=True,text=True,check=False,timeout=30)
                self.assertEqual(run.returncode,1)
                self.assertEqual(json.loads(run.stdout)["error"],"source_profile_unknown")

    def test_original_builder_output_and_every_non_component_field_are_preserved(self):
        wrapper = current.verify_bundle(self.root)["matrix_wrapper"]
        current_matrix = wrapper["matrix"]
        self.assertEqual(current_matrix, matrix_module.build_matrix())
        old = matrix_module.load_json(matrix_module.MATRIX)
        changed = []
        for before, after in zip(old["rows"],current_matrix["rows"]):
            self.assertEqual({k:v for k,v in before.items() if k!="component"},
                             {k:v for k,v in after.items() if k!="component"})
            if before!=after:
                changed.append(after["feature_id"])
        self.assertEqual(changed,["REF-021","REF-022","REF-031","REF-032","REF-033","REF-034"])
        self.assertEqual(old["summary"],current_matrix["summary"])

    def test_current_wrapper_green_owner_target_or_required_fixture_tamper_is_rejected(self):
        for keys,replacement in [
            (["matrix","rows",0,"gate_state"],"green"),
            (["matrix","rows",15,"catalog_phase"],"P09"),
            (["matrix","rows",0,"required_fixture_classes"],[]),
            (["matrix","claims","actual_hangul"],True),
            (["matrix","target","build"],"unqualified"),
            (["P09_gate"],"CLOSED"),
        ]:
            with self.subTest(keys=keys):
                def replace(raw):
                    value=json.loads(raw)
                    cursor=value
                    for key in keys[:-1]:cursor=cursor[key]
                    cursor[keys[-1]]=replacement
                    return json.dumps(value).encode()
                with self.changed(current.CURRENT_MATRIX,replace):self.assert_bundle_rejected()

    def test_current_qualification_promotion_or_pin_change_is_rejected(self):
        for keys,replacement in [
            (["claims","product_complete"],True),(["claims","actual_hangul"],True),
            (["gate","P09"],"CLOSED"),(["raw_pin_count"],239),
            (["raw_pins",0,"sha256"],"0"*64),
        ]:
            with self.subTest(keys=keys):
                def replace(raw):
                    value=json.loads(raw);cursor=value
                    for key in keys[:-1]:cursor=cursor[key]
                    cursor[keys[-1]]=replacement
                    return json.dumps(value).encode()
                with self.changed(current.QUALIFICATION,replace):self.assert_bundle_rejected()

    def test_missing_qualification_matrix_script_or_executable_is_rejected(self):
        binary=next(p["path"] for p in self.qualification["raw_pins"] if p["path"].endswith(".exe"))
        for relative in [current.QUALIFICATION,current.CURRENT_MATRIX,current.UPSTREAM_PROFILES[0]["validator"],binary]:
            with self.subTest(relative=relative),self.changed(relative,lambda raw:None):self.assert_bundle_rejected()

    def test_previous_comment_or_twelve_profile_receipt_change_is_rejected(self):
        for pin in self.qualification["component_qualifications"]:
            with self.subTest(relative=pin["path"]),self.changed(pin["path"],lambda raw:raw+b" "):
                self.assert_bundle_rejected()

    def test_frozen_old_contract_qualification_matrix_docs_and_tests_are_still_bound(self):
        paths=[self.qualification["historical_contract"],self.qualification["historical_qualification"],
               self.qualification["historical_matrix"],"tools/p09/tests/test_reference_conformance_contract.py",
               "implementation/p09/P09-11_REFERENCE_CONFORMANCE_REPORT.md"]
        for relative in paths:
            with self.subTest(relative=relative),self.changed(relative,lambda raw:raw+b" "):
                self.assert_bundle_rejected()

    def test_all_fifteen_upstream_script_bytes_are_pinned(self):
        for profile in current.UPSTREAM_PROFILES:
            with self.subTest(validator=profile["validator"]),self.changed(profile["validator"],lambda raw:raw+b" "):
                self.assert_bundle_rejected()

    def test_specs_and_actual_current_source_or_official_file_change_is_rejected(self):
        for relative in ["specs/feature-coverage-matrix.json","specs/capability-contracts.generated.json",
                         "specs/work-breakdown-structure.json","crates/hwpx-package/src/bookmark_hwpx.rs",
                         "fixtures/target-build/official-source-cache/hwpx-owpml-model-145338/OWPML/Class/enumdef.h"]:
            with self.subTest(relative=relative),self.changed(relative,lambda raw:raw+b" "):
                self.assert_bundle_rejected()

    def test_duplicate_wrapper_json_fails_before_any_new_claim(self):
        with self.changed(current.CURRENT_MATRIX,lambda raw:raw.replace(b'"profile_id": "current_source_v2",',
                b'"profile_id": "current_source_v2", "profile_id": "current_source_v2",')):
            self.assert_bundle_rejected()

    def test_upstream_payload_cannot_hide_failed_proof_wrong_schema_or_native_green(self):
        profile=current.UPSTREAM_PROFILES[0]
        payload={"state":"pass","schema_version":profile["expected_schema"],"product_complete":False,
                 "actual_hwpx":"not_run","actual_hangul":"not_run","render":"not_run","automation":"not_run",
                 "differential":"not_run","source_profile":current.PROFILE,"current_source_qualification_verified":True,
                 "current_source_raw_pins":172,"current_source_family":"field_core","p09_01_green":False}
        current.validate_upstream_payload(profile["validator"],payload)
        for key,replacement in [("state","fail"),("schema_version","wrong"),("product_complete",True),
                                ("actual_hangul","pass"),("p09_01_green",True),
                                ("current_source_qualification_verified",False),("current_source_raw_pins",0),
                                ("current_source_family","comment_model")]:
            with self.subTest(key=key),self.assertRaises(matrix_module.ConformanceError):
                changed=copy.deepcopy(payload);changed[key]=replacement
                current.validate_upstream_payload(profile["validator"],changed)

    def test_only_known_original_upstream_commands_and_exact_profiles_are_allowed(self):
        self.assertEqual([p["validator"] for p in current.UPSTREAM_PROFILES],validator.EXPECTED_UPSTREAM)
        self.assertEqual(sum(bool(p["arguments"]) for p in current.UPSTREAM_PROFILES),13)
        for profile in current.UPSTREAM_PROFILES:
            self.assertEqual(current.upstream_arguments(profile["validator"]),profile["arguments"])
        with self.assertRaises(matrix_module.ConformanceError):current.upstream_arguments("tools/p09/unqualified.py")

    def test_complete_raw_pin_set_and_no_native_gate_claims_are_fixed(self):
        self.assertEqual(self.qualification["raw_pin_count"],240)
        self.assertEqual(len(self.qualification["raw_pins"]),240)
        self.assertEqual(len({p["path"] for p in self.qualification["raw_pins"]}),240)
        self.assertEqual(self.qualification["gate"]["P09"],"OPEN")
        self.assertFalse(self.qualification["claims"]["p09_complete"])
        self.assertFalse(self.qualification["claims"]["product_complete"])


if __name__=="__main__":unittest.main()
