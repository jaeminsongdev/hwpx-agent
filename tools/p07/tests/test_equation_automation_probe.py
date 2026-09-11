from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.p07 import build_equation_automation_probe as builder


def record(record_id: str, name: str, kind: str, declared: str, section: str) -> dict:
    return {
        "record_id": record_id,
        "source_lock_id": builder.SOURCE_LOCK_ID,
        "source_kind": kind,
        "original_name": name,
        "locator": {"section": section},
        "parameters": [
            {
                "original_name": name,
                "declared_type": declared,
            }
        ],
    }


def fixture_records() -> list[dict]:
    parameter_set = "PrivateSet"
    values = [
        {
            "record_id": builder.ACTION_RECORD_IDS["eq.insert_native"],
            "source_lock_id": builder.SOURCE_LOCK_ID,
            "source_kind": "action_table",
            "original_name": "PrivateInsert",
            "parameters": [
                {
                    "original_name": parameter_set,
                    "declared_type": "ParameterSet ID",
                }
            ],
        },
        {
            "record_id": builder.ACTION_RECORD_IDS["eq.edit_native"],
            "source_lock_id": builder.SOURCE_LOCK_ID,
            "source_kind": "action_table",
            "original_name": "PrivateEdit",
            "parameters": [
                {
                    "original_name": parameter_set,
                    "declared_type": "ParameterSet ID",
                }
            ],
        },
        {
            "record_id": builder.SELECTION_ACTION_RECORD_ID,
            "source_lock_id": builder.SOURCE_LOCK_ID,
            "source_kind": "action_table",
            "original_name": "PrivateSelect",
            "parameters": [
                {
                    "original_name": "-",
                    "declared_type": "ParameterSet ID",
                }
            ],
        },
    ]
    for argument_id, record_id in builder.ITEM_RECORD_IDS.items():
        values.append(
            record(
                record_id,
                f"Private{argument_id}",
                "parameter_table",
                builder.EXPECTED_ITEM_TYPES[argument_id],
                f"{parameter_set} | private",
            )
        )
    return values


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def build(records: list[dict] | None = None):
    return builder.build_request(
        fixture_records() if records is None else records,
        "1" * 64,
        "x + 1",
        digest("x + 1"),
        "2" * 64,
        "x ^ 2 + 1",
        digest("x ^ 2 + 1"),
        "3" * 64,
    )


class EquationAutomationProbeTests(unittest.TestCase):
    def test_private_request_and_redacted_receipt_are_deterministic(self) -> None:
        request, receipt = build()
        self.assertEqual((request, receipt), build())
        self.assertEqual(request["source"]["binding_set_sha256"], receipt["binding_set_sha256"])
        self.assertEqual(receipt["action_binding_count"], 3)
        self.assertEqual(receipt["item_binding_count"], 8)
        self.assertEqual(receipt["runtime"], "not_run")
        self.assertFalse(receipt["production"])
        receipt_text = json.dumps(receipt)
        for private in ("PrivateInsert", "PrivateEdit", "PrivateSet", "x + 1"):
            self.assertNotIn(private, receipt_text)

    def test_source_record_identity_shape_and_type_tamper_fail(self) -> None:
        cases = []
        missing = fixture_records()
        missing.pop()
        cases.append(missing)
        duplicate = fixture_records()
        duplicate.append(copy.deepcopy(duplicate[0]))
        cases.append(duplicate)
        wrong_set = fixture_records()
        wrong_set[1]["parameters"][0]["original_name"] = "Different"
        cases.append(wrong_set)
        wrong_type = fixture_records()
        wrong_type[3]["parameters"][0]["declared_type"] = "PIT_UI4"
        cases.append(wrong_type)
        wrong_section = fixture_records()
        wrong_section[3]["locator"]["section"] = "Other | private"
        cases.append(wrong_section)
        for records in cases:
            with self.subTest(records=records):
                with self.assertRaises(builder.ProbeBuildError):
                    build(records)

    def test_digest_script_and_distinct_program_boundaries_fail(self) -> None:
        records = fixture_records()
        with self.assertRaises(builder.ProbeBuildError):
            builder.build_request(
                records,
                "1" * 64,
                "x",
                "0" * 64,
                "2" * 64,
                "y",
                digest("y"),
                "3" * 64,
            )
        with self.assertRaises(builder.ProbeBuildError):
            builder.build_request(
                records,
                "1" * 64,
                "x",
                digest("x"),
                "2" * 64,
                "x",
                digest("x"),
                "2" * 64,
            )

    def test_duplicate_json_source_hash_and_private_path_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            source.write_text('{"a":1,"a":2}', encoding="utf-8")
            raw = source.read_bytes()
            with self.assertRaises(builder.ProbeBuildError):
                builder.load_source_records(source, hashlib.sha256(raw).hexdigest())
            source.write_text("[]", encoding="utf-8")
            with self.assertRaises(builder.ProbeBuildError):
                builder.load_source_records(source, "0" * 64)
            boundary = root / "private"
            boundary.mkdir()
            with self.assertRaises(builder.ProbeBuildError):
                builder.require_private_output(root / "outside", boundary)

    def test_no_overwrite_preserves_first_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            builder.publish_no_overwrite(path, {"value": 1})
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                builder.publish_no_overwrite(path, {"value": 2})
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
