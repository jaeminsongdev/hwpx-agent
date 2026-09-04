from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tools" / "p10" / "validate_worker_supervision.py"
SPEC = importlib.util.spec_from_file_location("validate_worker_supervision", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
POLICY_PATH = (
    ROOT
    / "implementation"
    / "p10"
    / "supervision"
    / "p10-current-pc-worker-supervisor-policy.json"
)


class WorkerSupervisorPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = MODULE.load_json(POLICY_PATH)

    def test_current_policy_is_strictly_valid(self) -> None:
        validated = MODULE.validate_policy(POLICY_PATH)
        self.assertFalse(validated["scope_limits"]["production_or_provider_qualified"])
        self.assertFalse(
            validated["reconciliation"]["same_execution_automatic_replay_allowed"]
        )

    def test_unbounded_timeout_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.policy)
        tampered["timeouts"]["process_recycle_seconds"] = 61
        with self.assertRaises(ValueError):
            MODULE.validate_document(
                tampered, "worker-supervisor-policy-v1.schema.json"
            )

    def test_same_execution_replay_promotion_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.policy)
        tampered["reconciliation"]["same_execution_automatic_replay_allowed"] = True
        with self.assertRaises(ValueError):
            MODULE.validate_document(
                tampered, "worker-supervisor-policy-v1.schema.json"
            )

    def test_unowned_process_termination_promotion_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.policy)
        tampered["process_ownership"]["unowned_process_termination_allowed"] = True
        with self.assertRaises(ValueError):
            MODULE.validate_document(
                tampered, "worker-supervisor-policy-v1.schema.json"
            )

    def test_recursive_delete_promotion_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.policy)
        tampered["startup_recovery"]["recursive_delete_allowed"] = True
        with self.assertRaises(ValueError):
            MODULE.validate_document(
                tampered, "worker-supervisor-policy-v1.schema.json"
            )

    def test_target_build_drift_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.policy)
        tampered["target"]["product_build"] = "13.0.0.0"
        with self.assertRaises(ValueError):
            MODULE.validate_document(
                tampered, "worker-supervisor-policy-v1.schema.json"
            )

    def test_unknown_property_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.policy)
        tampered["force_retry"] = True
        with self.assertRaises(ValueError):
            MODULE.validate_document(
                tampered, "worker-supervisor-policy-v1.schema.json"
            )

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"policy_id":"a","policy_id":"b"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.load_json(path)

    def test_canonical_audit_is_valid(self) -> None:
        audit = self._canonical_audit()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.json"
            path.write_text(json.dumps(audit), encoding="utf-8")
            validated = MODULE.validate_audit(
                path, self.policy, self._policy_sha256()
            )
        self.assertEqual(validated["execution"]["test_count"], 28)

    def test_audit_policy_digest_drift_is_rejected(self) -> None:
        audit = self._canonical_audit()
        audit["policy_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.json"
            path.write_text(json.dumps(audit), encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.validate_audit(path, self.policy, self._policy_sha256())

    @staticmethod
    def _policy_sha256() -> str:
        return hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest()

    def _canonical_audit(self) -> dict[str, object]:
        return {
            "schema_version": "hwpx-agent.p10-09-worker-supervisor-audit/v1",
            "generated_at_utc": "2026-09-04T00:00:00Z",
            "state": "pass_current_pc_development_only",
            "policy_relative_path": (
                "implementation/p10/supervision/"
                "p10-current-pc-worker-supervisor-policy.json"
            ),
            "policy_sha256": self._policy_sha256(),
            "host_baseline_verification": {
                "state": "pass",
                "baseline_digest_sha256": self.policy["target"][
                    "host_baseline_sha256"
                ],
                "verification_sha256": "1" * 64,
            },
            "execution": {
                "agent_smoke_assembly_sha256": "2" * 64,
                "source_revision": "3" * 40,
                "source_tree_clean": True,
                "release_build_succeeded": True,
                "exit_code": 0,
                "stdout_sha256": "4" * 64,
                "expected_marker_present": True,
                "test_count": 28,
            },
            "observed_invariants": {
                "hancom_process_count_before": 0,
                "hancom_process_count_after": 0,
                "hard_timeout_exercised": True,
                "unknown_outcome_reconciliation_exercised": True,
                "proved_no_effect_retryable_exercised": True,
                "same_execution_terminal_replay_exercised": True,
                "duplicate_executor_effect_count": 0,
                "windows_job_object_tree_termination_exercised": True,
                "owned_descendant_exit_verified": True,
                "startup_quarantine_exercised": True,
                "ambiguous_residue_fail_closed_exercised": True,
            },
            "scope": {
                "target_profile_id": self.policy["target"]["profile_id"],
                "product_build": self.policy["target"]["product_build"],
                "process_architecture": self.policy["target"][
                    "process_architecture"
                ],
                "current_pc_local_development_qualified": True,
                "production_or_provider_qualified": False,
                "another_hancom_version_qualified": False,
            },
            "privacy": {
                "raw_process_command_line_present": False,
                "raw_document_text_present": False,
                "user_document_scanned": False,
                "external_network_invoked": False,
                "system_setting_changed": False,
            },
        }


if __name__ == "__main__":
    unittest.main()
