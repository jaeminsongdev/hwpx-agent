from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.p09 import comment_current_source as current
from tools.p09 import validate_comment_model_contract as validator


@contextmanager
def isolated_current_files():
    # 테스트가 소유한 임시 복사본만 변조하며 저장소 원본은 읽기만 한다.
    receipt = json.loads((validator.ROOT / current.QUALIFICATION).read_bytes())
    with tempfile.TemporaryDirectory(prefix="hwpx-agent-p09-90-") as directory:
        root = Path(directory)
        for relative in [current.QUALIFICATION, *(pin["path"] for pin in receipt["raw_pins"])]:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((validator.ROOT / relative).read_bytes())
        yield root


def replace_json(root: Path, relative: str, keys: list[str | int], replacement):
    target = root / relative
    value = json.loads(target.read_bytes())
    cursor = value
    for key in keys[:-1]:
        cursor = cursor[key]
    cursor[keys[-1]] = replacement
    target.write_text(json.dumps(value), encoding="utf-8")


class CommentCurrentSourceTests(unittest.TestCase):
    def current_result(self, root: Path = validator.ROOT):
        return validator.validate(root, source_profile=current.PROFILE)

    def assert_rejected(self, root: Path, error: str | None = None):
        value = self.current_result(root)
        self.assertEqual(value["state"], "fail", value)
        if error:
            self.assertIn(error, value["errors"])
        self.assertFalse(value["p09_04_green"])
        self.assertFalse(value["product_complete"])
        self.assertEqual(value["actual_hangul"], "not_run")
        self.assertEqual(value["native_semantic_bindings"], "unverified")
        if not value.get("current_source_qualification_verified", False):
            self.assertEqual(value.get("current_source_raw_pins", 0), 0)
            self.assertEqual(value.get("current_component_Rust_tests", 0), 0)

    def test_explicit_current_profile_checks_same_five_capabilities_and_no_native_promotion(self):
        value = self.current_result()
        self.assertEqual(value["state"], "pass", value)
        self.assertEqual(value["source_profile"], "current_source_v2")
        self.assertTrue(value["historical_source_qualification_verified"])
        self.assertTrue(value["current_source_qualification_verified"])
        self.assertEqual(value["current_source_raw_pins"], 32)
        self.assertEqual(value["current_component_Rust_tests"], 11)
        self.assertEqual(value["capabilities"], 5)
        self.assertEqual(value["official_source_files"], 17)
        self.assertEqual(value["p11_comment_delete"], "excluded")
        self.assertEqual(value["native_semantic_bindings"], "unverified")
        for key in ["direct_hwpx", "actual_hwpx", "actual_hangul", "render", "automation", "differential"]:
            self.assertEqual(value[key], "not_run")
        self.assertFalse(value["p09_04_green"])
        self.assertFalse(value["product_complete"])

    def test_historical_default_failure_and_exact_old_hashes_remain(self):
        value = validator.validate()
        self.assertEqual(value["errors"], ["implementation_digest"])
        self.assertEqual(value["state"], "fail")
        self.assertNotIn("source_profile", value)
        self.assertEqual(value["schema_version"], "hwpx-agent.p09-comment-model-validation/v1")
        receipt = json.loads((validator.ROOT / validator.QUALIFICATION).read_bytes())
        self.assertEqual(receipt["implementation_sha256"], validator.IMPLEMENTATION_SHA256)
        changed = [path for path in current.IMPLEMENTATION_SHA256
                   if current.IMPLEMENTATION_SHA256[path] != validator.IMPLEMENTATION_SHA256[path]]
        self.assertEqual(changed, ["crates/domain-ir/src/lib.rs"])

    def test_unknown_profile_fails_without_fallback(self):
        for profile in ["current", "current_source_v3", "", "historical_v2"]:
            with self.subTest(profile=profile):
                value = validator.validate(source_profile=profile)
                self.assertEqual(value["errors"], ["source_profile_unknown"])
                self.assertEqual(value["state"], "fail")

    def test_cli_requires_exact_explicit_flag(self):
        for arguments, expected_exit, expected_state in [
            ([], 1, "fail"), (["--current-source-v2"], 0, "pass"),
            (["--current-source-v2", "--allow-drift"], 1, "fail"),
            (["--current-source-v3"], 1, "fail"),
        ]:
            with self.subTest(arguments=arguments):
                run = subprocess.run(
                    [sys.executable, str(validator.ROOT / "tools/p09/validate_comment_model_contract.py"), *arguments],
                    cwd=validator.ROOT, capture_output=True, text=True, check=False, timeout=30,
                )
                self.assertEqual(run.returncode, expected_exit)
                self.assertEqual(json.loads(run.stdout)["state"], expected_state)

    def test_original_capability_and_native_structure_checks_still_reject(self):
        cases = [
            (["capability_features", "REF-030"], "ref.comment_delete", "capability_mapping"),
            (["excluded_capabilities", "review.comment_delete"], "P09", "excluded_capability"),
            (["official_model", "exact_native_structures", 1], "comment", "official_model"),
            (["official_model", "semantic_binding"], "verified", "official_model"),
        ]
        for keys, replacement, error in cases:
            with self.subTest(keys=keys), isolated_current_files() as root:
                replace_json(root, validator.CONTRACT, keys, replacement)
                self.assert_rejected(root, error)

    def test_original_state_binding_and_failure_policy_guards_still_reject(self):
        for keys, replacement, error in [
            (["state_binding", "preservation"], "allow_any_change", "state_binding"),
            (["failure_policy", 0], "skip_limits", "failure_policy"),
            (["model"], "hwpx-agent.comment-model/v2", "model"),
        ]:
            with self.subTest(keys=keys), isolated_current_files() as root:
                replace_json(root, validator.CONTRACT, keys, replacement)
                self.assert_rejected(root, error)

    def test_original_claim_and_gate_promotion_still_reject(self):
        for keys, replacement, error in [
            (["evidence_boundary", "native_author_time_binding_verified"], True, "evidence_boundary"),
            (["evidence_boundary", "product_complete"], True, "evidence_boundary"),
            (["gate_decision", "actual_target"], "pass", "gate_decision"),
        ]:
            with self.subTest(keys=keys), isolated_current_files() as root:
                replace_json(root, validator.CONTRACT, keys, replacement)
                self.assert_rejected(root, error)

    def test_historical_qualification_guards_still_reject(self):
        for keys, replacement, error in [
            (["claims", "p09_complete"], True, "qualification_claims"),
            (["tests", "licensed_application_used"], True, "qualification_tests"),
            (["implementation_sha256", "crates/domain-ir/src/lib.rs"],
             current.IMPLEMENTATION_SHA256["crates/domain-ir/src/lib.rs"], "qualification_implementation"),
            (["official_model", "qualified_facts", "comment_delete_owner"], "P09", "qualification_official_facts"),
        ]:
            with self.subTest(keys=keys), isolated_current_files() as root:
                replace_json(root, validator.QUALIFICATION, keys, replacement)
                self.assert_rejected(root, error)

    def test_all_authoritative_sources_are_physically_checked(self):
        for relative in validator.SOURCE_SHA256:
            with self.subTest(relative=relative), isolated_current_files() as root:
                target = root / relative
                target.write_bytes(target.read_bytes() + b" ")
                self.assert_rejected(root, "source_lock_digest")

    def test_all_current_implementation_files_are_physically_checked(self):
        for relative in current.IMPLEMENTATION_SHA256:
            with self.subTest(relative=relative), isolated_current_files() as root:
                target = root / relative
                target.write_bytes(target.read_bytes() + b" ")
                self.assert_rejected(root, "implementation_digest")

    def test_raw_drift_is_not_hidden_by_canonical_line_endings(self):
        relative = "crates/domain-ir/src/comment_model.rs"
        with isolated_current_files() as root:
            target = root / relative
            target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))
            self.assertEqual(current.canonical_digest(root, relative), current.IMPLEMENTATION_SHA256[relative])
            self.assert_rejected(root, "current_source_v2_qualification")

    def test_all_seventeen_official_source_files_are_physically_checked(self):
        for relative in validator.OFFICIAL_SOURCE_SHA256:
            with self.subTest(relative=relative), isolated_current_files() as root:
                target = root / (current.OFFICIAL_CACHE + relative)
                target.write_bytes(target.read_bytes() + b" ")
                self.assert_rejected(root, "current_source_v2_qualification")

    def test_missing_official_source_fails(self):
        with isolated_current_files() as root:
            (root / (current.OFFICIAL_CACHE + "OWPML/Class/Para/fieldBegin.cpp")).unlink()
            self.assert_rejected(root, "current_source_v2_qualification")

    def test_current_receipt_tamper_and_native_promotion_fail_exact_receipt(self):
        for keys, replacement in [
            (["gate", "P09"], "CLOSED"), (["claims", "product_complete"], True),
            (["claims", "native_author_time_binding_verified"], True),
            (["Rust_component_regression", "total_passed"], 12),
            (["official_commit"], "0" * 40), (["raw_pins", 0, "sha256"], "0" * 64),
        ]:
            with self.subTest(keys=keys), isolated_current_files() as root:
                replace_json(root, current.QUALIFICATION, keys, replacement)
                self.assert_rejected(root, "current_source_v2_qualification")

    def test_duplicate_json_and_replaced_receipt_are_not_admitted(self):
        with isolated_current_files() as root:
            target = root / current.QUALIFICATION
            text = target.read_text(encoding="utf-8")
            target.write_text(text.replace('"profile_id": "current_source_v2",',
                                          '"profile_id": "current_source_v2",\n"profile_id":"current_source_v2",'),
                              encoding="utf-8")
            self.assert_rejected(root, "current_source_v2_qualification")
        with self.assertRaises(current.CurrentSourceError):
            json.loads('{"key":1,"key":1}', object_pairs_hook=current.duplicate_guard)

    def test_missing_either_current_rust_executable_fails(self):
        receipt = json.loads((validator.ROOT / current.QUALIFICATION).read_bytes())
        binaries = [p for p in receipt["raw_pins"] if p["path"].endswith(".exe")]
        self.assertEqual(len(binaries), 2)
        for pin in binaries:
            with self.subTest(path=pin["path"]), isolated_current_files() as root:
                (root / pin["path"]).unlink()
                self.assert_rejected(root, "current_source_v2_qualification")

    def test_changed_current_rust_executable_fails(self):
        receipt = json.loads((validator.ROOT / current.QUALIFICATION).read_bytes())
        for pin in [p for p in receipt["raw_pins"] if p["path"].endswith(".exe")]:
            with self.subTest(path=pin["path"]), isolated_current_files() as root:
                target = root / pin["path"]
                data = target.read_bytes()
                target.write_bytes(bytes([data[0] ^ 1]) + data[1:])
                self.assert_rejected(root, "current_source_v2_qualification")

    def test_historical_document_bytes_cannot_be_rewritten_under_old_markers(self):
        for relative in [validator.MIGRATION, validator.POLICY, validator.REPORT]:
            with self.subTest(relative=relative), isolated_current_files() as root:
                target = root / relative
                target.write_bytes(target.read_bytes() + b" ")
                self.assert_rejected(root, "current_source_v2_qualification")

    def test_missing_current_receipt_fails_without_legacy_fallback(self):
        with isolated_current_files() as root:
            (root / current.QUALIFICATION).unlink()
            self.assert_rejected(root, "current_source_v2_qualification")

    def test_bounded_path_rejects_absolute_traversal_and_windows_aliases(self):
        for relative in ["", "/outside", "../outside", "a/../outside", "a/./b", "a//b", "C:/outside", "a\\b"]:
            with self.subTest(relative=relative), self.assertRaises(current.CurrentSourceError):
                current.bounded_file(validator.ROOT, relative)

    def test_bounded_file_and_pin_shape_size_reject(self):
        with isolated_current_files() as root:
            with self.assertRaises(current.CurrentSourceError):
                current.bounded_file(root, current.QUALIFICATION, maximum=1)
            for pin in [{}, {"path":current.QUALIFICATION, "bytes":True, "sha256":"0" * 64},
                        {"path":current.QUALIFICATION, "bytes":0, "sha256":"0" * 64},
                        {"path":current.QUALIFICATION, "bytes":current.QUALIFICATION_BYTES, "sha256":"0" * 64}]:
                with self.subTest(pin_shape=list(pin)), self.assertRaises(current.CurrentSourceError):
                    current.verify_pin(root, pin)

    def test_official_canonicalization_preserves_utf8_bom(self):
        relative = "OWPML/Class/Para/hiddenComment.cpp"
        raw = current.bounded_file(validator.ROOT, current.OFFICIAL_CACHE + relative)
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(current.canonical_digest(validator.ROOT, current.OFFICIAL_CACHE + relative),
                         validator.OFFICIAL_SOURCE_SHA256[relative])
        self.assertNotEqual(hashlib.sha256(raw[3:]).hexdigest(), validator.OFFICIAL_SOURCE_SHA256[relative])


if __name__ == "__main__":
    unittest.main()
