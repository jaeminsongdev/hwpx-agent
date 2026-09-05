from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tools/p16/integrated_postgres_acceptance.py"
SPEC = importlib.util.spec_from_file_location("integrated_postgres_acceptance_test", SOURCE)
assert SPEC is not None and SPEC.loader is not None
qualification = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qualification)


class IntegratedPostgresAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory(prefix="hwpx-p16-integrated-postgres-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

        self.source = qualification.load_source_validator()
        real_git_digest = self.source.git_digest
        history_patch = patch.object(
            self.source,
            "git_digest",
            side_effect=lambda _root, revision, relative: real_git_digest(ROOT, revision, relative),
        )
        history_patch.start()
        self.addCleanup(history_patch.stop)
        source_loader_patch = patch.object(
            qualification, "load_source_validator", return_value=self.source
        )
        source_loader_patch.start()
        self.addCleanup(source_loader_patch.stop)

        for relative in qualification.verification_paths(ROOT):
            source = ROOT / relative
            if not source.is_file():
                continue
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)

    def verified(self) -> dict:
        return qualification.verified_acceptance(self.root)

    def write_contract(self, value: object) -> None:
        (self.root / qualification.CONTRACT_PATH).write_text(json.dumps(value), encoding="utf-8")

    def test_exact_actual_acceptance_is_narrow(self) -> None:
        value = self.verified()
        self.assertTrue(value["claims"]["actual_integrated_postgres_retested"])
        self.assertFalse(value["claims"]["actual_hangul"])
        self.assertFalse(value["claims"]["p16_phase_complete"])
        self.assertEqual(len(value["runtime_sources"]), 21)

    def test_runtime_drift_rejects(self) -> None:
        target = self.root / "Cargo.lock"
        target.write_bytes(target.read_bytes() + b"\n# drift\n")
        with self.assertRaises(ValueError):
            self.verified()

    def test_receipt_or_source_contract_drift_rejects(self) -> None:
        for relative in (qualification.RECEIPT_PATH, qualification.SOURCE_CONTRACT):
            with self.subTest(relative=relative):
                target = self.root / relative
                original = target.read_bytes()
                target.write_bytes(original + b" ")
                with self.assertRaises(ValueError):
                    self.verified()
                target.write_bytes(original)

    def test_guard_drift_rejects(self) -> None:
        target = self.root / qualification.GUARD_PATHS[-1]
        target.write_bytes(target.read_bytes() + b"\nchanged\n")
        with self.assertRaisesRegex(qualification.QualificationError, "contract.exact"):
            self.verified()

    def test_claim_promotion_and_extra_source_reject(self) -> None:
        baseline = self.verified()
        promoted = copy.deepcopy(baseline)
        promoted["claims"]["p16_phase_complete"] = True
        extra = copy.deepcopy(baseline)
        extra["runtime_sources"].append(extra["runtime_sources"][0])
        wrong_type = copy.deepcopy(baseline)
        wrong_type["claims"]["actual_hangul"] = 0
        for value in (promoted, extra, wrong_type):
            self.write_contract(value)
            with self.assertRaisesRegex(qualification.QualificationError, "contract.exact"):
                self.verified()

    def test_writer_never_overwrites_contract(self) -> None:
        target = self.root / qualification.CONTRACT_PATH
        original = target.read_bytes()
        output = io.StringIO()
        with patch.object(qualification, "ROOT", self.root), patch(
            "sys.argv", ["qualification", "--write"]
        ), contextlib.redirect_stdout(output):
            self.assertEqual(qualification.main(), 1)
        self.assertEqual(target.read_bytes(), original)
        self.assertNotIn(str(self.root), output.getvalue())

    def test_cli_retains_open_phase_claim(self) -> None:
        output = io.StringIO()
        with patch("sys.argv", ["qualification", "--check"]), contextlib.redirect_stdout(output):
            self.assertEqual(qualification.main(), 0)
        value = json.loads(output.getvalue())
        self.assertTrue(value["actual_integrated_postgres_retested"])
        self.assertFalse(value["phase_complete"])


if __name__ == "__main__":
    unittest.main()
