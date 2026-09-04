from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tools" / "p10" / "validate_runtime_probe.py"
SPEC = importlib.util.spec_from_file_location("validate_runtime_probe", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
POLICY_PATH = (
    ROOT
    / "implementation"
    / "p10"
    / "probe"
    / "p10-current-pc-runtime-probe-policy.json"
)


class RuntimeProbePolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = MODULE.load_json(POLICY_PATH)

    def test_current_policy_and_all_pinned_files_are_valid(self) -> None:
        validated = MODULE.validate_policy(POLICY_PATH)
        self.assertEqual(validated["security_module"]["state"], "not_configured")
        self.assertFalse(validated["scope"]["production_or_provider_qualified"])

    def test_unknown_property_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.policy)
        tampered["force_routable"] = True
        with self.assertRaises(ValueError):
            MODULE.validate_document(tampered, "runtime-probe-policy-v1.schema.json")

    def test_unroutable_lease_promotion_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.policy)
        tampered["admission"]["unroutable_probe_acquires_lease"] = True
        with self.assertRaises(ValueError):
            MODULE.validate_document(tampered, "runtime-probe-policy-v1.schema.json")

    def test_user_document_scan_promotion_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.policy)
        tampered["scope"]["user_document_scan_allowed"] = True
        with self.assertRaises(ValueError):
            MODULE.validate_document(tampered, "runtime-probe-policy-v1.schema.json")

    def test_duplicate_capability_id_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.policy)
        tampered["pinned_evidence"].append(copy.deepcopy(tampered["pinned_evidence"][0]))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.validate_policy(path, verify_files=False)

    def test_not_configured_security_module_cannot_carry_pin(self) -> None:
        tampered = copy.deepcopy(self.policy)
        tampered["security_module"]["registration_name"] = "UnexpectedModule"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.validate_policy(path, verify_files=False)

    def test_pinned_file_digest_drift_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.policy)
        tampered["capability_registry"]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.validate_policy(path)

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
            validated = MODULE.validate_audit(path, self.policy, self._policy_sha256())
        self.assertEqual(validated["observation"]["acquire_lease_calls"], 0)

    def test_audit_policy_digest_drift_is_rejected(self) -> None:
        audit = self._canonical_audit()
        audit["policy_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.json"
            path.write_text(json.dumps(audit), encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.validate_audit(path, self.policy, self._policy_sha256())

    def test_missing_module_cannot_be_promoted_in_audit(self) -> None:
        audit = self._canonical_audit()
        audit["observation"]["probe_health"] = "healthy"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.json"
            path.write_text(json.dumps(audit), encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.validate_audit(path, self.policy, self._policy_sha256())

    @staticmethod
    def _policy_sha256() -> str:
        return hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest()

    def _canonical_audit(self) -> dict[str, object]:
        policy_sha = self._policy_sha256()
        observation = {
            "schema_version": "hwpx-agent.p10-10-current-host-runtime-probe/v1",
            "state": "pass_current_pc_development_only",
            "policy_sha256": policy_sha,
            "isolation_policy_sha256": self.policy["isolation_policy"]["sha256"],
            "target_profile_id": self.policy["target"]["profile_id"],
            "product_build": self.policy["target"]["product_build"],
            "process_architecture": self.policy["target"]["process_architecture"],
            "capability_registry_sha256": self.policy["capability_registry"]["sha256"],
            "probe_health": "unroutable",
            "capability_set_sha256": "1" * 64,
            "evidence_artifact_sha256": "2" * 64,
            "evidence_artifact_bytes": 2048,
            "capability_count": 9,
            "verified_capability_count": 8,
            "unavailable_capability_count": 1,
            "security_module_state": "not_registered",
            "report_probe_calls": 1,
            "acquire_lease_calls": 0,
            "executor_calls": 0,
            "profile_mismatch_no_rpc_tested": True,
            "unroutable_probe_no_lease_verified": True,
            "hancom_process_count_before": 0,
            "hancom_process_count_after": 0,
            "raw_path_present": False,
            "raw_document_content_present": False,
            "user_document_scanned": False,
            "external_network_invoked": False,
            "system_setting_changed": False,
            "hancom_process_started": False,
            "production_or_provider_qualified": False,
            "another_host_or_version_qualified": False,
        }
        return {
            "schema_version": "hwpx-agent.p10-10-runtime-probe-audit/v1",
            "generated_at_utc": "2026-09-04T00:00:00Z",
            "state": "pass_current_pc_development_only",
            "policy_relative_path": (
                "implementation/p10/probe/p10-current-pc-runtime-probe-policy.json"
            ),
            "policy_sha256": policy_sha,
            "host_baseline_verification": {
                "state": "pass",
                "baseline_digest_sha256": self.policy["target"]["host_baseline_sha256"],
                "verification_sha256": "3" * 64,
            },
            "execution": {
                "agent_smoke_assembly_sha256": "4" * 64,
                "source_revision": "5" * 40,
                "source_tree_clean": True,
                "release_build_succeeded": True,
                "full_smoke_exit_code": 0,
                "full_smoke_stdout_sha256": "6" * 64,
                "p10_10_marker_present": True,
                "agent_test_count": 32,
                "actual_probe_exit_code": 0,
                "actual_probe_stdout_sha256": "7" * 64,
            },
            "observation": observation,
            "scope": {
                "current_pc_local_development_qualified": True,
                "production_or_provider_qualified": False,
                "another_hancom_version_qualified": False,
                "another_host_qualified": False,
            },
            "privacy": {
                "raw_path_present": False,
                "raw_document_content_present": False,
                "user_document_scanned": False,
                "external_network_invoked": False,
                "system_setting_changed": False,
                "hancom_process_started": False,
            },
        }


if __name__ == "__main__":
    unittest.main()
