from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.p02.extract_help import ExtractionError
from tools.p02.plan_runtime_probe import build_request, serialize
from tools.p02.registry_signing import (
    SignedRegistryVerificationConfig,
    build_payload,
    canonical_json,
    compare_registry_drift,
    create_envelope,
    create_key_pair_material,
    expected_qualification,
    generate_key_pair,
    parse_private_key,
    public_key_material,
    parse_public_key,
    serialize_json,
    sha256_bytes,
    verify_envelope_content,
    verify_signed_registry,
    validate_schema,
)
from tools.p02.tests.test_runtime_probe import (
    CONTRACTS_PATH,
    CONTRACTS_SHA,
    PROFILE_PATH,
    PROFILE_SHA,
    contracts,
    passing_receipt,
    passing_trace,
    plan_config,
    synthetic_registry,
)


SOURCE_COMMIT = "a" * 40


def synthetic_chain() -> dict[str, object]:
    registry = synthetic_registry()
    registry_bytes = serialize(registry)
    registry_sha = sha256_bytes(registry_bytes)
    request = build_request(plan_config(registry_sha), registry, contracts())
    request_bytes = serialize(request)
    request_sha = sha256_bytes(request_bytes)
    trace = passing_trace(request, request_sha, registry_sha)
    trace_bytes = serialize(trace)
    trace_sha = sha256_bytes(trace_bytes)
    receipt = passing_receipt(request, request_sha, trace_sha, registry_sha)
    receipt_bytes = serialize(receipt)
    receipt_sha = sha256_bytes(receipt_bytes)
    payload = build_payload(
        registry_bytes,
        registry,
        request,
        trace,
        receipt,
        PROFILE_SHA,
        request_sha,
        trace_sha,
        receipt_sha,
        SOURCE_COMMIT,
    )
    private_pem, public_pem, key_id = create_key_pair_material()
    private_key = parse_private_key(private_pem)
    envelope = create_envelope(payload, private_key)
    return {
        "registry": registry,
        "registry_bytes": registry_bytes,
        "registry_sha": registry_sha,
        "request": request,
        "request_bytes": request_bytes,
        "request_sha": request_sha,
        "trace": trace,
        "trace_bytes": trace_bytes,
        "trace_sha": trace_sha,
        "receipt": receipt,
        "receipt_bytes": receipt_bytes,
        "receipt_sha": receipt_sha,
        "payload": payload,
        "private_pem": private_pem,
        "private_key": private_key,
        "public_pem": public_pem,
        "public_sha": sha256_bytes(public_pem),
        "key_id": key_id,
        "envelope": envelope,
        "envelope_bytes": serialize_json(envelope),
    }


def verified_chain(chain: dict[str, object]):
    return verify_envelope_content(
        chain["envelope_bytes"], chain["public_pem"], chain["public_sha"]
    )


