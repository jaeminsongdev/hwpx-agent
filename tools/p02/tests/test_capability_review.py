from __future__ import annotations

import csv
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.p02.build_candidates import (
    InputSpec,
    build_graph,
    load_inputs,
    load_source_lock,
    serialize_graph,
)
from tools.p02.extract_help import ExtractionError
from tools.p02.review_capabilities import (
    MATRIX_FIELDS,
    ReviewConfig,
    build_proposals,
    load_matrix,
    run,
)
from tools.p02.verify_reviewed_catalog import verify


def source_record(
    record_id: str,
    source_id: str,
    source_sha256: str,
    source_kind: str,
    name: str,
    description: str,
) -> dict:
    if source_kind == "help":
        locator = {"kind": "section", "value": "copy"}
    elif source_kind == "xsd":
        locator = {
            "kind": "xsd_component",
            "value": "appendix:B|namespace:urn:synthetic|kind:attribute|path:/copy",
        }
    else:
        locator = {
            "kind": "automation_item",
            "value": "action_table/page:1",
            "section": "ActionTable",
        }
    return {
        "schema_version": "hwpx-agent.source-record/v1",
        "record_id": record_id,
        "source_lock_id": "review-test-lock",
        "source_id": source_id,
        "source_sha256": source_sha256,
        "source_kind": source_kind,
        "locator": locator,
        "original_name": name,
        "description_ko": description,
        "parameters": [],
        "availability": {
            "product": "hancom_hangul",
            "target_profile_id": None,
            "minimum_version": None,
            "maximum_version": None,
            "locales": ["ko-KR"],
            "support_scope": "documentation_only",
        },
        "extraction": {
            "extractor_id": "review-test-source",
            "extractor_version": "0.1.0",
            "record_ordinal": 0,
        },
    }


