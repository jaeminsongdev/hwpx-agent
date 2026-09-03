#!/usr/bin/env python3
from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from cryptography.exceptions import InvalidSignature
from tools.p02.extract_help import ExtractionError, publish_no_overwrite, resolve_output
from tools.p02.registry_signing import (
    canonical_json,
    create_key_pair_material,
    parse_private_key,
    parse_public_key,
    public_key_material,
    read_locked,
    serialize_json,
    sha256_bytes,
    validate_schema,
    verify_envelope_content,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
P10_PRIVATE_OUTPUT_ROOT = REPOSITORY_ROOT / "implementation" / "p10" / "evidence"
P10_PRIVATE_KEY_ROOT = P10_PRIVATE_OUTPUT_ROOT / "signing-keys"
P10_TRUST_OUTPUT_ROOT = REPOSITORY_ROOT / "implementation" / "p10" / "trust"
P02_PRIVATE_OUTPUT_ROOT = REPOSITORY_ROOT / "implementation" / "p02" / "evidence"
P02_TRUSTED_PUBLIC_KEY_PATH = (
    REPOSITORY_ROOT
    / "implementation"
    / "p02"
    / "trust"
    / "p02-current-pc-local-ed25519-public.pem"
)
P10_TRUST_POLICY_PATH = P10_TRUST_OUTPUT_ROOT / "p10-current-pc-local-trust-policy.json"

P10_BUNDLE_SCHEMA = (
    REPOSITORY_ROOT
    / "protocol"
    / "json-schema"
    / "hancom-binding-bundle-v1.schema.json"
)
P10_ENVELOPE_SCHEMA = (
    REPOSITORY_ROOT
    / "protocol"
    / "json-schema"
    / "hancom-signed-binding-envelope-v1.schema.json"
)
BUILD_RECEIPT_SCHEMA = (
    Path(__file__).with_name("schemas") / "binding-bundle-build-receipt-v1.schema.json"
)
TRUST_POLICY_SCHEMA = (
    Path(__file__).with_name("schemas") / "binding-trust-policy-v1.schema.json"
)

EXPECTED_TARGET = {
    "profile_id": "hancom-hangul-2020-secondary",
    "product": "Hancom Hangul 2020",
    "major_release": "2020",
    "exact_build": "11.0.0.9136",
    "locale": "ko-KR",
    "architecture": "x86",
    "executable_sha256": (
        "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
    ),
}
P10_PAYLOAD_SCHEMA_VERSION = "hwpx-agent.p10-06-binding-bundle/v1"
P10_ENVELOPE_SCHEMA_VERSION = "hwpx-agent.p10-06-signed-binding-envelope/v1"
RECEIPT_SCHEMA_VERSION = "hwpx-agent.p10-06-binding-bundle-build-receipt/v1"
MAX_CAPABILITY_REGISTRY_BYTES = 8 * 1024 * 1024
MAX_P02_ENVELOPE_BYTES = 64 * 1024 * 1024
MAX_P10_ENVELOPE_BYTES = 1024 * 1024
MAX_P10_PAYLOAD_BYTES = 512 * 1024
MAX_KEY_BYTES = 64 * 1024
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
SEMANTIC_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z0-9_-]+)+$")


@dataclass(frozen=True)
class BuildConfig:
    signed_p02_registry: Path
    signed_p02_registry_sha256: str
    p02_public_key: Path
    p02_public_key_sha256: str
    capability_registry: Path
    capability_registry_sha256: str
    p10_private_key: Path
    p10_private_key_sha256: str
    p10_public_key: Path
    p10_public_key_sha256: str
    p10_trust_policy: Path
    p10_trust_policy_sha256: str
    bundle_id: str
    sequence: int
    output_root: Path
    envelope_output_relative: str
    receipt_output_relative: str