class RegistrySigningTests(unittest.TestCase):
    def test_actual_local_trust_policy_matches_public_key(self) -> None:
        root = Path(__file__).resolve().parents[3]
        policy_path = (
            root
            / "implementation/p02/trust/p02-current-pc-local-trust-policy.json"
        )
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        validate_schema(
            policy,
            root / "tools/p02/schemas/registry-trust-policy-v1.schema.json",
            "registry trust policy",
        )
        public_path = root / policy["public_key"]["relative_path"]
        public_bytes = public_path.read_bytes()
        self.assertEqual(sha256_bytes(public_bytes), policy["public_key"]["sha256"])
        _, key_id = public_key_material(parse_public_key(public_bytes))
        self.assertEqual(key_id, policy["key_id"])

    def test_cli_entrypoints_bootstrap_repository_imports(self) -> None:
        root = Path(__file__).resolve().parents[3]
        for relative in (
            "tools/p02/generate_signing_key.py",
            "tools/p02/sign_registry.py",
            "tools/p02/verify_signed_registry.py",
            "tools/p02/compare_registry_drift.py",
        ):
            result = subprocess.run(
                [sys.executable, str(root / relative), "--help"],
                cwd=root,
                capture_output=True,
                check=False,
                text=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, f"{relative}: {result.stderr}")

    def test_ed25519_envelope_is_deterministic_and_verifiable(self) -> None:
        chain = synthetic_chain()
        first = create_envelope(chain["payload"], chain["private_key"])
        second = create_envelope(deepcopy(chain["payload"]), chain["private_key"])
        self.assertEqual(serialize_json(first), serialize_json(second))
        verified = verified_chain(chain)
        self.assertEqual(verified.envelope["key_id"], chain["key_id"])
        self.assertEqual(verified.registry_bytes, chain["registry_bytes"])

    def test_qualification_promotes_only_verified_canaries(self) -> None:
        chain = synthetic_chain()
        qualification = chain["payload"]["qualification"]
        self.assertEqual(
            qualification["state"], "partially_qualified_scoped_current_target"
        )
        states = {
            row["capability_id"]: row["runtime_support_state"]
            for row in qualification["bindings"]
        }
        self.assertEqual(states["edit.undo"], "verified_current_target")
        self.assertEqual(states["edit.redo"], "verified_current_target")
        self.assertEqual(states["edit.go_to"], "unverified_not_run")
        self.assertEqual(states["edit.copy"], "blocked_by_policy")
        self.assertEqual(qualification["coverage"]["verified_count"], 2)
        self.assertEqual(qualification["coverage"]["routing_enabled_count"], 0)

    def test_failed_default_read_is_not_promoted(self) -> None:
        chain = synthetic_chain()
        trace = deepcopy(chain["trace"])
        row = next(
            item for item in trace["probe_results"] if item["capability_id"] == "edit.go_to"
        )
        row.update(
            disposition="failed",
            default_read_state="failed",
            default_member_count=0,
            default_shape_sha256=None,
            error_type="Synthetic.RuntimeException",
            error_hresult=-1,
            error_message_sha256="9" * 64,
        )
        qualification = expected_qualification(
            chain["registry"],
            trace,
            chain["request_sha"],
            chain["trace_sha"],
            chain["receipt_sha"],
        )
        failed = next(
            item for item in qualification["bindings"] if item["capability_id"] == "edit.go_to"
        )
        self.assertEqual(failed["runtime_support_state"], "failed_current_target")
        self.assertFalse(failed["routing_enabled"])

    def test_payload_tamper_is_rejected(self) -> None:
        chain = synthetic_chain()
        tampered = deepcopy(chain["envelope"])
        tampered["payload"]["release_policy"]["production_release_state"] = "enabled"
        tampered["payload_sha256"] = sha256_bytes(canonical_json(tampered["payload"]))
        with self.assertRaisesRegex(ExtractionError, "schema invalid|signature verification failed"):
            verify_envelope_content(
                serialize_json(tampered), chain["public_pem"], chain["public_sha"]
            )

    def test_wrong_trust_anchor_is_rejected(self) -> None:
        chain = synthetic_chain()
        _, other_public, _ = create_key_pair_material()
        with self.assertRaisesRegex(ExtractionError, "key ID mismatch|signature"):
            verify_envelope_content(
                chain["envelope_bytes"], other_public, sha256_bytes(other_public)
            )

    def test_embedded_registry_tamper_is_rejected(self) -> None:
        chain = synthetic_chain()
        tampered = deepcopy(chain["envelope"])
        encoded = tampered["payload"]["source_registry"]["bytes_base64"]
        registry_bytes = bytearray(base64.b64decode(encoded))
        registry_bytes[-2] ^= 1
        tampered["payload"]["source_registry"]["bytes_base64"] = base64.b64encode(
            registry_bytes
        ).decode("ascii")
        tampered["payload"]["source_registry"]["sha256"] = sha256_bytes(registry_bytes)
        tampered["payload_sha256"] = sha256_bytes(canonical_json(tampered["payload"]))
        with self.assertRaisesRegex(ExtractionError, "signature verification failed"):
            verify_envelope_content(
                serialize_json(tampered), chain["public_pem"], chain["public_sha"]
            )

    def test_full_independent_verifier_accepts_complete_chain(self) -> None:
        chain = synthetic_chain()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = {
                "registry": root / "registry.json",
                "request": root / "request.json",
                "trace": root / "trace.json",
                "receipt": root / "receipt.json",
                "envelope": root / "signed.json",
                "public": root / "public.pem",
            }
            for name in ("registry", "request", "trace", "receipt", "envelope", "public"):
                paths[name].write_bytes(chain[f"{name}_bytes"] if f"{name}_bytes" in chain else chain["public_pem"])
            result = verify_signed_registry(
                SignedRegistryVerificationConfig(
                    signed_registry=paths["envelope"],
                    signed_registry_sha256=sha256_bytes(chain["envelope_bytes"]),
                    public_key=paths["public"],
                    public_key_sha256=chain["public_sha"],
                    registry=paths["registry"],
                    registry_sha256=chain["registry_sha"],
                    target_profile=PROFILE_PATH,
                    profile_sha256=PROFILE_SHA,
                    contracts=CONTRACTS_PATH,
                    contracts_sha256=CONTRACTS_SHA,
                    request=paths["request"],
                    request_sha256=chain["request_sha"],
                    trace=paths["trace"],
                    trace_sha256=chain["trace_sha"],
                    receipt=paths["receipt"],
                    receipt_sha256=chain["receipt_sha"],
                )
            )
            self.assertEqual(result["state"], "pass", result["errors"])
            self.assertTrue(result["signature_valid"])
            self.assertTrue(result["runtime_evidence_valid"])
            self.assertEqual(result["raw_identifier_value_leak_count"], 0)

    def test_baseline_unavailable_is_not_reported_as_cross_build_pass(self) -> None:
        chain = synthetic_chain()
        report = compare_registry_drift(verified_chain(chain), None)
        self.assertEqual(report["state"], "pass")
        self.assertEqual(report["baseline_state"], "baseline_unavailable")
        self.assertEqual(report["summary"]["compared_capability_count"], 0)
        self.assertEqual(report["changes"], [])

    def test_drift_report_hashes_raw_changes_and_demotes_support(self) -> None:
        baseline_chain = synthetic_chain()
        baseline = verified_chain(baseline_chain)
        current_payload = deepcopy(baseline_chain["payload"])
        current_payload["lineage"] = {
            "registry_sequence": 2,
            "parent_payload_sha256": baseline.envelope["payload_sha256"],
        }
        registry_bytes = base64.b64decode(
            current_payload["source_registry"]["bytes_base64"]
        )
        registry = json.loads(registry_bytes.decode("utf-8"))
        copy_binding = next(
            row for row in registry["bindings"] if row["capability_id"] == "edit.copy"
        )
        copy_binding["invocation"]["action_id"] = "ChangedSyntheticCopy"
        goto_binding = next(
            row for row in registry["bindings"] if row["capability_id"] == "edit.go_to"
        )
        goto_binding["invocation"]["parameter_set_id"] = "ChangedSyntheticGotoSet"
        new_registry_bytes = serialize(registry)
        current_payload["source_registry"]["bytes_base64"] = base64.b64encode(
            new_registry_bytes
        ).decode("ascii")
        current_payload["source_registry"]["sha256"] = sha256_bytes(new_registry_bytes)
        undo_overlay = next(
            row
            for row in current_payload["qualification"]["bindings"]
            if row["capability_id"] == "edit.undo"
        )
        undo_overlay["evidence"]["post_snapshot_sha256"] = "8" * 64
        current_envelope = create_envelope(
            current_payload, baseline_chain["private_key"]
        )
        current = verify_envelope_content(
            serialize_json(current_envelope),
            baseline_chain["public_pem"],
            baseline_chain["public_sha"],
        )
        report = compare_registry_drift(current, baseline)
        self.assertEqual(report["summary"]["binding_changed_count"], 1)
        self.assertEqual(report["summary"]["parameter_changed_count"], 1)
        self.assertEqual(report["summary"]["behavior_changed_count"], 1)
        self.assertEqual(report["summary"]["unverified_for_build_count"], 3)
        serialized = serialize_json(report).decode("utf-8")
        self.assertNotIn("ChangedSyntheticCopy", serialized)
        self.assertNotIn("ChangedSyntheticGotoSet", serialized)

    def test_drift_rejects_signed_rollback_and_wrong_parent(self) -> None:
        baseline_chain = synthetic_chain()
        baseline = verified_chain(baseline_chain)
        rollback_payload = deepcopy(baseline_chain["payload"])
        rollback_payload["lineage"]["parent_payload_sha256"] = baseline.envelope[
            "payload_sha256"
        ]
        rollback_envelope = create_envelope(
            rollback_payload, baseline_chain["private_key"]
        )
        rollback = verify_envelope_content(
            serialize_json(rollback_envelope),
            baseline_chain["public_pem"],
            baseline_chain["public_sha"],
        )
        with self.assertRaisesRegex(ExtractionError, "sequence is not monotonic"):
            compare_registry_drift(rollback, baseline)

        wrong_parent_payload = deepcopy(baseline_chain["payload"])
        wrong_parent_payload["lineage"] = {
            "registry_sequence": 2,
            "parent_payload_sha256": "f" * 64,
        }
        wrong_parent_envelope = create_envelope(
            wrong_parent_payload, baseline_chain["private_key"]
        )
        wrong_parent = verify_envelope_content(
            serialize_json(wrong_parent_envelope),
            baseline_chain["public_pem"],
            baseline_chain["public_sha"],
        )
        with self.assertRaisesRegex(ExtractionError, "parent payload mismatch"):
            compare_registry_drift(wrong_parent, baseline)

    def test_key_generation_is_no_overwrite_and_receipt_has_no_private_material(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            private_root = root / "private"
            public_root = root / "public"
            private_root.mkdir()
            public_root.mkdir()
            receipt = generate_key_pair(
                private_root,
                "key.pem",
                public_root,
                "key.pub.pem",
            )
            self.assertFalse(receipt["private_key_material_printed"])
            self.assertTrue((private_root / "key.pem").is_file())
            self.assertTrue((public_root / "key.pub.pem").is_file())
            with self.assertRaisesRegex(ExtractionError, "already exists"):
                generate_key_pair(
                    private_root,
                    "key.pem",
                    public_root,
                    "key.pub.pem",
                )

    def test_public_key_id_is_stable_for_same_key(self) -> None:
        private_pem, public_pem, key_id = create_key_pair_material()
        private_key = parse_private_key(private_pem)
        exported, exported_id = public_key_material(private_key.public_key())
        self.assertEqual(public_pem, exported)
        self.assertEqual(key_id, exported_id)
        self.assertEqual(hashlib.sha256(public_pem).hexdigest(), sha256_bytes(exported))


if __name__ == "__main__":
    unittest.main()