class CapabilityReviewTests(unittest.TestCase):
    def write_fixture(
        self, root: Path, license_state: str = "public_reference"
    ) -> tuple[ReviewConfig, str]:
        definitions = {
            "help": ("help-source", "1" * 64, "help"),
            "automation": ("automation-source", "2" * 64, "action_table"),
            "owpml": ("owpml-source", "3" * 64, "xsd"),
        }
        specs: list[InputSpec] = []
        sources: list[dict] = []
        for role, (source_id, source_sha256, source_kind) in definitions.items():
            record = source_record(
                f"{role}.copy",
                source_id,
                source_sha256,
                source_kind,
                "Copy",
                "복사",
            )
            content = (json.dumps([record], ensure_ascii=False) + "\n").encode("utf-8")
            path = root / f"{role}.json"
            path.write_bytes(content)
            specs.append(
                InputSpec(
                    role=role,
                    path=path,
                    expected_sha256=hashlib.sha256(content).hexdigest(),
                )
            )
            sources.append(
                {
                    "source_id": source_id,
                    "sha256": source_sha256,
                    "license_state": license_state,
                }
            )
        source_lock = root / "source-lock.json"
        source_lock.write_text(
            json.dumps(
                {
                    "schema_version": "hwpx-agent.source-lock/v2",
                    "source_lock_id": "review-test-lock",
                    "sources": sources,
                }
            ),
            encoding="utf-8",
        )
        source_lock_id, entries = load_source_lock(source_lock)
        loaded = load_inputs(tuple(specs), source_lock_id, entries)
        graph = build_graph(source_lock_id, loaded)
        graph_content = serialize_graph(graph)
        graph_path = root / "candidate-graph.json"
        graph_path.write_bytes(graph_content)
        graph_sha256 = hashlib.sha256(graph_content).hexdigest()

        matrix_path = root / "matrix.csv"
        with matrix_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=MATRIX_FIELDS, lineterminator="\n")
            writer.writeheader()
            for feature_id, capability_id, feature_ko in (
                ("EDIT-001", "edit.copy", "복사"),
                ("EDIT-002", "edit.paste", "붙여넣기"),
            ):
                writer.writerow(
                    {
                        "feature_id": feature_id,
                        "domain": "편집",
                        "scope_class": "artifact_semantics",
                        "feature_ko": feature_ko,
                        "capability_id": capability_id,
                        "semantic_operation": feature_ko,
                        "document_ir": "Selection",
                        "preferred_backend": "desktop_automation",
                        "fallback_backend": "direct_hwpx",
                        "support_level": "HYBRID",
                        "phase": "P05",
                        "validation": "semantic_diff",
                        "permission": "document.write",
                        "source_group": "synthetic",
                        "notes": "",
                    }
                )
        matrix_content = matrix_path.read_bytes()
        matrix_sha256 = hashlib.sha256(matrix_content).hexdigest()
        _, matrix_rows = load_matrix(matrix_path, matrix_sha256, 2)
        records_by_ref = {
            (item.role, ordinal): record
            for item in loaded
            for ordinal, record in enumerate(item.records)
        }
        _, proposals = build_proposals(graph, records_by_ref, matrix_rows)
        self.assertEqual(len(proposals), 1)
        proposal = next(iter(proposals.values()))
        decisions = {
            "schema_version": "hwpx-agent.capability-review-decisions/v1",
            "candidate_graph_sha256": graph_sha256,
            "canonical_matrix_sha256": matrix_sha256,
            "reviewer": {
                "reviewer_id": "synthetic-reviewer",
                "review_revision": "synthetic-review-v1",
                "method": "manual_strict_multi_signal_v1",
            },
            "items": [
                {
                    "node_id": proposal.node_id,
                    "status": "mapped",
                    "reason_code": "strict_multi_signal_semantic_match",
                    "capability_id": proposal.capability_id,
                }
            ],
        }
        decisions_content = (
            json.dumps(decisions, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        decisions_path = root / "decisions.json"
        decisions_path.write_bytes(decisions_content)
        decisions_sha256 = hashlib.sha256(decisions_content).hexdigest()
        output_root = root / "output"
        output_root.mkdir()
        config = ReviewConfig(
            source_lock=source_lock,
            inputs=tuple(specs),
            candidate_graph=graph_path,
            candidate_graph_sha256=graph_sha256,
            matrix=matrix_path,
            matrix_sha256=matrix_sha256,
            expected_matrix_count=2,
            decisions=decisions_path,
            decisions_sha256=decisions_sha256,
            output_root=output_root,
            output_relative="catalog.json",
        )
        return config, proposal.node_id

    def test_dispositions_cover_every_node_and_edge_without_runtime_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, mapped_node_id = self.write_fixture(root)
            receipt = run(config)
            output = config.output_root / config.output_relative
            catalog = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(receipt["coverage"]["node_count"], 3)
            self.assertEqual(receipt["coverage"]["mapped_node_count"], 1)
            self.assertEqual(receipt["coverage"]["ignored_node_count"], 2)
            self.assertEqual(receipt["coverage"]["edge_count"], 3)
            self.assertEqual(receipt["coverage"]["undisposed_edge_count"], 0)
            self.assertEqual(receipt["coverage"]["auto_merge_count"], 0)
            mapped = next(
                item for item in catalog["node_dispositions"] if item["node_id"] == mapped_node_id
            )
            self.assertEqual(mapped["capability"]["capability_id"], "edit.copy")
            self.assertEqual(mapped["runtime_support_state"], "unverified")
            self.assertEqual(catalog["runtime_qualification"]["state"], "unverified")
            self.assertTrue(all(edge["auto_merge"] is False for edge in catalog["edge_dispositions"]))
            result = verify(
                output,
                config.source_lock,
                config.inputs,
                config.candidate_graph,
                config.candidate_graph_sha256,
                config.matrix,
                config.matrix_sha256,
                config.expected_matrix_count,
                config.decisions,
                config.decisions_sha256,
            )
            self.assertEqual(result["errors"], [])

    def test_deterministic_no_overwrite_and_input_order_independence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, _ = self.write_fixture(root)
            first = run(config)
            with self.assertRaisesRegex(ExtractionError, "already exists"):
                run(config)
            second_root = root / "second"
            second_root.mkdir()
            second = run(
                replace(
                    config,
                    inputs=tuple(reversed(config.inputs)),
                    output_root=second_root,
                )
            )
            self.assertEqual(first["output_sha256"], second["output_sha256"])

    def test_rejects_missing_review_and_wrong_capability(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, _ = self.write_fixture(root)
            decisions = json.loads(config.decisions.read_text(encoding="utf-8"))
            decisions["items"] = []
            content = (
                json.dumps(decisions, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            ).encode("utf-8")
            config.decisions.write_bytes(content)
            with self.assertRaisesRegex(ExtractionError, "schema invalid"):
                run(replace(config, decisions_sha256=hashlib.sha256(content).hexdigest()))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, _ = self.write_fixture(root)
            decisions = json.loads(config.decisions.read_text(encoding="utf-8"))
            decisions["items"][0]["capability_id"] = "edit.paste"
            content = (
                json.dumps(decisions, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            ).encode("utf-8")
            config.decisions.write_bytes(content)
            with self.assertRaisesRegex(ExtractionError, "does not match strict proposal"):
                run(replace(config, decisions_sha256=hashlib.sha256(content).hexdigest()))

    def test_rejects_locked_artifact_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, _ = self.write_fixture(root)
            config.matrix.write_bytes(config.matrix.read_bytes() + b"\n")
            with self.assertRaisesRegex(ExtractionError, "canonical matrix SHA-256 mismatch"):
                run(config)

    def test_explicit_ambiguity_rejection_remains_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, mapped_node_id = self.write_fixture(root)
            decisions = json.loads(config.decisions.read_text(encoding="utf-8"))
            decisions["items"][0] = {
                "node_id": mapped_node_id,
                "status": "ignored_with_reason",
                "reason_code": "ambiguous_canonical_semantics",
            }
            content = (
                json.dumps(decisions, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            ).encode("utf-8")
            config.decisions.write_bytes(content)
            receipt = run(
                replace(config, decisions_sha256=hashlib.sha256(content).hexdigest())
            )
            catalog = json.loads(
                (config.output_root / config.output_relative).read_text(encoding="utf-8")
            )
            rejected = next(
                item
                for item in catalog["node_dispositions"]
                if item["node_id"] == mapped_node_id
            )
            self.assertEqual(receipt["coverage"]["mapped_node_count"], 0)
            self.assertEqual(rejected["status"], "ignored_with_reason")
            self.assertEqual(rejected["reason_code"], "ambiguous_canonical_semantics")
            self.assertIsNone(rejected["capability"])

    def test_restricted_derivative_cannot_escape_private_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, _ = self.write_fixture(root, license_state="restricted")
            with self.assertRaisesRegex(ExtractionError, "implementation/p02/evidence"):
                run(config)

    def test_independent_verifier_detects_missing_edge_disposition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, _ = self.write_fixture(root)
            run(config)
            output = config.output_root / config.output_relative
            catalog = json.loads(output.read_text(encoding="utf-8"))
            catalog["edge_dispositions"].pop()
            tampered = root / "tampered.json"
            tampered.write_text(
                json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            result = verify(
                tampered,
                config.source_lock,
                config.inputs,
                config.candidate_graph,
                config.candidate_graph_sha256,
                config.matrix,
                config.matrix_sha256,
                config.expected_matrix_count,
                config.decisions,
                config.decisions_sha256,
            )
            self.assertTrue(any("edge dispositions" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
