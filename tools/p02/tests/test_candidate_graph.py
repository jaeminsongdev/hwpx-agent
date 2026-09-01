from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.p02.build_candidates import (
    CandidateConfig,
    ExtractionError,
    InputSpec,
    build_graph,
    load_inputs,
    load_source_lock,
    normalize_label,
    normalize_signal_value,
    run,
    serialize_graph,
)
from tools.p02.verify_candidate_graph import verify


def source_record(
    record_id: str,
    source_id: str,
    source_sha256: str,
    source_kind: str,
    name: str,
    ordinal: int,
) -> dict:
    if source_kind in {"help", "webhwp"}:
        locator = {"kind": "section", "value": f"section-{ordinal}"}
    elif source_kind == "xsd":
        locator = {
            "kind": "xsd_component",
            "value": f"appendix:B|namespace:urn:synthetic|kind:attribute|path:/a[{ordinal + 1}]",
        }
    else:
        locator = {
            "kind": "automation_item",
            "value": f"{source_kind}/page:{ordinal + 1}",
            "section": "ITable | methods",
        }
    return {
        "schema_version": "hwpx-agent.source-record/v1",
        "record_id": record_id,
        "source_lock_id": "candidate-test-lock",
        "source_id": source_id,
        "source_sha256": source_sha256,
        "source_kind": source_kind,
        "locator": locator,
        "original_name": name,
        "description_ko": None,
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
            "extractor_id": "candidate-test-source",
            "extractor_version": "0.1.0",
            "record_ordinal": ordinal,
        },
    }


class CandidateGraphTests(unittest.TestCase):
    def write_inputs(
        self, root: Path, license_state: str = "public_reference"
    ) -> tuple[Path, tuple[InputSpec, ...]]:
        definitions = {
            "help": ("help-source", "1" * 64, "help", "Table Merge (&M)"),
            "automation": (
                "automation-source",
                "2" * 64,
                "automation_object",
                "TableMerge",
            ),
            "owpml": ("owpml-source", "3" * 64, "xsd", "Table-Merge"),
        }
        sources = []
        specs = []
        for role, (source_id, source_sha256, source_kind, name) in definitions.items():
            records = [
                source_record(
                    f"{role}.record", source_id, source_sha256, source_kind, name, 0
                )
            ]
            content = (json.dumps(records, ensure_ascii=False) + "\n").encode("utf-8")
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
                    "source_lock_id": "candidate-test-lock",
                    "sources": sources,
                }
            ),
            encoding="utf-8",
        )
        return source_lock, tuple(specs)

    def config(
        self, root: Path, source_lock: Path, specs: tuple[InputSpec, ...]
    ) -> CandidateConfig:
        return CandidateConfig(
            source_lock=source_lock,
            inputs=specs,
            output_root=root,
            output_relative="records/candidates.json",
        )

    def test_normalization_is_explicit_and_rejects_deceptive_labels(self) -> None:
        self.assertEqual(normalize_label("TableMerge (&M)")[0], "table merge")
        self.assertEqual(normalize_label("Table-Merge")[0], "table merge")
        self.assertEqual(normalize_signal_value("+"), "symbol-u002b")
        with self.assertRaisesRegex(ExtractionError, "prohibited control/format"):
            normalize_label("safe\u202eevil")
        with self.assertRaisesRegex(ExtractionError, "empty"):
            normalize_label("---")

    def test_builds_all_nodes_and_review_only_edges_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_lock, specs = self.write_inputs(root)
            source_lock_id, entries = load_source_lock(source_lock)
            loaded = load_inputs(tuple(reversed(specs)), source_lock_id, entries)
            graph = build_graph(source_lock_id, loaded)
            self.assertEqual(graph["coverage"]["node_count"], 3)
            self.assertEqual(graph["coverage"]["edge_count"], 3)
            self.assertEqual(graph["coverage"]["review_candidate_count"], 2)
            self.assertEqual(graph["coverage"]["collision_review_count"], 1)
            self.assertEqual(graph["coverage"]["auto_merge_count"], 0)
            self.assertTrue(all(edge["auto_merge"] is False for edge in graph["edges"]))
            self.assertEqual(
                serialize_graph(graph),
                serialize_graph(build_graph(source_lock_id, load_inputs(specs, source_lock_id, entries))),
            )

    def test_publishes_no_overwrite_and_verifies_every_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "records").mkdir()
            source_lock, specs = self.write_inputs(root)
            config = self.config(root, source_lock, specs)
            receipt = run(config)
            output = root / "records" / "candidates.json"
            result = verify(output, source_lock, specs)
            self.assertEqual(result["errors"], [])
            self.assertEqual(receipt["coverage"]["input_record_count"], 3)
            with self.assertRaisesRegex(ExtractionError, "already exists"):
                run(config)

    def test_rejects_input_tamper_duplicate_id_and_noncontiguous_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_lock, specs = self.write_inputs(root)
            specs[0].path.write_bytes(specs[0].path.read_bytes() + b" ")
            source_lock_id, entries = load_source_lock(source_lock)
            with self.assertRaisesRegex(ExtractionError, "SHA-256 mismatch"):
                load_inputs(specs, source_lock_id, entries)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_lock, specs = self.write_inputs(root)
            automation = next(spec for spec in specs if spec.role == "automation")
            records = json.loads(automation.path.read_text(encoding="utf-8"))
            duplicate = dict(records[0])
            duplicate["extraction"] = dict(duplicate["extraction"], record_ordinal=1)
            records.append(duplicate)
            content = (json.dumps(records) + "\n").encode("utf-8")
            automation.path.write_bytes(content)
            changed = tuple(
                replace(spec, expected_sha256=hashlib.sha256(content).hexdigest())
                if spec.role == "automation"
                else spec
                for spec in specs
            )
            source_lock_id, entries = load_source_lock(source_lock)
            with self.assertRaisesRegex(ExtractionError, "duplicate input record_id"):
                load_inputs(changed, source_lock_id, entries)

    def test_rejects_role_mismatch_and_output_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_lock, specs = self.write_inputs(root)
            bad = tuple(
                replace(spec, role="automation") if spec.role == "help" else spec
                for spec in specs
            )
            source_lock_id, entries = load_source_lock(source_lock)
            with self.assertRaisesRegex(ExtractionError, "exactly one"):
                load_inputs(bad, source_lock_id, entries)
            config = replace(
                self.config(root, source_lock, specs), output_relative="../escape.json"
            )
            with self.assertRaisesRegex(ExtractionError, "normal repository-style"):
                run(config)

    def test_restricted_derivative_cannot_escape_private_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "records").mkdir()
            source_lock, specs = self.write_inputs(root, license_state="restricted")
            with self.assertRaisesRegex(ExtractionError, "implementation/p02/evidence"):
                run(self.config(root, source_lock, specs))


if __name__ == "__main__":
    unittest.main()
