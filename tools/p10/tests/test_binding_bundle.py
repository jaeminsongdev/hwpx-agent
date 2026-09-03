from __future__ import annotations

import base64
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from tools.p02.extract_help import ExtractionError
from tools.p02.registry_signing import (
    create_envelope,
    create_key_pair_material,
    parse_public_key,
    public_key_material,
    serialize_json,
    sha256_bytes,
)
from tools.p02.tests.test_registry_signing import synthetic_chain
from tools.p10.binding_bundle import (
    BUILD_RECEIPT_SCHEMA,
    _receipt,
    project_payload,
    sign_payload,
    validate_schema,
    verify_signed_bundle,
)


BUNDLE_ID = "hancom.synthetic.runtime_verified_v1"


def capability_registry(*identifiers: str) -> bytes:
    return serialize_json(
        {
            "schema_version": "hwpx-agent.capability-contract-registry/v1",
            "generated_at": "2026-09-04T00:00:00Z",
            "source": "synthetic-test-only",
            "count": len(identifiers),
            "warning": "synthetic",
            "contracts": [
                {"capability_id": identifier, "synthetic": True}
                for identifier in identifiers
            ],
        }
    )


def projection_material():
    chain = synthetic_chain()
    capabilities = capability_registry(
        "edit.undo",
        "edit.redo",
        "edit.go_to",
        "metadata.haction_reference",
    )
    capabilities_sha = sha256_bytes(capabilities)
    payload, metadata = project_payload(
        chain["envelope_bytes"],
        chain["public_pem"],
        chain["public_sha"],
        capabilities,
        capabilities_sha,
        BUNDLE_ID,
        1,
    )
    private_pem, public_pem, _ = create_key_pair_material()
    envelope_bytes, envelope = sign_payload(
        payload,
        private_pem,
        public_pem,
        sha256_bytes(public_pem),
    )
    return {
        "chain": chain,
        "capabilities": capabilities,
        "capabilities_sha": capabilities_sha,
        "payload": payload,
        "metadata": metadata,
        "private_pem": private_pem,
        "public_pem": public_pem,
        "public_sha": sha256_bytes(public_pem),
        "envelope_bytes": envelope_bytes,
        "envelope": envelope,
    }


