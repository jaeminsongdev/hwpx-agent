from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import current_workspace_source_qualification_v41 as qualification


ROOT = Path(__file__).resolve().parents[3]


class CurrentWorkspaceSourceQualificationV41Tests(unittest.TestCase):
    def test_exact_current_source_and_runtime_qualification_pass(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(
            result["qualification_id"],
            "p17.current-workspace-source.v41.20260910",
        )
        self.assertEqual(result["source_successor_count"], 28)
        self.assertEqual(len(result["implementation_sources"]), 20)
        self.assertEqual(len(result["runtime_qualification_sources"]), 6)
        self.assertEqual(len(result["guard_sources"]), 3)

    def test_bounded_runtime_claims_are_promoted_without_phase_promotion(self) -> None:
        claims = qualification.verify(ROOT)["claims"]
        self.assertTrue(claims["p17_git_mirror_authenticated_dispatch_verified"])
        self.assertTrue(claims["p17_git_mirror_postgresql_state_machine_verified"])
        self.assertTrue(claims["p17_disposable_local_bare_git_push_verified"])
        self.assertTrue(claims["p17_committed_push_recovery_verified"])
        self.assertFalse(claims["p17_durable_pull_verified"])
        self.assertFalse(claims["p17_git_mirror_remote_network_verified"])
        self.assertFalse(claims["p17_06_complete"])
        self.assertFalse(claims["production"])
        self.assertFalse(claims["product_complete"])

    def test_runtime_qualification_claim_tamper_fails_closed(self) -> None:
        original = qualification.runtime.verify

        def tampered(root: Path) -> dict[str, object]:
            contract = dict(original(root))
            claims = dict(contract["claims"])
            claims["actual_remote_network"] = True
            contract["claims"] = claims
            return contract

        with patch.object(qualification.runtime, "verify", side_effect=tampered):
            with self.assertRaisesRegex(
                qualification.foundation.QualificationError, "runtime.claims"
            ):
                qualification.verify(ROOT)

    def test_implementation_history_tamper_fails_closed(self) -> None:
        original = qualification.foundation.git_digest

        def tampered(root: Path, revision: str, relative: str) -> str:
            observed = original(root, revision, relative)
            if relative == "crates/remote-sync-host/src/durable_git_push.rs":
                return "0" * 64
            return observed

        with patch.object(
            qualification.foundation, "git_digest", side_effect=tampered
        ):
            with self.assertRaisesRegex(
                qualification.foundation.QualificationError,
                "implementation.history",
            ):
                qualification.verify(ROOT)


if __name__ == "__main__":
    unittest.main()
