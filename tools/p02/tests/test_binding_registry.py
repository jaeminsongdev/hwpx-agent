from __future__ import annotations

import csv
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import yaml

from tools.p02.build_bindings import BindingConfig, run
from tools.p02.extract_help import ExtractionError
from tools.p02.review_capabilities import MATRIX_FIELDS
from tools.p02.verify_binding_registry import verify

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class BindingRegistryTests(unittest.TestCase):
    def write_fixture(
        self, root: Path, license_state: str = "public_reference"
    ) -> BindingConfig:
        source_lock_id = "binding-test-lock"
        source_id = "automation-source"
        source_sha256 = "a" * 64
        record = {
            "schema_version": "hwpx-agent.source-record/v1",
            "record_id": "automation.copy",
            "source_lock_id": source_lock_id,
            "source_id": source_id,
            "source_sha256": source_sha256,
            "source_kind": "action_table",
            "locator": {
                "kind": "automation_item",
                "value": "action_table/page:1",
                "section": "Action Table",
                "anchor": "Copy",
            },
            "original_name": "Copy",
            "description_ko": "복사",
            "parameters": [
                {
                    "ordinal": 0,
                    "original_name": "-",
                    "declared_type": "ParameterSet ID",
                    "direction": "unknown",
                    "required": None,
                    "description_ko": None,
                }
            ],
            "availability": {
                "product": "hancom_hangul",
                "target_profile_id": None,
                "minimum_version": None,
                "maximum_version": None,
                "locales": ["ko-KR"],
                "support_scope": "documentation_only",
            },
            "extraction": {
                "extractor_id": "binding-test-source",
                "extractor_version": "0.1.0",
                "record_ordinal": 0,
            },
        }
        automation_content = (
            json.dumps([record], ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        automation_records = root / "automation.json"
        automation_records.write_bytes(automation_content)
        automation_sha256 = hashlib.sha256(automation_content).hexdigest()
        source_lock = root / "source-lock.json"
        source_lock.write_text(
            json.dumps(
                {
                    "schema_version": "hwpx-agent.source-lock/v2",
                    "source_lock_id": source_lock_id,
                    "sources": [
                        {
                            "source_id": source_id,
                            "sha256": source_sha256,
                            "license_state": license_state,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        matrix = root / "matrix.csv"
        rows = [
            {
                "feature_id": "EDIT-001",
                "domain": "편집",
                "scope_class": "artifact_semantics",
                "feature_ko": "복사",
                "capability_id": "edit.copy",
                "semantic_operation": "복사",
                "document_ir": "Selection",
                "preferred_backend": "desktop_automation",
                "fallback_backend": "direct_hwpx",
                "support_level": "HYBRID",
                "phase": "P05",
                "validation": "semantic_diff",
                "permission": "document.write",
                "source_group": "synthetic",
                "notes": "",
            },
            {
                "feature_id": "EDIT-002",
                "domain": "편집",
                "scope_class": "artifact_semantics",
                "feature_ko": "붙여넣기",
                "capability_id": "edit.paste",
                "semantic_operation": "붙여넣기",
                "document_ir": "Selection",
                "preferred_backend": "desktop_automation",
                "fallback_backend": "direct_hwpx",
                "support_level": "AUTOMATION_FULL",
                "phase": "P05",
                "validation": "semantic_diff",
                "permission": "document.write",
                "source_group": "synthetic",
                "notes": "",
            },
            {
                "feature_id": "EDIT-003",
                "domain": "편집",
                "scope_class": "artifact_semantics",
                "feature_ko": "직접 기능",
                "capability_id": "edit.direct_only",
                "semantic_operation": "직접 기능",
                "document_ir": "Selection",
                "preferred_backend": "direct_hwpx",
                "fallback_backend": "",
                "support_level": "DIRECT_FULL",
                "phase": "P05",
                "validation": "semantic_diff",
                "permission": "document.write",
                "source_group": "synthetic",
                "notes": "",
            },
        ]
        with matrix.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=MATRIX_FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        matrix_content = matrix.read_bytes()
        matrix_sha256 = hashlib.sha256(matrix_content).hexdigest()

        node_id = "node:" + "1" * 24
        reviewed = {
            "schema_version": "hwpx-agent.reviewed-catalog/v1",
            "source_lock_id": source_lock_id,
            "generator": {
                "generator_id": "semantic-capability-review-generator",
                "generator_version": "0.1.0",
                "review_policy": "strict_multi_signal_v1",
                "auto_merge": False,
                "runtime_qualification_performed": False,
            },
            "restricted_derivative": license_state == "restricted",
            "candidate_graph": {
                "sha256": "b" * 64,
                "node_count": 1,
                "edge_count": 0,
                "input_sha256": [automation_sha256, "c" * 64, "d" * 64],
            },
            "canonical_matrix": {"sha256": matrix_sha256, "row_count": 3},
            "review_decisions": {
                "sha256": "e" * 64,
                "reviewer_id": "synthetic-reviewer",
                "review_revision": "synthetic-review-v1",
                "method": "manual_strict_multi_signal_v1",
                "item_count": 1,
            },
            "runtime_qualification": {
                "state": "unverified",
                "target_profile_id": None,
                "evidence_refs": [],
            },
            "node_dispositions": [
                {
                    "node_id": node_id,
                    "record_id": record["record_id"],
                    "source_id": source_id,
                    "source_kind": "action_table",
                    "candidate_refs": [],
                    "status": "mapped",
                    "reason_code": "strict_multi_signal_semantic_match",
                    "capability": {
                        "feature_id": "EDIT-001",
                        "capability_id": "edit.copy",
                        "domain": "편집",
                        "scope_class": "artifact_semantics",
                        "support_level": "HYBRID",
                        "preferred_backend": "desktop_automation",
                        "fallback_backend": "direct_hwpx",
                        "phase": "P05",
                    },
                    "semantic_evidence": {
                        "policy": "strict_multi_signal_v1",
                        "action_label_score_ppm": 1000000,
                        "korean_description_score_ppm": 1000000,
                        "combined_score_ppm": 1000000,
                        "runner_up_margin_ppm": 500000,
                        "assertions": [
                            "action_identifier",
                            "korean_description",
                            "backend_compatibility",
                            "human_approval",
                        ],
                    },
                    "runtime_support_state": "unverified",
                }
            ],
            "edge_dispositions": [],
            "coverage": {
                "node_count": 1,
                "mapped_node_count": 1,
                "ignored_node_count": 0,
                "unresolved_node_count": 0,
                "node_reason_counts": [
                    {"code": "strict_multi_signal_semantic_match", "count": 1}
                ],
                "edge_count": 0,
                "disposed_edge_count": 0,
                "undisposed_edge_count": 0,
                "edge_status_counts": [],
                "strict_proposal_count": 1,
                "review_decision_count": 1,
                "runtime_qualified_count": 0,
                "auto_merge_count": 0,
            },
        }
        reviewed_content = (
            json.dumps(reviewed, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        reviewed_catalog = root / "reviewed.json"
        reviewed_catalog.write_bytes(reviewed_content)
        reviewed_sha256 = hashlib.sha256(reviewed_content).hexdigest()

        profile = {
            "profile_id": "hancom-hangul-2020-secondary",
            "product": "Hancom Hangul 2020",
            "major_release": "2020",
            "exact_build": "11.0.0.9136",
            "os_image": "synthetic-current-pc",
            "locale": "ko-KR",
            "fonts_manifest": "synthetic-fonts.yaml",
            "printer_profile": None,
            "automation_catalog_version": "synthetic",
            "owpml_version": "synthetic",
            "capability_catalog_version": "3",
            "license_state": "approved",
            "enabled_backends": ["direct_hwpx"],
            "constraints": {
                "executable_architecture": "x86",
                "desktop_automation_release_state": "allowed_for_test",
                "runtime_probe_scope": "exact_identity_on_current_development_pc",
                "production_release_state": "disabled",
            },
            "image_digest": None,
            "source_lock_id": source_lock_id,
        }
        profile_content = yaml.safe_dump(
            profile, allow_unicode=True, sort_keys=False
        ).encode("utf-8")
        target_profile = root / "target-profile.yaml"
        target_profile.write_bytes(profile_content)
        profile_sha256 = hashlib.sha256(profile_content).hexdigest()
        output_root = root / "output"
        output_root.mkdir()
        return BindingConfig(
            source_lock=source_lock,
            automation_records=automation_records,
            automation_records_sha256=automation_sha256,
            reviewed_catalog=reviewed_catalog,
            reviewed_catalog_sha256=reviewed_sha256,
            matrix=matrix,
            matrix_sha256=matrix_sha256,
            expected_matrix_count=3,
            target_profile=target_profile,
            target_profile_sha256=profile_sha256,
            expected_profile_id="hancom-hangul-2020-secondary",
            expected_exact_build="11.0.0.9136",
            expected_locale="ko-KR",
            expected_architecture="x86",
            expected_automation_release_state="allowed_for_test",
            output_root=output_root,
            output_relative="bindings.json",
        )

    def test_builds_complete_unroutable_registry_and_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.write_fixture(root)
            receipt = run(config)
            output = config.output_root / config.output_relative
            registry = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(receipt["coverage"]["required_capability_count"], 2)
            self.assertEqual(receipt["coverage"]["candidate_unverified_count"], 1)
            self.assertEqual(receipt["coverage"]["unavailable_count"], 1)
            self.assertEqual(receipt["coverage"]["runtime_qualified_count"], 0)
            self.assertFalse(receipt["routing_enabled"])
            self.assertNotIn("Copy", json.dumps(receipt, ensure_ascii=False))
            candidate = next(
                binding
                for binding in registry["bindings"]
                if binding["status"] == "candidate_unverified"
            )
            self.assertEqual(candidate["invocation"]["action_id"], "Copy")
            self.assertIsNone(candidate["invocation"]["parameter_set_id"])
            self.assertFalse(candidate["routing_enabled"])
            result = verify(output, config)
            self.assertEqual(result["errors"], [])
            self.assertFalse(result["raw_identifier_values_emitted_in_receipt"])

    def test_is_deterministic_and_no_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.write_fixture(root)
            first = run(config)
            with self.assertRaisesRegex(ExtractionError, "already exists"):
                run(config)
            second_root = root / "second"
            second_root.mkdir()
            second = run(replace(config, output_root=second_root))
            self.assertEqual(first["output_sha256"], second["output_sha256"])

    def test_rejects_profile_tamper_and_exact_identity_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.write_fixture(root)
            config.target_profile.write_bytes(config.target_profile.read_bytes() + b"\n")
            with self.assertRaisesRegex(ExtractionError, "target profile SHA-256 mismatch"):
                run(config)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.write_fixture(root)
            with self.assertRaisesRegex(ExtractionError, "exact identity mismatch: exact_build"):
                run(replace(config, expected_exact_build="11.0.0.9999"))

    def test_rejects_matrix_reference_and_missing_action_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.write_fixture(root)
            reviewed = json.loads(config.reviewed_catalog.read_text(encoding="utf-8"))
            reviewed["canonical_matrix"]["sha256"] = "f" * 64
            content = (
                json.dumps(reviewed, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            ).encode("utf-8")
            config.reviewed_catalog.write_bytes(content)
            with self.assertRaisesRegex(ExtractionError, "canonical matrix SHA-256 mismatch"):
                run(
                    replace(
                        config,
                        reviewed_catalog_sha256=hashlib.sha256(content).hexdigest(),
                    )
                )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.write_fixture(root)
            reviewed = json.loads(config.reviewed_catalog.read_text(encoding="utf-8"))
            reviewed["node_dispositions"][0]["record_id"] = "automation.missing"
            content = (
                json.dumps(reviewed, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            ).encode("utf-8")
            config.reviewed_catalog.write_bytes(content)
            with self.assertRaisesRegex(ExtractionError, "record is missing"):
                run(
                    replace(
                        config,
                        reviewed_catalog_sha256=hashlib.sha256(content).hexdigest(),
                    )
                )

    def test_restricted_official_derivative_cannot_escape_private_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.write_fixture(root, license_state="restricted")
            with self.assertRaisesRegex(ExtractionError, "implementation/p02/evidence"):
                run(config)

    def test_verifier_detects_missing_capability_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.write_fixture(root)
            run(config)
            output = config.output_root / config.output_relative
            registry = json.loads(output.read_text(encoding="utf-8"))
            registry["bindings"].pop()
            tampered = root / "tampered.json"
            tampered.write_text(
                json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            result = verify(tampered, config)
            self.assertTrue(
                any("order/coverage mismatch" in error for error in result["errors"])
            )

    def test_catalog_v2_is_unchanged_and_v3_contains_binding_schema(self) -> None:
        v2 = REPOSITORY_ROOT / "protocol/generated/typescript/schema-catalog-v2.json"
        v3 = REPOSITORY_ROOT / "protocol/generated/typescript/schema-catalog-v3.json"
        self.assertEqual(
            hashlib.sha256(v2.read_bytes()).hexdigest(),
            "21732da04009162452492026198654dd895d2537f69569788e44f8e2323605f5",
        )
        ids = [item["id"] for item in json.loads(v3.read_text(encoding="utf-8"))["schemas"]]
        self.assertIn(
            "https://hwpx-agent.local/schemas/catalog/automation-binding-registry-v1.schema.json",
            ids,
        )
if __name__ == "__main__":
    unittest.main()
