from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/p16"
import sys

sys.path.insert(0, str(TOOLS))
import build_universal_package_contract as contract_builder  # noqa: E402
import universal_package as package  # noqa: E402


class UniversalPackageTests(unittest.TestCase):
    def base_entries(self) -> dict[str, bytes]:
        entries, errors = package.read_base_entries()
        self.assertEqual([], errors)
        return entries

    def valid_receipt(self) -> dict[str, object]:
        return {
            "schema_version": "hwpx-agent.p16-registration-receipt/v1",
            "evidence_id": "123e4567-e89b-42d3-a456-426614174000",
            "evidence_kind": "actual_developer_mode_registration",
            "captured_at": "2026-09-05T00:00:00Z",
            "registered_app_id": "plugin_asdk_app_A8b3K9m2Q7z4",
            "endpoint_url": "https://staging.hwpx-agent.invalid/mcp",
            "official_source_lock_sha256": package.OFFICIAL_SOURCE_LOCK_SHA256,
            "user_confirmed": True,
        }

    def test_tracked_base_is_exact_and_valid(self) -> None:
        entries = self.base_entries()
        self.assertEqual(set(package.BASE_ENTRIES), set(entries))
        self.assertEqual(4, len(package.base_snapshot(entries)))

    def test_manifest_rejects_duplicate_keys(self) -> None:
        _, errors = package.load_json_bytes(b'{"name":"a","name":"b"}', "manifest")
        self.assertIn("manifest.duplicate_key", errors)

    def test_extra_entry_is_rejected(self) -> None:
        entries = self.base_entries()
        entries[".app.json"] = b'{"apps":{}}\n'
        self.assertIn("package.entries", package.validate_base_entries(entries))

    def test_manifest_path_escape_and_placeholder_are_rejected(self) -> None:
        entries = self.base_entries()
        manifest = json.loads(entries[".codex-plugin/plugin.json"])
        manifest["interface"]["logo"] = "./../outside.png"
        manifest["description"] = "[TODO: replace this package description before release]"
        entries[".codex-plugin/plugin.json"] = package.canonical_json_bytes(manifest)
        errors = package.validate_base_entries(entries)
        self.assertIn("manifest.interface.logo", errors)
        self.assertIn(".codex-plugin/plugin.json.placeholder", errors)

    def test_png_dimension_tamper_is_rejected(self) -> None:
        entries = self.base_entries()
        tampered = bytearray(entries["assets/icon.png"])
        tampered[16:20] = (127).to_bytes(4, "big")
        entries["assets/icon.png"] = bytes(tampered)
        self.assertIn("assets/icon.png.dimensions", package.validate_base_entries(entries))

    def test_receipt_accepts_only_strict_actual_shape(self) -> None:
        binding, errors = package.validate_registration_receipt(self.valid_receipt())
        self.assertEqual([], errors)
        self.assertIsNotNone(binding)
        assert binding is not None
        self.assertEqual("plugin_asdk_app_A8b3K9m2Q7z4", binding.registered_app_id)

    def test_receipt_rejects_synthetic_placeholder_and_source_drift(self) -> None:
        receipt = self.valid_receipt()
        receipt["evidence_kind"] = "synthetic_test"
        receipt["registered_app_id"] = "plugin_asdk_app_TESTFIXTURE"
        receipt["official_source_lock_sha256"] = "0" * 64
        binding, errors = package.validate_registration_receipt(receipt)
        self.assertIsNone(binding)
        self.assertIn("receipt.evidence_kind", errors)
        self.assertIn("receipt.registered_app_id_placeholder", errors)
        self.assertIn("receipt.official_source_lock_sha256", errors)

    def test_receipt_rejects_endpoint_credentials_query_and_unknown_secret(self) -> None:
        receipt = self.valid_receipt()
        receipt["endpoint_url"] = "https://user:pass@example.invalid/mcp?token=value"
        receipt["api_token"] = "not-a-real-token"
        binding, errors = package.validate_registration_receipt(receipt)
        self.assertIsNone(binding)
        self.assertIn("receipt.fields", errors)
        self.assertIn("receipt.endpoint_url", errors)

    def test_registered_composition_adds_only_manifest_binding(self) -> None:
        entries = self.base_entries()
        binding, errors = package.validate_registration_receipt(self.valid_receipt())
        self.assertEqual([], errors)
        assert binding is not None
        composed, errors = package.compose_entries(entries, binding)
        self.assertEqual([], errors)
        self.assertEqual(set(entries) | {".app.json"}, set(composed))
        manifest = json.loads(composed[".codex-plugin/plugin.json"])
        app_manifest = json.loads(composed[".app.json"])
        self.assertEqual("./.app.json", manifest["apps"])
        self.assertEqual(binding.registered_app_id, app_manifest["apps"]["hwpx-agent"]["id"])
        self.assertNotIn(binding.endpoint_url.encode(), composed[".app.json"])

    def test_direct_binding_cannot_bypass_receipt_validation(self) -> None:
        entries = self.base_entries()
        binding = package.RegistrationBinding(
            "not-a-uuid",
            "plugin_asdk_app_TESTFIXTURE",
            "http://example.invalid/mcp?secret=value",
        )
        composed, errors = package.compose_entries(entries, binding)
        self.assertEqual({}, composed)
        self.assertIn("binding.evidence_id", errors)
        self.assertIn("binding.registered_app_id_placeholder", errors)
        self.assertIn("binding.endpoint_url", errors)

    def test_receipt_loader_rejects_arbitrary_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            receipt_path = Path(temporary) / "receipt.json"
            receipt_path.write_text(json.dumps(self.valid_receipt()), encoding="utf-8")
            binding, errors = package.load_registration_receipt(receipt_path)
            self.assertIsNone(binding)
            self.assertEqual(["receipt.path"], errors)

    def test_source_archive_is_deterministic_and_no_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first.zip"
            second = root / "second.zip"
            result_one, errors = package.publish_archive(first)
            self.assertEqual([], errors)
            result_two, errors = package.publish_archive(second)
            self.assertEqual([], errors)
            assert result_one is not None and result_two is not None
            self.assertEqual(result_one["sha256"], result_two["sha256"])
            self.assertEqual([], package.validate_archive(first, registered=False))
            _, errors = package.publish_archive(first)
            self.assertIn("output.exists", errors)

    def test_registered_archive_is_structurally_valid_but_not_actual_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "registered-fixture.zip"
            binding, errors = package.validate_registration_receipt(self.valid_receipt())
            self.assertEqual([], errors)
            assert binding is not None
            _, errors = package.publish_archive(output, binding=binding)
            self.assertEqual([], errors)
            self.assertEqual([], package.validate_archive(output, registered=True))

    def test_output_inside_source_is_rejected(self) -> None:
        output = package.PACKAGE_ROOT / "forbidden.zip"
        _, errors = package.publish_archive(output)
        self.assertIn("output.inside_source", errors)
        self.assertFalse(output.exists())

    def test_base_source_is_unchanged_after_composition(self) -> None:
        entries = self.base_entries()
        before = package.base_snapshot(entries)
        binding, errors = package.validate_registration_receipt(self.valid_receipt())
        self.assertEqual([], errors)
        assert binding is not None
        _, errors = package.compose_entries(copy.deepcopy(entries), binding)
        self.assertEqual([], errors)
        current, errors = package.read_base_entries()
        self.assertEqual([], errors)
        self.assertEqual(before, package.base_snapshot(current))

    def test_generated_contract_is_exact(self) -> None:
        expected = contract_builder.build_contract()
        actual = json.loads(contract_builder.CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
