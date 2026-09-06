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
SOURCE = ROOT / "tools/p16/integrated_source_qualification.py"
SPEC = importlib.util.spec_from_file_location("integrated_source_qualification_test", SOURCE)
assert SPEC is not None and SPEC.loader is not None
qualification = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qualification)
REAL_GIT_DIGEST = qualification.git_digest


class IntegratedSourceQualificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory(prefix="hwpx-p16-main-integration-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for relative in qualification.verification_paths(ROOT):
            source = ROOT / relative
            if not source.is_file():
                continue
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)

    def verified(self) -> dict[str, tuple[str, str]]:
        with patch.object(
            qualification,
            "git_digest",
            side_effect=lambda _root, revision, relative: REAL_GIT_DIGEST(ROOT, revision, relative),
        ):
            return qualification.verified_replacements(self.root)

    def write_contract(self, value: object) -> None:
        (self.root / qualification.CONTRACT_PATH).write_text(json.dumps(value), encoding="utf-8")

    def test_exact_contract_admits_only_declared_successors(self) -> None:
        replacements = self.verified()
        current = qualification.current_source_successors(ROOT)
        self.assertEqual(
            set(replacements), set(qualification.REPLACED_PATHS) | set(current)
        )
        self.assertTrue(all(before != after for before, after in replacements.values()))

    def test_each_replacement_drift_rejects(self) -> None:
        for relative in self.verified():
            with self.subTest(relative=relative):
                target = self.root / relative
                original = target.read_bytes()
                target.write_bytes(original + b"\n# drift\n")
                with self.assertRaises(ValueError):
                    self.verified()
                target.write_bytes(original)

    def test_each_guard_drift_rejects(self) -> None:
        for relative in qualification.GUARD_PATHS:
            with self.subTest(relative=relative):
                target = self.root / relative
                original = target.read_bytes()
                target.write_bytes(original + b"\nchanged\n")
                with self.assertRaises(ValueError):
                    self.verified()
                target.write_bytes(original)

    def test_predecessor_contracts_are_immutable(self) -> None:
        for relative in (qualification.POSTGRES_CONTRACT, qualification.P15_CONTRACT):
            with self.subTest(relative=relative):
                target = self.root / relative
                original = target.read_bytes()
                target.write_bytes(original + b" ")
                with self.assertRaisesRegex(qualification.QualificationError, "predecessor.digest"):
                    self.verified()
                target.write_bytes(original)

    def test_history_mismatch_rejects(self) -> None:
        with patch.object(qualification, "git_digest", return_value="0" * 64):
            with self.assertRaisesRegex(ValueError, "history"):
                qualification.verified_replacements(self.root)

    def test_claim_promotion_extra_path_and_wrong_type_reject(self) -> None:
        contract = json.loads((self.root / qualification.CONTRACT_PATH).read_bytes())
        mutations = []
        promoted = copy.deepcopy(contract)
        promoted["claims"]["p16_phase_complete"] = True
        mutations.append(promoted)
        extra = copy.deepcopy(contract)
        extra["replacements"].append(extra["replacements"][0])
        mutations.append(extra)
        wrong_type = copy.deepcopy(contract)
        wrong_type["claims"]["actual_hangul"] = 0
        mutations.append(wrong_type)
        for value in mutations:
            self.write_contract(value)
            with self.assertRaisesRegex(qualification.QualificationError, "contract.exact"):
                self.verified()

    def test_writer_never_overwrites_contract(self) -> None:
        target = self.root / qualification.CONTRACT_PATH
        original = target.read_bytes()
        output = io.StringIO()
        with patch.object(qualification, "ROOT", self.root), patch.object(
            qualification,
            "git_digest",
            side_effect=lambda _root, revision, relative: REAL_GIT_DIGEST(ROOT, revision, relative),
        ), patch("sys.argv", ["qualification", "--write"]), contextlib.redirect_stdout(output):
            self.assertEqual(qualification.main(), 1)
        self.assertEqual(target.read_bytes(), original)
        self.assertNotIn(str(self.root), output.getvalue())

    def test_cli_retains_open_claims(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch("sys.argv", ["qualification", "--check"]):
            self.assertEqual(qualification.main(), 0)
        value = json.loads(output.getvalue())
        self.assertFalse(value["actual_integrated_postgres_retested"])
        self.assertFalse(value["phase_complete"])


if __name__ == "__main__":
    unittest.main()
