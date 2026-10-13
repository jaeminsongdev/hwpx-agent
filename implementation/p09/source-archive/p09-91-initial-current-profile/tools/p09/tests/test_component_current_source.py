from __future__ import annotations

from contextlib import contextmanager
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.p09 import component_current_source as current


class ComponentCurrentSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repository = Path(__file__).resolve().parents[3]
        cls.receipt = json.loads((cls.repository / current.QUALIFICATION).read_bytes())
        cls.modules = {name: importlib.import_module("tools.p09.validate_" + name + "_contract")
                       for name in current.IMPLEMENTATION_SHA256}
        # 테스트 소유 복사본 하나만 만들고 매 변조 후 원래 바이트로 복구한다.
        cls.temporary = tempfile.TemporaryDirectory(prefix="hwpx-agent-p09-91-")
        cls.root = Path(cls.temporary.name)
        for relative in [current.QUALIFICATION, *(p["path"] for p in cls.receipt["raw_pins"])]:
            target = cls.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((cls.repository / relative).read_bytes())

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

    def assert_rejected(self, family="field_core", expected=None):
        value = self.modules[family].validate(self.root, source_profile=current.PROFILE)
        self.assertEqual(value["state"], "fail", value)
        if expected:
            self.assertIn(expected, value["errors"])
        self.assertFalse(value.get("product_complete", False))
        self.assertFalse(value.get("native_or_product_gate_promoted", False))
        self.assertEqual(value.get("actual_hangul", "not_run"), "not_run")
        if not value.get("current_source_qualification_verified", False):
            self.assertEqual(value.get("current_source_raw_pins", 0), 0)

    def test_all_twelve_current_profiles_pass_without_native_or_product_promotion(self):
        for family, validator in self.modules.items():
            with self.subTest(family=family):
                value = validator.validate(self.root, source_profile=current.PROFILE)
                self.assertEqual(value["state"], "pass", value)
                self.assertEqual(value["source_profile"], current.PROFILE)
                self.assertTrue(value["current_source_qualification_verified"])
                self.assertEqual(value["current_source_raw_pins"], 171)
                self.assertFalse(value["native_or_product_gate_promoted"])
                self.assertFalse(value["product_complete"])
                self.assertEqual(value.get("actual_hangul", "not_run"), "not_run")
                for key, item in value.items():
                    if key.endswith("_green") or key == "green_rows":
                        self.assertFalse(item)

    def test_all_historical_default_result_fields_match_preserved_original_validators(self):
        for family, validator in self.modules.items():
            with self.subTest(family=family):
                archive = self.repository / "implementation/p09/source-archive/p09-91-pre-component-current-source" / (
                    "tools/p09/validate_" + family + "_contract.py")
                spec = importlib.util.spec_from_file_location("p91_historical_test_" + family, archive)
                original = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(original)
                old = original.validate(self.repository)
                new = validator.validate(self.repository)
                self.assertEqual(new, old)
                self.assertEqual(new["state"], "fail")
                self.assertNotIn("source_profile", new)

    def test_all_families_reject_unknown_profiles(self):
        for family, validator in self.modules.items():
            with self.subTest(family=family):
                value = validator.validate(self.root, source_profile="current_source_v3")
                self.assertEqual(value["errors"], ["source_profile_unknown"])
                self.assertEqual(value["state"], "fail")

    def test_original_contract_schema_guards_are_not_filtered(self):
        for family, proof in self.receipt["families"].items():
            with self.subTest(family=family):
                def replace(raw):
                    value = json.loads(raw)
                    value["schema_version"] = "unaccepted"
                    return json.dumps(value).encode()
                with self.changed(proof["historical_contract"], replace):
                    self.assert_rejected(family, "current_source_v2_qualification")

    def test_original_qualification_guards_are_not_rewritten(self):
        for family, proof in self.receipt["families"].items():
            with self.subTest(family=family):
                def replace(raw):
                    value = json.loads(raw)
                    value["schema_version"] = "unaccepted"
                    return json.dumps(value).encode()
                with self.changed(proof["historical_qualification"], replace):
                    self.assert_rejected(family, "current_source_v2_qualification")

    def test_every_current_implementation_file_is_checked(self):
        owners = {}
        for family, mapping in current.IMPLEMENTATION_SHA256.items():
            for relative in mapping:
                owners.setdefault(relative, family)
        for relative, family in owners.items():
            with self.subTest(relative=relative), self.changed(relative, lambda raw: raw + b" "):
                self.assert_rejected(family, "current_source_v2_qualification")

    def test_every_authoritative_source_is_checked(self):
        relatives = self.receipt["families"]["field_core"]["authoritative_source_sha256"]
        for relative in relatives:
            with self.subTest(relative=relative), self.changed(relative, lambda raw: raw + b" "):
                self.assert_rejected(expected="current_source_v2_qualification")

    def test_all_sixty_eight_official_sources_are_checked_as_raw_bytes(self):
        pins = [p for p in self.receipt["raw_pins"] if p["path"].startswith(current.OFFICIAL_CACHE)]
        self.assertEqual(len(pins), 68)
        for pin in pins:
            with self.subTest(relative=pin["path"]), self.changed(pin["path"], lambda raw: raw + b" "):
                self.assert_rejected(expected="current_source_v2_qualification")

    def test_all_fourteen_current_rust_executables_are_checked(self):
        pins = [p for p in self.receipt["raw_pins"] if p["path"].endswith(".exe")]
        self.assertEqual(len(pins), 14)
        for pin in pins:
            with self.subTest(relative=pin["path"]), self.changed(pin["path"],
                    lambda raw: bytes([raw[0] ^ 1]) + raw[1:]):
                self.assert_rejected(expected="current_source_v2_qualification")

    def test_missing_receipt_or_official_file_or_executable_fails(self):
        binary = next(p["path"] for p in self.receipt["raw_pins"] if p["path"].endswith(".exe"))
        for relative in [current.QUALIFICATION, current.OFFICIAL_CACHE + "OWPML/Class/enumdef.h", binary]:
            with self.subTest(relative=relative), self.changed(relative, lambda raw: None):
                self.assert_rejected(expected="current_source_v2_qualification")

    def test_receipt_native_gate_or_test_promotion_fails_exact_fingerprint(self):
        for keys, replacement in [
            (["gate", "P09"], "CLOSED"), (["claims", "product_complete"], True),
            (["claims", "actual_hangul"], True), (["claims", "P10_new_implementation"], True),
            (["Rust_component_regression", "total_passed"], 138),
        ]:
            with self.subTest(keys=keys):
                def replace(raw):
                    value = json.loads(raw)
                    cursor = value
                    for key in keys[:-1]:
                        cursor = cursor[key]
                    cursor[keys[-1]] = replacement
                    return json.dumps(value).encode()
                with self.changed(current.QUALIFICATION, replace):
                    self.assert_rejected(expected="current_source_v2_qualification")

    def test_duplicate_receipt_json_is_rejected(self):
        with self.changed(current.QUALIFICATION, lambda raw: raw.replace(
                b'"profile_id": "current_source_v2",',
                b'"profile_id": "current_source_v2", "profile_id": "current_source_v2",')):
            self.assert_rejected(expected="current_source_v2_qualification")
        with self.assertRaises(ValueError):
            json.loads('{"a":1,"a":1}', object_pairs_hook=current.duplicate_guard)

    def test_raw_line_endings_cannot_be_hidden_by_canonical_hash(self):
        relative = "crates/domain-ir/src/citation.rs"
        original = (self.root / relative).read_bytes()
        with self.changed(relative, lambda raw: raw.replace(b"\n", b"\r\n")):
            self.assertEqual(current.canonical((self.root / relative).read_bytes()), current.canonical(original))
            self.assert_rejected("citation", "current_source_v2_qualification")

    def test_reference_auxiliary_bom_convention_is_explicit_not_fallback(self):
        relative = "OWPML/Class/enumdef.h"
        raw = (self.root / (current.OFFICIAL_CACHE + relative)).read_bytes()
        self.assertTrue(raw.startswith(bytes.fromhex("EFBBBF")))
        auxiliary = self.receipt["families"]["reference_auxiliary"]
        form = self.receipt["families"]["form_control"]
        self.assertEqual(current.canonical(raw, remove_bom=True), auxiliary["official_source_sha256"][relative])
        self.assertEqual(current.canonical(raw), form["official_source_sha256"][relative])
        self.assertNotEqual(current.canonical(raw), auxiliary["official_source_sha256"][relative])

    def test_bom_removal_fails_raw_pin_even_if_historical_auxiliary_hash_still_matches(self):
        relative = current.OFFICIAL_CACHE + "OWPML/Class/enumdef.h"
        expected = self.receipt["families"]["reference_auxiliary"]["official_source_sha256"]["OWPML/Class/enumdef.h"]
        with self.changed(relative, lambda raw: raw[3:]):
            self.assertEqual(current.canonical((self.root / relative).read_bytes(), remove_bom=True), expected)
            self.assert_rejected("reference_auxiliary", "current_source_v2_qualification")

    def test_current_overrides_are_disallowed_and_legacy_override_interface_is_retained(self):
        for family in ["bookmark_hwpx", "note_hwpx"]:
            with self.subTest(family=family):
                validator = self.modules[family]
                contract = json.loads((self.root / validator.CONTRACT).read_bytes())
                value = validator.validate(self.root, source_profile=current.PROFILE, contract_override=contract)
                self.assertEqual(value["state"], "fail")
                self.assertIn("current_source_override_not_admitted", value["errors"])
                self.assertNotIn("current_source_override_not_admitted", validator.validate(
                    self.root, contract_override=contract)["errors"])

    def test_exact_cli_profile_does_not_accept_extra_flags(self):
        self.assertEqual(current.cli_profile([]), "historical_v1")
        self.assertEqual(current.cli_profile(["--current-source-v2"]), current.PROFILE)
        for arguments in [["--current-source-v3"], ["--current-source-v2", "--allow-drift"]]:
            with self.subTest(arguments=arguments):
                run = subprocess.run([sys.executable, "tools/p09/validate_field_core_contract.py", *arguments],
                                     cwd=self.repository, capture_output=True, text=True, check=False, timeout=30)
                self.assertEqual(run.returncode, 1)
                self.assertEqual(json.loads(run.stdout)["errors"], ["source_profile_unknown"])

    def test_original_receipt_and_full_coverage_are_fixed(self):
        raw = (self.root / current.QUALIFICATION).read_bytes()
        self.assertEqual(len(raw), current.QUALIFICATION_BYTES)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), current.QUALIFICATION_SHA256)
        self.assertEqual(len(self.receipt["raw_pins"]), 171)
        self.assertEqual(len({p["path"] for p in self.receipt["raw_pins"]}), 171)
        self.assertEqual(sum(p["component_tests"] for p in self.receipt["families"].values()), 128)
        self.assertEqual(self.receipt["Rust_component_regression"]["total_passed"], 137)


if __name__ == "__main__":
    unittest.main()
