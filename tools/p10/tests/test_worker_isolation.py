from __future__ import annotations

import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tools" / "p10" / "validate_worker_isolation.py"
SPEC = importlib.util.spec_from_file_location("validate_worker_isolation", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
POLICY_PATH = (
    ROOT
    / "implementation"
    / "p10"
    / "isolation"
    / "p10-current-pc-local-worker-policy.json"
)


class WorkerIsolationPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = MODULE.load_json(POLICY_PATH)

    def test_current_policy_is_strictly_valid(self) -> None:
        validated = MODULE.validate_policy(POLICY_PATH)
        self.assertFalse(validated["worker_image"]["production_isolation_qualified"])
        self.assertFalse(validated["worker_image"]["release_routable"])

    def test_production_overclaim_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.policy)
        tampered["worker_image"]["production_isolation_qualified"] = True
        with self.assertRaises(ValueError):
            MODULE.validate_document(tampered, "worker-isolation-policy-v1.schema.json")

    def test_unqualified_control_promotion_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.policy)
        tampered["unqualified_dedicated_controls"]["clipboard_isolated"] = True
        with self.assertRaises(ValueError):
            MODULE.validate_document(tampered, "worker-isolation-policy-v1.schema.json")

    def test_target_build_drift_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.policy)
        tampered["target"]["product_build"] = "11.0.0.0"
        with self.assertRaises(ValueError):
            MODULE.validate_document(tampered, "worker-isolation-policy-v1.schema.json")

    def test_target_executable_digest_drift_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.policy)
        tampered["target"]["executable_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            MODULE.validate_document(tampered, "worker-isolation-policy-v1.schema.json")

    def test_host_isolation_identity_drift_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.policy)
        tampered["target"]["host_isolation_identity_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            MODULE.validate_document(tampered, "worker-isolation-policy-v1.schema.json")

    def test_unknown_property_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.policy)
        tampered["allow_shared_clipboard"] = True
        with self.assertRaises(ValueError):
            MODULE.validate_document(tampered, "worker-isolation-policy-v1.schema.json")

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"scope":"a","scope":"b"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.load_json(path)


if __name__ == "__main__":
    unittest.main()
