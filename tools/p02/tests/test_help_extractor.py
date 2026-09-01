from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from tools.p02.extract_help import (
    ExtractionConfig,
    ExtractionError,
    build_records,
    load_source_entry,
    parse_headings,
    read_regular_file,
    run,
    serialize_records,
)
from tools.p02.verify_help_output import verify

ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = ROOT / "fixtures" / "synthetic" / "p02-help"


class HelpExtractorTests(unittest.TestCase):
    def config(self, output_root: Path, output_relative: str = "records/help.json") -> ExtractionConfig:
        return ExtractionConfig(
            source_lock=FIXTURE_ROOT / "source-lock.json",
            source_id="synthetic-help-html",
            input_path=FIXTURE_ROOT / "help.html",
            output_root=output_root,
            output_relative=output_relative,
        )

    def test_extracts_deterministic_schema_valid_records(self) -> None:
        source_lock_id, entry = load_source_entry(
            FIXTURE_ROOT / "source-lock.json", "synthetic-help-html"
        )
        content = read_regular_file(FIXTURE_ROOT / "help.html", 1024 * 1024)
        config = self.config(Path("unused"))
        first = serialize_records(build_records(config, source_lock_id, entry, content))
        second = serialize_records(build_records(config, source_lock_id, entry, content))
        self.assertEqual(first, second)
        records = json.loads(first)
        self.assertEqual(len(records), 4)
        self.assertEqual(records[1]["locator"]["value"], "file")
        self.assertEqual(records[2]["original_name"], "문서 열기")
        self.assertRegex(records[3]["locator"]["value"], r"^h2@L[0-9]+:C[0-9]+$")
        self.assertNotIn("raw action", first.decode("utf-8"))

    def test_publishes_atomically_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "records").mkdir()
            config = self.config(root)
            receipt = run(config)
            output = root / "records" / "help.json"
            self.assertEqual(receipt["record_count"], 4)
            self.assertEqual(
                receipt["output_sha256"], hashlib.sha256(output.read_bytes()).hexdigest()
            )
            verification = verify(
                output,
                FIXTURE_ROOT / "source-lock.json",
                "synthetic-help-html",
                FIXTURE_ROOT / "help.html",
            )
            self.assertEqual(verification["errors"], [])
            self.assertEqual(verification["record_count"], 4)
            with self.assertRaises(ExtractionError):
                run(config)

    def test_rejects_tampered_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "records").mkdir()
            tampered = root / "tampered.html"
            tampered.write_bytes((FIXTURE_ROOT / "help.html").read_bytes() + b" ")
            with self.assertRaisesRegex(ExtractionError, "SHA-256 mismatch"):
                run(replace(self.config(root), input_path=tampered))

    def test_rejects_link_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            link = root / "help-link.html"
            try:
                os.symlink(FIXTURE_ROOT / "help.html", link)
            except OSError as error:
                self.skipTest(f"symlink creation unavailable: {error}")
            with self.assertRaisesRegex(ExtractionError, "regular non-link"):
                read_regular_file(link, 1024 * 1024)

    def test_rejects_non_help_lock_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_lock = json.loads((FIXTURE_ROOT / "source-lock.json").read_text("utf-8"))
            source_lock["sources"][0]["kind"] = "pdf_manual"
            lock_path = root / "source-lock.json"
            lock_path.write_text(json.dumps(source_lock), encoding="utf-8")
            with self.assertRaisesRegex(ExtractionError, "not web_help"):
                load_source_entry(lock_path, "synthetic-help-html")

    def test_rejects_traversal_and_missing_heading(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ExtractionError, "normal repository-style"):
                run(self.config(root, "../escape.json"))
        with self.assertRaisesRegex(ExtractionError, "no title or heading"):
            parse_headings(b"<html><body><p>no heading</p></body></html>")

    def test_rejects_invalid_availability_and_reserved_output(self) -> None:
        source_lock_id, entry = load_source_entry(
            FIXTURE_ROOT / "source-lock.json", "synthetic-help-html"
        )
        content = read_regular_file(FIXTURE_ROOT / "help.html", 1024 * 1024)
        config = replace(
            self.config(Path("unused")),
            minimum_version="13.0.0.0",
            maximum_version="11.0.0.0",
        )
        with self.assertRaisesRegex(ExtractionError, "greater than"):
            build_records(config, source_lock_id, entry, content)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "records").mkdir()
            with self.assertRaisesRegex(ExtractionError, "reserved path"):
                run(self.config(root, "records/CON.json"))

    def test_restricted_source_is_confined_to_private_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "records").mkdir()
            source_lock = json.loads((FIXTURE_ROOT / "source-lock.json").read_text("utf-8"))
            source_lock["sources"][0]["license_state"] = "restricted"
            lock_path = root / "source-lock.json"
            lock_path.write_text(json.dumps(source_lock), encoding="utf-8")
            config = replace(self.config(root), source_lock=lock_path)
            with self.assertRaisesRegex(ExtractionError, "implementation/p02/evidence"):
                run(config)


if __name__ == "__main__":
    unittest.main()
