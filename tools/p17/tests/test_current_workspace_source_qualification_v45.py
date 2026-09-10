from __future__ import annotations

import copy
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import current_workspace_source_qualification_v45 as qualification
from tools.p17 import durable_git_mirror_pull_qualification as foundation


ROOT = Path(__file__).resolve().parents[3]


class CurrentWorkspaceSourceQualificationV45Tests(unittest.TestCase):
    def test_current_exact_license_admission_sources_pass(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(
            result["qualification_id"],
            "p17.current-workspace-source.v45.20260911",
        )
        self.assertEqual(result["source_successor_count"], 28)
        self.assertEqual(len(result["implementation_sources"]), 8)
        self.assertEqual(len(result["runtime_qualification_sources"]), 2)
        self.assertEqual(len(result["guard_sources"]), 3)

    def test_license_claims_do_not_promote_remote_or_product(self) -> None:
        result = qualification.verify(ROOT)
        claims = result["claims"]
        self.assertTrue(
            claims["p17_remote_tls_dependency_license_admission_current_pc_verified"]
        )
        self.assertTrue(
            claims["p17_remote_tls_dependency_license_exact_versions_only"]
        )
        self.assertFalse(
            claims["p17_remote_tls_dependency_license_global_isc_allowance"]
        )
        self.assertFalse(claims["p17_remote_tls_transport_external_network_verified"])
        self.assertFalse(claims["p17_real_service_certificate_verified"])
        self.assertFalse(claims["p17_real_service_credential_verified"])
        self.assertFalse(claims["p17_credential_issuance_rotation_verified"])
        self.assertFalse(claims["production"])
        self.assertFalse(claims["p17_06_complete"])
        self.assertFalse(claims["product_complete"])

    def test_receipt_or_implementation_drift_fails_closed(self) -> None:
        receipt = foundation.load_document(qualification.receipt_path(ROOT), "receipt")
        tampered = copy.deepcopy(receipt)
        tampered["source_commit"] = "0" * 40
        with self.assertRaises(foundation.QualificationError):
            qualification.validate_receipt(tampered, ROOT)

        original = qualification.source_lock

        def drifted(
            root: Path, relative: str, *, committed: bool = False
        ) -> dict[str, object]:
            value = original(root, relative, committed=committed)
            if relative == "deny.toml":
                value = {**value, "sha256": "0" * 64}
            return value

        with patch.object(qualification, "source_lock", side_effect=drifted):
            with self.assertRaises(foundation.QualificationError):
                qualification.verify(ROOT)

    def test_mutable_gate_promotion_fails_contract_identity(self) -> None:
        current_path = ROOT / qualification.BASE / "current-host.json"
        expected = qualification.expected_contract(ROOT, current_path)
        promoted = copy.deepcopy(expected)
        promoted["claims"]["p17_06_complete"] = True
        contract_path = ROOT / qualification.BASE / "contract.json"
        original_load = foundation.load_document
        with patch.object(
            foundation,
            "load_document",
            wraps=original_load,
        ) as loader:
            loader.side_effect = lambda path, code: (
                promoted if path == contract_path else original_load(path, code)
            )
            with self.assertRaises(foundation.QualificationError):
                qualification.verify(ROOT)


if __name__ == "__main__":
    unittest.main()
