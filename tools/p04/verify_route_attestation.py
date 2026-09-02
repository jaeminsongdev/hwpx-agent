from __future__ import annotations

import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


ROOT = Path(__file__).resolve().parents[2]
TRUST = ROOT / "implementation" / "p04" / "trust"


def fail(code: str) -> None:
    raise SystemExit(code)


def exact_keys(value: dict[str, object], expected: set[str], code: str) -> None:
    if set(value) != expected:
        fail(code)


def main() -> int:
    policy = json.loads((TRUST / "p04-direct-route-trust-policy.json").read_text("utf-8"))
    exact_keys(
        policy,
        {
            "schema_version",
            "attestation_relative_path",
            "attestation_sha256",
            "signature_relative_path",
            "signature_raw_sha256",
            "algorithm",
            "key_id",
            "public_key",
            "minimum_sequence",
            "allowed_capability_id",
            "allowed_backend_id",
            "scope",
        },
        "P04_ROUTE_POLICY_FIELDS_INVALID",
    )
    public_record = policy["public_key"]
    if not isinstance(public_record, dict):
        fail("P04_ROUTE_PUBLIC_KEY_RECORD_INVALID")
    exact_keys(public_record, {"relative_path", "pem_sha256", "raw_hex"}, "P04_ROUTE_PUBLIC_KEY_FIELDS_INVALID")
    if (
        policy["schema_version"] != "hwpx-agent.direct-route-trust-policy/v1"
        or policy["attestation_relative_path"]
        != "implementation/p04/trust/p04-direct-route-attestation.json"
        or policy["signature_relative_path"]
        != "implementation/p04/trust/p04-direct-route-attestation.sig"
        or public_record["relative_path"]
        != "implementation/p04/trust/p04-current-pc-direct-route-public.pem"
        or policy["algorithm"] != "Ed25519"
        or policy["minimum_sequence"] != 1
        or policy["allowed_capability_id"] != "document.create_vs0"
        or policy["allowed_backend_id"] != "direct-hwpx-vs0"
        or policy["scope"] != "current_pc_personal_local_development_only"
    ):
        fail("P04_ROUTE_POLICY_VALUE_INVALID")

    attestation_path = ROOT / str(policy["attestation_relative_path"])
    signature_path = ROOT / str(policy["signature_relative_path"])
    public_path = ROOT / str(public_record["relative_path"])
    payload = attestation_path.read_bytes()
    signature_text = signature_path.read_text("ascii")
    public_pem = public_path.read_bytes()
    try:
        signature = bytes.fromhex(signature_text.strip())
        raw_public = bytes.fromhex(str(public_record["raw_hex"]))
    except ValueError:
        fail("P04_ROUTE_HEX_INVALID")
    if len(signature) != 64 or len(raw_public) != 32:
        fail("P04_ROUTE_CRYPTO_LENGTH_INVALID")
    if hashlib.sha256(payload).hexdigest() != policy["attestation_sha256"]:
        fail("P04_ROUTE_ATTESTATION_DIGEST_MISMATCH")
    if hashlib.sha256(signature).hexdigest() != policy["signature_raw_sha256"]:
        fail("P04_ROUTE_SIGNATURE_DIGEST_MISMATCH")
    if hashlib.sha256(public_pem).hexdigest() != public_record["pem_sha256"]:
        fail("P04_ROUTE_PUBLIC_KEY_DIGEST_MISMATCH")
    if "\r" in signature_text or not signature_text.endswith("\n"):
        fail("P04_ROUTE_SIGNATURE_ENCODING_INVALID")
    public_key = serialization.load_pem_public_key(public_pem)
    if not isinstance(public_key, Ed25519PublicKey):
        fail("P04_ROUTE_PUBLIC_KEY_TYPE_INVALID")
    if public_key.public_bytes_raw() != raw_public:
        fail("P04_ROUTE_PUBLIC_KEY_RAW_MISMATCH")
    try:
        public_key.verify(signature, payload)
    except Exception:
        fail("P04_ROUTE_SIGNATURE_INVALID")

    attestation = json.loads(payload)
    exact_keys(
        attestation,
        {"schema_version", "attestation_id", "sequence", "target", "route", "basis", "scope", "trust_anchor"},
        "P04_ROUTE_ATTESTATION_FIELDS_INVALID",
    )
    expected = {
        "schema_version": "hwpx-agent.direct-route-attestation/v1",
        "sequence": policy["minimum_sequence"],
        "capability": policy["allowed_capability_id"],
        "backend": policy["allowed_backend_id"],
        "profile": "hancom-hangul-2020-secondary",
        "build": "11.0.0.9136",
        "architecture": "x86",
        "key_id": policy["key_id"],
    }
    if (
        attestation["schema_version"] != expected["schema_version"]
        or attestation["sequence"] != expected["sequence"]
        or attestation["route"]["capability_id"] != expected["capability"]
        or attestation["route"]["backend_id"] != expected["backend"]
        or attestation["target"]["profile_id"] != expected["profile"]
        or attestation["target"]["exact_build"] != expected["build"]
        or attestation["target"]["architecture"] != expected["architecture"]
        or attestation["trust_anchor"]["key_id"] != expected["key_id"]
        or attestation["route"]["support"] != "verified_current_pc_local"
        or attestation["scope"]["direct_hwpx_route_allowed"] is not True
        or any(
            attestation["scope"][field] is not False
            for field in (
                "production_allowed",
                "provider_allowed",
                "network_allowed",
                "desktop_automation_route_allowed",
            )
        )
    ):
        fail("P04_ROUTE_SCOPE_INVALID")
    print(
        json.dumps(
            {
                "schema_version": "hwpx-agent.direct-route-verification/v1",
                "state": "pass",
                "attestation_sha256": policy["attestation_sha256"],
                "signature_valid": True,
                "target_profile_id": expected["profile"],
                "exact_build": expected["build"],
                "capability_id": expected["capability"],
                "backend_id": expected["backend"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
