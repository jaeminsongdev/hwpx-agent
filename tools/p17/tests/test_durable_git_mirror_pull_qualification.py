from __future__ import annotations

import copy
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import durable_git_mirror_pull_qualification as qualification


ROOT = Path(__file__).resolve().parents[3]


class DurableGitMirrorPullQualificationTests(unittest.TestCase):
    def test_exact_current_pc_qualification_without_phase_promotion(self) -> None:
        contract = qualification.verify(ROOT)
        claims = contract["claims"]
        self.assertTrue(claims["actual_current_pc_postgresql_18_4"])
        self.assertTrue(claims["actual_disposable_local_bare_git"])
        self.assertTrue(claims["actual_authenticated_loopback"])
        self.assertTrue(claims["durable_pull"])
        self.assertTrue(claims["actual_clean_remote_advance"])
        self.assertTrue(claims["actual_ahead_conflict_preservation"])
        self.assertTrue(claims["actual_exact_replay_without_second_observation"])
        self.assertFalse(claims["actual_remote_network"])
        self.assertFalse(claims["persistent_credential_custody"])
        self.assertFalse(claims["actual_hangul"])
        self.assertFalse(claims["production"])
        self.assertFalse(claims["p17_06_complete"])
        self.assertFalse(claims["product_complete"])

    def test_receipt_claim_and_effect_tamper_fail_closed(self) -> None:
        receipt_path = ROOT / qualification.RECEIPT_RELATIVE
        receipt = qualification.runtime.load_unique(receipt_path)
        promoted = copy.deepcopy(receipt)
        promoted["claims"]["actual_remote_network"] = True
        with self.assertRaisesRegex(
            qualification.runtime.ContractError, "receipt.claims"
        ):
            qualification.runtime.validate_receipt(promoted, ROOT)
        changed = copy.deepcopy(receipt)
        changed["effect"]["observation_count"] = 2
        with self.assertRaisesRegex(
            qualification.runtime.ContractError, "receipt.effect"
        ):
            qualification.runtime.validate_receipt(changed, ROOT)

    def test_committed_runtime_source_tamper_fails_closed(self) -> None:
        original = qualification.git_blob

        def tampered(root: Path, commit: str, relative: str) -> bytes:
            raw = original(root, commit, relative)
            if relative == "crates/remote-sync-host/src/durable_git_pull.rs":
                return raw + b"\n"
            return raw

        with patch.object(qualification, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                qualification.QualificationError, "source.history"
            ):
                qualification.verify(ROOT)

    def test_contract_and_duplicate_json_tamper_fail_closed(self) -> None:
        contract_path = ROOT / qualification.BASE / "contract.json"
        contract = qualification.load_document(contract_path, "contract")
        changed = copy.deepcopy(contract)
        changed["claims"]["production"] = True
        original = qualification.load_document

        def tampered(path: Path, code: str) -> dict[str, object]:
            return changed if path == contract_path else original(path, code)

        with patch.object(
            qualification,
            "load_document",
            side_effect=tampered,
        ):
            with self.assertRaisesRegex(
                qualification.QualificationError, "contract.identity"
            ):
                qualification.verify(ROOT)
        duplicate = ROOT / qualification.BASE / "current-host.json"
        raw = duplicate.read_bytes()
        self.assertRaises(
            qualification.QualificationError,
            qualification.load_document,
            _DuplicatePath(raw.replace(b"{", b'{"schema_version":"x",', 1)),
            "current",
        )


class _DuplicatePath:
    def __init__(self, raw: bytes) -> None:
        self.raw = raw

    def read_bytes(self) -> bytes:
        return self.raw


if __name__ == "__main__":
    unittest.main()
