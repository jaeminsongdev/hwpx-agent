from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from tools.p06 import table_conformance as conformance
from tools.p06.build_table_conformance_report import (
    DEFAULT_CATALOG,
    DEFAULT_CONTRACTS,
    DEFAULT_EVIDENCE,
    DEFAULT_PROJECTION,
)


ROOT = Path(__file__).resolve().parents[3]
REPORT = "implementation/p06/evidence/conformance/p06-table-conformance.current-2020.v1.json"


class TableConformanceTests(unittest.TestCase):
    def load(self, relative: str) -> object:
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def build_current(self) -> dict[str, object]:
        return conformance.load_and_build(
            ROOT,
            catalog_path=DEFAULT_CATALOG,
            contracts_path=DEFAULT_CONTRACTS,
            projection_path=DEFAULT_PROJECTION,
            evidence_path=DEFAULT_EVIDENCE,
        )

    def test_current_matrix_is_exact_reproducible_and_non_green(self) -> None:
        report = self.build_current()
        committed = (ROOT / REPORT).read_bytes()
        self.assertEqual(conformance.canonical_json(report), committed)
        self.assertEqual(report["summary"]["required_rows"], 61)
        self.assertEqual(report["summary"]["green_rows"], 0)
        self.assertEqual(report["summary"]["non_green_rows"], 61)
        self.assertEqual(
            report["summary"]["direct_stage_counts"],
            {
                "cataloged": 0,
                "integration_passed": 28,
                "oracle_verified": 33,
                "unit_passed": 0,
            },
        )
        self.assertEqual(
            report["summary"]["automation_binding_counts"],
            {"candidate_unverified": 6, "unavailable_with_reason": 55},
        )
        self.assertEqual(report["summary"]["differential_counts"], {"not_run": 61})
        self.assertEqual(report["summary"]["p06_09"], "in_progress")
        self.assertFalse(report["summary"]["product_complete"])
        self.assertEqual(
            [row["feature_id"] for row in report["rows"]],
            [f"TABLE-{index:03d}" for index in range(1, 62)],
        )

    def test_redacted_projection_rebuilds_without_private_identifiers(self) -> None:
        projection = self.load(DEFAULT_PROJECTION)
        registry_rows = []
        for row in projection["rows"]:
            registry_rows.append(
                {
                    **row,
                    "status": row["binding_status"],
                    "target_profile_id": conformance.TARGET_PROFILE_ID,
                    "invocation": {
                        "action_id": "PRIVATE-ACTION-MARKER",
                        "parameter_set_id": "PRIVATE-PARAMETER-MARKER",
                    },
                }
            )
        registry = {
            "schema_version": "hwpx-agent.automation-binding-registry/v1",
            "target": {
                "profile_id": conformance.TARGET_PROFILE_ID,
                "product": "Hancom Hangul 2020",
                "exact_build": conformance.TARGET_BUILD,
                "locale": conformance.TARGET_LOCALE,
                "architecture": conformance.TARGET_ARCHITECTURE,
            },
            "bindings": registry_rows,
        }
        rebuilt = conformance.build_automation_projection(registry, "a" * 64)
        encoded = conformance.canonical_json(rebuilt)
        self.assertNotIn(b"PRIVATE-ACTION-MARKER", encoded)
        self.assertNotIn(b"PRIVATE-PARAMETER-MARKER", encoded)
        self.assertFalse(any("invocation" in row for row in rebuilt["rows"]))
        self.assertEqual(conformance.validate_projection(rebuilt).__len__(), 61)

        registry["bindings"][0]["target_profile_id"] = "wrong-target"
        with self.assertRaisesRegex(conformance.ConformanceError, "table_binding_target"):
            conformance.build_automation_projection(registry, "a" * 64)

    def test_only_complete_current_target_differential_can_be_green(self) -> None:
        catalog = self.load(DEFAULT_CATALOG)
        contracts = self.load(DEFAULT_CONTRACTS)
        projection = deepcopy(self.load(DEFAULT_PROJECTION))
        for row in projection["rows"]:
            row["binding_status"] = "verified_current_target"
            row["runtime_support_state"] = "verified_current_target"
        evidence_file = "implementation/p06/P06-08_REPORT.md"
        evidence = {
            "schema_version": conformance.EVIDENCE_SCHEMA_VERSION,
            "target": deepcopy(projection["target"]),
            "required_fixture_classes": list(conformance.FIXTURE_CLASSES),
            "records": [
                {
                    "feature_ids": [f"TABLE-{index:03d}" for index in range(1, 62)],
                    "backend": "direct_hwpx",
                    "stage": "oracle_verified",
                    "validations_passed": [
                        "formula_readback",
                        "page_split",
                        "render_diff",
                        "schema",
                        "semantic_reopen",
                    ],
                    "fixture_classes_passed": sorted(conformance.FIXTURE_CLASSES),
                    "negative_passed": True,
                    "rollback_or_retry_passed": True,
                    "differential_state": "exact_match",
                    "evidence_files": [
                        {
                            "path": evidence_file,
                            "sha256": conformance.sha256_file(ROOT / evidence_file),
                        }
                    ],
                }
            ],
            "not_claimed": {
                "p06_07_renderer_gate": False,
                "p06_09_complete": False,
                "p06_phase_complete": False,
                "production": False,
                "other_pc_or_version": False,
                "product_complete": False,
            },
        }
        report = conformance.build_report(
            root=ROOT,
            catalog=catalog,
            catalog_sha256="1" * 64,
            contracts=contracts,
            contracts_sha256="2" * 64,
            projection=projection,
            projection_sha256="3" * 64,
            evidence=evidence,
            evidence_sha256="4" * 64,
        )
        self.assertEqual(report["summary"]["green_rows"], 61)
        self.assertEqual(report["summary"]["required_matrix"], "green")
        self.assertEqual(report["summary"]["p06_09"], "pass")

        evidence["records"][0]["differential_state"] = "not_run"
        blocked = conformance.build_report(
            root=ROOT,
            catalog=catalog,
            catalog_sha256="1" * 64,
            contracts=contracts,
            contracts_sha256="2" * 64,
            projection=projection,
            projection_sha256="3" * 64,
            evidence=evidence,
            evidence_sha256="4" * 64,
        )
        self.assertEqual(blocked["summary"]["green_rows"], 0)

    def test_tamper_duplicate_paths_and_component_overclaim_fail_closed(self) -> None:
        evidence = deepcopy(self.load(DEFAULT_EVIDENCE))
        evidence["records"][0]["evidence_files"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(conformance.ConformanceError, "evidence_file_digest"):
            conformance.validate_evidence(ROOT, evidence)

        evidence = deepcopy(self.load(DEFAULT_EVIDENCE))
        component = evidence["records"][0]
        component["backend"] = "component_only"
        component["stage"] = "integration_passed"
        with self.assertRaisesRegex(conformance.ConformanceError, "component_stage_overclaim"):
            conformance.validate_evidence(ROOT, evidence)

        projection = deepcopy(self.load(DEFAULT_PROJECTION))
        projection["unexpected"] = True
        with self.assertRaisesRegex(conformance.ConformanceError, "projection_shape"):
            conformance.validate_projection(projection)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "payload.json").write_text('{"a":1,"a":2}', encoding="utf-8")
            with self.assertRaisesRegex(conformance.ConformanceError, "duplicate_json_key"):
                conformance.load_json_file(root, "payload.json")
            with self.assertRaisesRegex(conformance.ConformanceError, "unsafe_path"):
                conformance.load_json_file(root, "../payload.json")

    def test_public_report_has_no_raw_registry_identifier_values_or_private_paths(self) -> None:
        report_bytes = (ROOT / REPORT).read_bytes()
        projection_bytes = (ROOT / DEFAULT_PROJECTION).read_bytes()
        self.assertNotIn(b"invocation", report_bytes)
        self.assertNotIn(b'"action_id":', report_bytes)
        self.assertNotIn(b'"parameter_set_id":', report_bytes)
        self.assertNotIn(b"invocation", projection_bytes)
        self.assertNotIn(b'"action_id":', projection_bytes)
        self.assertNotIn(b'"parameter_set_id":', projection_bytes)
        self.assertNotIn(b":\\", report_bytes)
        self.assertNotIn(b":\\", projection_bytes)

    def test_publication_is_create_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            conformance.write_new(output, b"first")
            with self.assertRaises(FileExistsError):
                conformance.write_new(output, b"second")
            self.assertEqual(output.read_bytes(), b"first")


if __name__ == "__main__":
    unittest.main()