class BindingBundleBuilderTests(unittest.TestCase):
    def test_actual_local_trust_policy_matches_public_key_and_source_pins(self) -> None:
        root = Path(__file__).resolve().parents[3]
        policy_path = (
            root / "implementation/p10/trust/p10-current-pc-local-trust-policy.json"
        )
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        validate_schema(
            policy,
            root / "tools/p10/schemas/binding-trust-policy-v1.schema.json",
            "P10 binding trust policy",
        )
        public_bytes = (root / policy["public_key"]["relative_path"]).read_bytes()
        self.assertEqual(sha256_bytes(public_bytes), policy["public_key"]["sha256"])
        _, key_id = public_key_material(parse_public_key(public_bytes))
        self.assertEqual(key_id, policy["key_id"])
        capability_path = (
            root / policy["source_projection"]["capability_registry_relative_path"]
        )
        self.assertEqual(
            sha256_bytes(capability_path.read_bytes()),
            policy["source_projection"]["capability_registry_sha256"],
        )

    def test_projects_only_runtime_verified_current_target_bindings(self) -> None:
        material = projection_material()
        bindings = material["payload"]["bindings"]
        self.assertEqual(
            [row["capability_id"] for row in bindings],
            ["edit.redo", "edit.undo"],
        )
        self.assertTrue(all(row["parameter_set_id"] is None for row in bindings))
        self.assertTrue(all(row["parameters"] == [] for row in bindings))
        self.assertEqual(material["metadata"]["binding_count"], 2)
        self.assertFalse(
            material["payload"]["authorization"]["source_registry_routing_enabled"]
        )

    def test_signed_bundle_round_trips_exact_canonical_payload(self) -> None:
        material = projection_material()
        payload, envelope = verify_signed_bundle(
            material["envelope_bytes"],
            material["public_pem"],
            material["public_sha"],
        )
        self.assertEqual(payload, material["payload"])
        self.assertEqual(envelope, material["envelope"])
        decoded = base64.b64decode(envelope["payload_base64"], validate=True)
        self.assertEqual(sha256_bytes(decoded), envelope["payload_sha256"])

    def test_receipt_is_redacted_and_schema_valid(self) -> None:
        material = projection_material()
        receipt = _receipt(
            material["payload"],
            material["envelope"],
            material["envelope_bytes"],
            material["metadata"],
        )
        validate_schema(receipt, BUILD_RECEIPT_SCHEMA, "synthetic P10 receipt")
        serialized = serialize_json(receipt).decode("utf-8")
        for row in material["payload"]["bindings"]:
            self.assertNotIn(row["action_id"], serialized)
        self.assertFalse(receipt["raw_identifier_values_in_receipt"])
        self.assertFalse(receipt["private_key_material_printed"])

    def test_unverified_failed_and_blocked_bindings_are_not_projected(self) -> None:
        material = projection_material()
        identifiers = {row["capability_id"] for row in material["payload"]["bindings"]}
        self.assertNotIn("edit.go_to", identifiers)
        self.assertNotIn("edit.copy", identifiers)

    def test_capability_registry_omission_fails_closed(self) -> None:
        chain = synthetic_chain()
        capabilities = capability_registry("edit.undo")
        with self.assertRaisesRegex(
            ExtractionError, "absent from the contract registry"
        ):
            project_payload(
                chain["envelope_bytes"],
                chain["public_pem"],
                chain["public_sha"],
                capabilities,
                sha256_bytes(capabilities),
                BUNDLE_ID,
                1,
            )

    def test_parameter_candidate_without_typed_projection_fails_closed(self) -> None:
        chain = synthetic_chain()
        changed_payload = deepcopy(chain["payload"])
        registry = json.loads(
            base64.b64decode(
                changed_payload["source_registry"]["bytes_base64"], validate=True
            ).decode("utf-8")
        )
        undo = next(
            row for row in registry["bindings"] if row["capability_id"] == "edit.undo"
        )
        undo["invocation"]["parameter_set_id"] = "SyntheticParameterSet"
        undo["invocation"]["parameter_set_state"] = "documented_candidate"
        registry_bytes = serialize_json(registry)
        changed_payload["source_registry"]["bytes_base64"] = base64.b64encode(
            registry_bytes
        ).decode("ascii")
        changed_payload["source_registry"]["sha256"] = sha256_bytes(registry_bytes)
        resigned = create_envelope(changed_payload, chain["private_key"])
        capabilities = capability_registry("edit.undo", "edit.redo")
        with self.assertRaisesRegex(ExtractionError, "finite typed P10 projection"):
            project_payload(
                serialize_json(resigned),
                chain["public_pem"],
                chain["public_sha"],
                capabilities,
                sha256_bytes(capabilities),
                BUNDLE_ID,
                1,
            )

    def test_signature_tamper_and_wrong_key_fail_closed(self) -> None:
        material = projection_material()
        tampered = bytearray(material["envelope_bytes"])
        signature_offset = material["envelope_bytes"].find(b'"signature_base64"')
        self.assertGreater(signature_offset, 0)
        index = material["envelope_bytes"].find(b'"', signature_offset + 20) + 1
        tampered[index] = ord("A") if tampered[index] != ord("A") else ord("B")
        with self.assertRaises(ExtractionError):
            verify_signed_bundle(
                bytes(tampered), material["public_pem"], material["public_sha"]
            )
        _, other_public, _ = create_key_pair_material()
        with self.assertRaises(ExtractionError):
            verify_signed_bundle(
                material["envelope_bytes"], other_public, sha256_bytes(other_public)
            )

    def test_duplicate_json_property_is_rejected(self) -> None:
        material = projection_material()
        duplicate = material["envelope_bytes"].replace(
            b'{\n  "algorithm"', b'{\n  "algorithm": "Ed25519",\n  "algorithm"', 1
        )
        with self.assertRaisesRegex(ExtractionError, "duplicate JSON property"):
            verify_signed_bundle(
                duplicate, material["public_pem"], material["public_sha"]
            )

    def test_private_key_must_match_trusted_public_key(self) -> None:
        material = projection_material()
        other_private, _, _ = create_key_pair_material()
        with self.assertRaisesRegex(ExtractionError, "does not match"):
            sign_payload(
                material["payload"],
                other_private,
                material["public_pem"],
                material["public_sha"],
            )

    def test_cli_entrypoints_bootstrap_repository_imports(self) -> None:
        root = Path(__file__).resolve().parents[3]
        for relative in (
            "tools/p10/generate_signing_key.py",
            "tools/p10/build_signed_binding_bundle.py",
            "tools/p10/verify_signed_binding_bundle.py",
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


if __name__ == "__main__":
    unittest.main()