@dataclass(frozen=True)
class VerifyConfig:
    signed_p02_registry: Path
    signed_p02_registry_sha256: str
    p02_public_key: Path
    p02_public_key_sha256: str
    capability_registry: Path
    capability_registry_sha256: str
    signed_p10_bundle: Path
    signed_p10_bundle_sha256: str
    p10_public_key: Path
    p10_public_key_sha256: str
    p10_trust_policy: Path
    p10_trust_policy_sha256: str
    bundle_id: str
    sequence: int
    output_root: Path
    receipt_output_relative: str


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ExtractionError(f"duplicate JSON property: {key}")
        result[key] = value
    return result


def parse_unique_json(content: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ExtractionError(f"{label} is not valid unique UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ExtractionError(f"{label} root is not an object")
    return value


def _require_hash(value: object, label: str) -> str:
    if not isinstance(value, str) or HASH_PATTERN.fullmatch(value) is None:
        raise ExtractionError(f"{label} is not a SHA-256 digest")
    return value


def _require_private_identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 512:
        raise ExtractionError(f"{label} is not a bounded private identifier")
    if any(
        ord(character) <= 0x1F or 0x7F <= ord(character) <= 0x9F for character in value
    ):
        raise ExtractionError(f"{label} contains a control character")
    return value


def _load_capability_ids(content: bytes) -> set[str]:
    value = parse_unique_json(content, "capability contract registry")
    if value.get("schema_version") != "hwpx-agent.capability-contract-registry/v1":
        raise ExtractionError("capability contract registry schema version mismatch")
    rows = value.get("contracts")
    count = value.get("count")
    if not isinstance(rows, list) or not isinstance(count, int) or count != len(rows):
        raise ExtractionError("capability contract registry count mismatch")
    identifiers: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ExtractionError("capability contract row is not an object")
        identifier = row.get("capability_id")
        if (
            not isinstance(identifier, str)
            or SEMANTIC_ID_PATTERN.fullmatch(identifier) is None
        ):
            raise ExtractionError(
                "capability contract contains an invalid semantic identifier"
            )
        identifiers.append(identifier)
    if len(identifiers) != len(set(identifiers)):
        raise ExtractionError(
            "capability contract registry contains duplicate identifiers"
        )
    return set(identifiers)


def _load_trust_policy(content: bytes) -> dict[str, Any]:
    policy = parse_unique_json(content, "P10 binding trust policy")
    validate_schema(policy, TRUST_POLICY_SCHEMA, "P10 binding trust policy")
    return policy


def _verify_policy_inputs(
    policy: dict[str, Any],
    *,
    signed_p02_registry: Path,
    signed_p02_registry_sha256: str,
    p02_public_key: Path,
    p02_public_key_sha256: str,
    capability_registry: Path,
    capability_registry_sha256: str,
    p10_public_key: Path,
    p10_public_key_sha256: str,
    sequence: int,
) -> None:
    source = policy["source_projection"]
    if not signed_p02_registry.resolve().is_relative_to(
        P02_PRIVATE_OUTPUT_ROOT.resolve()
    ):
        raise ExtractionError(
            "signed P02 registry must stay under private P02 evidence"
        )
    if p02_public_key.resolve() != P02_TRUSTED_PUBLIC_KEY_PATH.resolve():
        raise ExtractionError(
            "P02 public key path differs from the trusted current-PC anchor"
        )
    if (
        p10_public_key.resolve()
        != (REPOSITORY_ROOT / policy["public_key"]["relative_path"]).resolve()
    ):
        raise ExtractionError(
            "P10 public key path differs from the binding trust policy"
        )
    if (
        capability_registry.resolve()
        != (REPOSITORY_ROOT / source["capability_registry_relative_path"]).resolve()
    ):
        raise ExtractionError(
            "capability registry path differs from the binding trust policy"
        )
    expected = {
        "signed P02 registry": (
            signed_p02_registry_sha256,
            source["p02_signed_registry_sha256"],
        ),
        "P02 public key": (p02_public_key_sha256, source["p02_public_key_sha256"]),
        "capability registry": (
            capability_registry_sha256,
            source["capability_registry_sha256"],
        ),
        "P10 public key": (p10_public_key_sha256, policy["public_key"]["sha256"]),
    }
    for label, (actual, pinned) in expected.items():
        if actual != pinned:
            raise ExtractionError(
                f"{label} does not match the P10 binding trust policy"
            )
    if sequence < policy["lineage"]["minimum_bundle_sequence"]:
        raise ExtractionError("P10 bundle sequence is below the trusted minimum")


def _verify_projected_policy(
    policy: dict[str, Any],
    metadata: dict[str, Any],
    envelope: dict[str, Any],
) -> None:
    source = policy["source_projection"]
    if (
        metadata["p02_payload_sha256"] != source["p02_payload_sha256"]
        or metadata["source_registry_sha256"] != source["source_registry_sha256"]
        or envelope["key_id"] != policy["key_id"]
        or envelope["public_key_sha256"] != policy["public_key"]["sha256"]
    ):
        raise ExtractionError(
            "projected P10 bundle differs from the binding trust policy"
        )


def _verify_exact_p02_target(verified: Any) -> None:
    payload = verified.payload
    target = payload.get("target")
    if not isinstance(target, dict):
        raise ExtractionError("signed P02 target is missing")
    for key, expected in EXPECTED_TARGET.items():
        if target.get(key) != expected:
            raise ExtractionError(f"signed P02 target {key} mismatch")
    release = payload.get("release_policy")
    if not isinstance(release, dict) or release != {
        "production_release_state": "disabled",
        "provider_release_state": "disabled",
        "routing_enabled": False,
        "target_scope": "current_pc_exact_identity_only",
        "use_scope": "personal_noncommercial_local_development",
    }:
        raise ExtractionError(
            "signed P02 release policy is not the current-PC local policy"
        )
    runtime = payload.get("runtime_evidence")
    if (
        not isinstance(runtime, dict)
        or runtime.get("independent_verification_state") != "pass"
    ):
        raise ExtractionError(
            "signed P02 runtime evidence was not independently verified"
        )
    qualification = payload.get("qualification")
    if (
        not isinstance(qualification, dict)
        or qualification.get("state") != "partially_qualified_scoped_current_target"
        or qualification.get("routing_enabled") is not False
    ):
        raise ExtractionError("signed P02 qualification boundary is invalid")


def _probe_evidence_digest(row: dict[str, Any], runtime: dict[str, Any]) -> str:
    evidence = row.get("evidence")
    if not isinstance(evidence, dict):
        raise ExtractionError("runtime-qualified binding has no evidence object")
    for key in ("request_sha256", "trace_sha256", "receipt_sha256"):
        if _require_hash(evidence.get(key), f"binding evidence {key}") != runtime.get(
            key
        ):
            raise ExtractionError(
                f"binding evidence {key} does not match the signed run"
            )
    for key in ("pre_snapshot_sha256", "post_snapshot_sha256"):
        _require_hash(evidence.get(key), f"binding evidence {key}")
    if (
        evidence.get("execute_state") != "pass"
        or evidence.get("expected_effect_observed") is not True
        or evidence.get("pre_snapshot_sha256") == evidence.get("post_snapshot_sha256")
    ):
        raise ExtractionError(
            "runtime-qualified binding lacks a proved semantic effect"
        )
    projection = {
        "binding_key": row.get("binding_key"),
        "capability_id": row.get("capability_id"),
        "runtime_support_state": row.get("runtime_support_state"),
        "probe_disposition": row.get("probe_disposition"),
        "evidence": evidence,
    }
    return sha256_bytes(canonical_json(projection))


def project_payload(
    signed_p02_registry: bytes,
    p02_public_key: bytes,
    p02_public_key_sha256: str,
    capability_registry: bytes,
    capability_registry_sha256: str,
    bundle_id: str,
    sequence: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    parse_unique_json(signed_p02_registry, "signed P02 registry")
    if sha256_bytes(p02_public_key) != p02_public_key_sha256:
        raise ExtractionError("P02 trusted public key SHA-256 mismatch")
    if sha256_bytes(capability_registry) != capability_registry_sha256:
        raise ExtractionError("capability registry SHA-256 mismatch")
    if SEMANTIC_ID_PATTERN.fullmatch(bundle_id) is None:
        raise ExtractionError("P10 bundle ID is not a semantic identifier")
    if "haction" in bundle_id.lower() or "parameterset" in bundle_id.lower():
        raise ExtractionError("P10 bundle ID contains a raw automation token")
    if (
        not isinstance(sequence, int)
        or isinstance(sequence, bool)
        or not 1 <= sequence <= 1_000_000_000
    ):
        raise ExtractionError("P10 bundle sequence is out of range")

    verified = verify_envelope_content(
        signed_p02_registry,
        p02_public_key,
        p02_public_key_sha256,
    )
    _verify_exact_p02_target(verified)
    capability_ids = _load_capability_ids(capability_registry)
    source_rows = verified.registry.get("bindings")
    overlay_rows = verified.payload["qualification"].get("bindings")
    if not isinstance(source_rows, list) or not isinstance(overlay_rows, list):
        raise ExtractionError("signed P02 binding collections are invalid")
    source_by_id = {
        row.get("capability_id"): row for row in source_rows if isinstance(row, dict)
    }
    if len(source_by_id) != len(source_rows):
        raise ExtractionError("signed P02 source bindings are not uniquely keyed")

    runtime = verified.payload["runtime_evidence"]
    projected: list[dict[str, Any]] = []
    for overlay in overlay_rows:
        if not isinstance(overlay, dict):
            raise ExtractionError("signed P02 qualification row is not an object")
        if overlay.get("runtime_support_state") != "verified_current_target":
            continue
        capability_id = overlay.get("capability_id")
        if (
            not isinstance(capability_id, str)
            or SEMANTIC_ID_PATTERN.fullmatch(capability_id) is None
            or "haction" in capability_id.lower()
            or "parameterset" in capability_id.lower()
            or capability_id not in capability_ids
        ):
            raise ExtractionError(
                "runtime-qualified capability is absent from the contract registry"
            )
        if (
            overlay.get("source_status") != "candidate_unverified"
            or overlay.get("probe_disposition") != "verified"
            or overlay.get("routing_enabled") is not False
        ):
            raise ExtractionError(
                "runtime-qualified P02 overlay has an invalid disposition"
            )
        source = source_by_id.get(capability_id)
        if not isinstance(source, dict):
            raise ExtractionError("runtime-qualified capability has no source binding")
        if (
            source.get("status") != "candidate_unverified"
            or source.get("runtime_support_state") != "unverified"
            or source.get("routing_enabled") is not False
            or source.get("target_profile_id") != EXPECTED_TARGET["profile_id"]
            or source.get("raw_identifiers_present") is not True
        ):
            raise ExtractionError(
                "runtime-qualified source binding is not an unrouted candidate"
            )
        invocation = source.get("invocation")
        if not isinstance(invocation, dict) or invocation.get("kind") != "action":
            raise ExtractionError(
                "runtime-qualified source binding has no action invocation"
            )
        if (
            invocation.get("parameter_set_id") is not None
            or invocation.get("parameter_set_state") != "source_declares_none"
            or invocation.get("parameter_map") != []
        ):
            raise ExtractionError(
                "runtime-qualified parameter binding has no finite typed P10 projection"
            )
        projected.append(
            {
                "capability_id": capability_id,
                "action_id": _require_private_identifier(
                    invocation.get("action_id"), "P02 action identifier"
                ),
                "parameter_set_id": None,
                "probe_evidence_sha256": _probe_evidence_digest(overlay, runtime),
                "target_mode": "document_global",
                "parameters": [],
            }
        )

    projected.sort(key=lambda row: row["capability_id"])
    if not projected:
        raise ExtractionError("signed P02 registry has no P10-admissible binding")
    coverage = verified.payload["qualification"].get("coverage")
    if not isinstance(coverage, dict) or coverage.get("verified_count") != len(
        projected
    ):
        raise ExtractionError(
            "signed P02 verified-binding coverage does not match projection"
        )

    target = verified.payload["target"]
    payload = {
        "schema_version": P10_PAYLOAD_SCHEMA_VERSION,
        "bundle_id": bundle_id,
        "sequence": sequence,
        "source_registry_sha256": verified.payload["source_registry"]["sha256"],
        "capability_registry_sha256": capability_registry_sha256,
        "target": {
            "profile_id": target["profile_id"],
            "product_build": target["exact_build"],
            "locale": target["locale"],
            "process_architecture": target["architecture"],
            "executable_sha256": target["executable_sha256"],
        },
        "authorization": {
            "execution_enabled": True,
            "source_registry_routing_enabled": False,
            "scope": "current_pc_exact_target_only",
            "minimum_probe_state": "runtime_verified_current_target",
        },
        "bindings": projected,
    }
    validate_schema(payload, P10_BUNDLE_SCHEMA, "P10 binding payload")
    payload_bytes = canonical_json(payload)
    if len(payload_bytes) > MAX_P10_PAYLOAD_BYTES:
        raise ExtractionError("P10 binding payload exceeds worker limit")
    metadata = {
        "p02_envelope_sha256": verified.envelope_sha256,
        "p02_payload_sha256": verified.envelope["payload_sha256"],
        "source_registry_sha256": verified.payload["source_registry"]["sha256"],
        "binding_count": len(projected),
    }
    return payload, metadata


def sign_payload(
    payload: dict[str, Any],
    private_key_content: bytes,
    public_key_content: bytes,
    expected_public_key_sha256: str,
) -> tuple[bytes, dict[str, Any]]:
    if sha256_bytes(public_key_content) != expected_public_key_sha256:
        raise ExtractionError("P10 trusted public key SHA-256 mismatch")
    private_key = parse_private_key(private_key_content)
    public_key = parse_public_key(public_key_content)
    normalized_public, key_id = public_key_material(public_key)
    private_public, private_key_id = public_key_material(private_key.public_key())
    if normalized_public != public_key_content:
        raise ExtractionError("P10 trusted public key PEM is not canonical")
    if private_public != public_key_content or private_key_id != key_id:
        raise ExtractionError("P10 private key does not match the trusted public key")
    payload_bytes = canonical_json(payload)
    signature = private_key.sign(payload_bytes)
    envelope = {
        "schema_version": P10_ENVELOPE_SCHEMA_VERSION,
        "algorithm": "Ed25519",
        "key_id": key_id,
        "public_key_sha256": expected_public_key_sha256,
        "payload_sha256": sha256_bytes(payload_bytes),
        "payload_base64": base64.b64encode(payload_bytes).decode("ascii"),
        "signature_base64": base64.b64encode(signature).decode("ascii"),
    }
    validate_schema(envelope, P10_ENVELOPE_SCHEMA, "P10 signed binding envelope")
    envelope_bytes = serialize_json(envelope)
    if len(envelope_bytes) > MAX_P10_ENVELOPE_BYTES:
        raise ExtractionError("P10 signed binding envelope exceeds worker limit")
    return envelope_bytes, envelope


def verify_signed_bundle(
    envelope_content: bytes,
    public_key_content: bytes,
    expected_public_key_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    envelope = parse_unique_json(envelope_content, "signed P10 bundle")
    validate_schema(envelope, P10_ENVELOPE_SCHEMA, "P10 signed binding envelope")
    if sha256_bytes(public_key_content) != expected_public_key_sha256:
        raise ExtractionError("P10 trusted public key SHA-256 mismatch")
    public_key = parse_public_key(public_key_content)
    normalized_public, key_id = public_key_material(public_key)
    if normalized_public != public_key_content or envelope.get("key_id") != key_id:
        raise ExtractionError("P10 trusted key identity mismatch")
    if envelope.get("public_key_sha256") != expected_public_key_sha256:
        raise ExtractionError("P10 envelope public-key identity mismatch")
    try:
        payload_bytes = base64.b64decode(envelope["payload_base64"], validate=True)
        signature = base64.b64decode(envelope["signature_base64"], validate=True)
    except (ValueError, binascii.Error) as error:
        raise ExtractionError("P10 envelope contains invalid Base64") from error
    if len(payload_bytes) > MAX_P10_PAYLOAD_BYTES or len(signature) != 64:
        raise ExtractionError(
            "P10 envelope contains an invalid payload or signature length"
        )
    if (
        base64.b64encode(payload_bytes).decode("ascii") != envelope["payload_base64"]
        or sha256_bytes(payload_bytes) != envelope["payload_sha256"]
    ):
        raise ExtractionError("P10 payload encoding or digest mismatch")
    try:
        public_key.verify(signature, payload_bytes)
    except InvalidSignature as error:
        raise ExtractionError("P10 binding signature verification failed") from error
    payload = parse_unique_json(payload_bytes, "P10 binding payload")
    if canonical_json(payload) != payload_bytes:
        raise ExtractionError("P10 payload bytes are not canonical JSON")
    validate_schema(payload, P10_BUNDLE_SCHEMA, "P10 binding payload")
    return payload, envelope


def _receipt(
    payload: dict[str, Any],
    envelope: dict[str, Any],
    envelope_bytes: bytes,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    receipt = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "state": "pass",
        "bundle_id": payload["bundle_id"],
        "sequence": payload["sequence"],
        "target_profile_id": payload["target"]["profile_id"],
        "product_build": payload["target"]["product_build"],
        "process_architecture": payload["target"]["process_architecture"],
        "p02_envelope_sha256": metadata["p02_envelope_sha256"],
        "p02_payload_sha256": metadata["p02_payload_sha256"],
        "source_registry_sha256": payload["source_registry_sha256"],
        "capability_registry_sha256": payload["capability_registry_sha256"],
        "p10_key_id": envelope["key_id"],
        "p10_public_key_sha256": envelope["public_key_sha256"],
        "payload_sha256": envelope["payload_sha256"],
        "signed_bundle_sha256": sha256_bytes(envelope_bytes),
        "binding_count": len(payload["bindings"]),
        "probe_evidence_digest_count": len(
            {row["probe_evidence_sha256"] for row in payload["bindings"]}
        ),
        "source_registry_routing_enabled": False,
        "raw_identifier_values_in_receipt": False,
        "private_key_material_printed": False,
    }
    validate_schema(receipt, BUILD_RECEIPT_SCHEMA, "P10 bundle receipt")
    return receipt


def _publish_pair(
    root: Path,
    first_relative: str,
    first_content: bytes,
    second_relative: str,
    second_content: bytes,
) -> None:
    first = resolve_output(root, first_relative)
    second = resolve_output(root, second_relative)
    if first == second or first.exists() or second.exists():
        raise ExtractionError("P10 bundle output already exists or collides")
    publish_no_overwrite(first, first_content)
    try:
        publish_no_overwrite(second, second_content)
    except Exception:
        try:
            first.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def run_build(config: BuildConfig) -> dict[str, Any]:
    if config.output_root.resolve() != P10_PRIVATE_OUTPUT_ROOT.resolve():
        raise ExtractionError("P10 bundle may publish only under private P10 evidence")
    if not config.p10_private_key.resolve().is_relative_to(
        P10_PRIVATE_KEY_ROOT.resolve()
    ):
        raise ExtractionError("P10 private key must stay under private P10 evidence")
    if config.p10_trust_policy.resolve() != P10_TRUST_POLICY_PATH.resolve():
        raise ExtractionError(
            "P10 trust policy path is not the committed current-PC policy"
        )
    trust_policy_content = read_locked(
        config.p10_trust_policy,
        config.p10_trust_policy_sha256,
        MAX_KEY_BYTES,
        "P10 binding trust policy",
    )
    trust_policy = _load_trust_policy(trust_policy_content)
    _verify_policy_inputs(
        trust_policy,
        signed_p02_registry=config.signed_p02_registry,
        signed_p02_registry_sha256=config.signed_p02_registry_sha256,
        p02_public_key=config.p02_public_key,
        p02_public_key_sha256=config.p02_public_key_sha256,
        capability_registry=config.capability_registry,
        capability_registry_sha256=config.capability_registry_sha256,
        p10_public_key=config.p10_public_key,
        p10_public_key_sha256=config.p10_public_key_sha256,
        sequence=config.sequence,
    )
    signed_p02 = read_locked(
        config.signed_p02_registry,
        config.signed_p02_registry_sha256,
        MAX_P02_ENVELOPE_BYTES,
        "signed P02 registry",
    )
    p02_public = read_locked(
        config.p02_public_key,
        config.p02_public_key_sha256,
        MAX_KEY_BYTES,
        "P02 trusted public key",
    )
    capabilities = read_locked(
        config.capability_registry,
        config.capability_registry_sha256,
        MAX_CAPABILITY_REGISTRY_BYTES,
        "capability registry",
    )
    p10_private = read_locked(
        config.p10_private_key,
        config.p10_private_key_sha256,
        MAX_KEY_BYTES,
        "P10 private key",
    )
    p10_public = read_locked(
        config.p10_public_key,
        config.p10_public_key_sha256,
        MAX_KEY_BYTES,
        "P10 trusted public key",
    )
    payload, metadata = project_payload(
        signed_p02,
        p02_public,
        config.p02_public_key_sha256,
        capabilities,
        config.capability_registry_sha256,
        config.bundle_id,
        config.sequence,
    )
    envelope_bytes, envelope = sign_payload(
        payload,
        p10_private,
        p10_public,
        config.p10_public_key_sha256,
    )
    _verify_projected_policy(trust_policy, metadata, envelope)
    verified_payload, verified_envelope = verify_signed_bundle(
        envelope_bytes,
        p10_public,
        config.p10_public_key_sha256,
    )
    if verified_payload != payload or verified_envelope != envelope:
        raise ExtractionError("P10 signed bundle self-verification mismatch")
    for path, content, maximum, label in (
        (
            config.signed_p02_registry,
            signed_p02,
            MAX_P02_ENVELOPE_BYTES,
            "signed P02 registry",
        ),
        (config.p02_public_key, p02_public, MAX_KEY_BYTES, "P02 trusted public key"),
        (
            config.capability_registry,
            capabilities,
            MAX_CAPABILITY_REGISTRY_BYTES,
            "capability registry",
        ),
        (config.p10_private_key, p10_private, MAX_KEY_BYTES, "P10 private key"),
        (config.p10_public_key, p10_public, MAX_KEY_BYTES, "P10 trusted public key"),
        (
            config.p10_trust_policy,
            trust_policy_content,
            MAX_KEY_BYTES,
            "P10 binding trust policy",
        ),
    ):
        if read_locked(path, sha256_bytes(content), maximum, label) != content:
            raise ExtractionError(f"{label} changed during bundle construction")
    receipt = _receipt(payload, envelope, envelope_bytes, metadata)
    _publish_pair(
        config.output_root,
        config.envelope_output_relative,
        envelope_bytes,
        config.receipt_output_relative,
        serialize_json(receipt),
    )
    return receipt


def run_verify(config: VerifyConfig) -> dict[str, Any]:
    if config.output_root.resolve() != P10_PRIVATE_OUTPUT_ROOT.resolve():
        raise ExtractionError(
            "P10 verification may publish only under private P10 evidence"
        )
    if config.p10_trust_policy.resolve() != P10_TRUST_POLICY_PATH.resolve():
        raise ExtractionError(
            "P10 trust policy path is not the committed current-PC policy"
        )
    trust_policy_content = read_locked(
        config.p10_trust_policy,
        config.p10_trust_policy_sha256,
        MAX_KEY_BYTES,
        "P10 binding trust policy",
    )
    trust_policy = _load_trust_policy(trust_policy_content)
    _verify_policy_inputs(
        trust_policy,
        signed_p02_registry=config.signed_p02_registry,
        signed_p02_registry_sha256=config.signed_p02_registry_sha256,
        p02_public_key=config.p02_public_key,
        p02_public_key_sha256=config.p02_public_key_sha256,
        capability_registry=config.capability_registry,
        capability_registry_sha256=config.capability_registry_sha256,
        p10_public_key=config.p10_public_key,
        p10_public_key_sha256=config.p10_public_key_sha256,
        sequence=config.sequence,
    )
    signed_p02 = read_locked(
        config.signed_p02_registry,
        config.signed_p02_registry_sha256,
        MAX_P02_ENVELOPE_BYTES,
        "signed P02 registry",
    )
    p02_public = read_locked(
        config.p02_public_key,
        config.p02_public_key_sha256,
        MAX_KEY_BYTES,
        "P02 trusted public key",
    )
    capabilities = read_locked(
        config.capability_registry,
        config.capability_registry_sha256,
        MAX_CAPABILITY_REGISTRY_BYTES,
        "capability registry",
    )
    signed_p10 = read_locked(
        config.signed_p10_bundle,
        config.signed_p10_bundle_sha256,
        MAX_P10_ENVELOPE_BYTES,
        "signed P10 bundle",
    )
    p10_public = read_locked(
        config.p10_public_key,
        config.p10_public_key_sha256,
        MAX_KEY_BYTES,
        "P10 trusted public key",
    )
    expected_payload, metadata = project_payload(
        signed_p02,
        p02_public,
        config.p02_public_key_sha256,
        capabilities,
        config.capability_registry_sha256,
        config.bundle_id,
        config.sequence,
    )
    payload, envelope = verify_signed_bundle(
        signed_p10,
        p10_public,
        config.p10_public_key_sha256,
    )
    _verify_projected_policy(trust_policy, metadata, envelope)
    if payload != expected_payload:
        raise ExtractionError("P10 bundle differs from independent P02 projection")
    for path, content, maximum, label in (
        (
            config.signed_p02_registry,
            signed_p02,
            MAX_P02_ENVELOPE_BYTES,
            "signed P02 registry",
        ),
        (config.p02_public_key, p02_public, MAX_KEY_BYTES, "P02 trusted public key"),
        (
            config.capability_registry,
            capabilities,
            MAX_CAPABILITY_REGISTRY_BYTES,
            "capability registry",
        ),
        (
            config.signed_p10_bundle,
            signed_p10,
            MAX_P10_ENVELOPE_BYTES,
            "signed P10 bundle",
        ),
        (config.p10_public_key, p10_public, MAX_KEY_BYTES, "P10 trusted public key"),
        (
            config.p10_trust_policy,
            trust_policy_content,
            MAX_KEY_BYTES,
            "P10 binding trust policy",
        ),
    ):
        if read_locked(path, sha256_bytes(content), maximum, label) != content:
            raise ExtractionError(f"{label} changed during bundle verification")
    receipt = _receipt(payload, envelope, signed_p10, metadata)
    output = resolve_output(config.output_root, config.receipt_output_relative)
    publish_no_overwrite(output, serialize_json(receipt))
    return receipt


def generate_p10_key_pair(
    private_output_root: Path,
    private_output_relative: str,
    public_output_root: Path,
    public_output_relative: str,
) -> dict[str, Any]:
    if private_output_root.resolve() != P10_PRIVATE_KEY_ROOT.resolve():
        raise ExtractionError("private key output root must be private P10 evidence")
    if public_output_root.resolve() != P10_TRUST_OUTPUT_ROOT.resolve():
        raise ExtractionError("public key output root must be the P10 trust directory")
    private_pem, public_pem, key_id = create_key_pair_material()
    private_output = resolve_output(private_output_root, private_output_relative)
    public_output = resolve_output(public_output_root, public_output_relative)
    if private_output.exists() or public_output.exists():
        raise ExtractionError("P10 signing key output already exists")
    publish_no_overwrite(private_output, private_pem)
    try:
        publish_no_overwrite(public_output, public_pem)
    except Exception:
        try:
            private_output.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return {
        "schema_version": "hwpx-agent.p10-06-signing-key-generation-receipt/v1",
        "state": "pass",
        "algorithm": "Ed25519",
        "key_id": key_id,
        "public_key_sha256": sha256_bytes(public_pem),
        "private_key_material_printed": False,
        "production_trust": False,
    }
