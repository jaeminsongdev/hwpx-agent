#!/usr/bin/env python3
from __future__ import annotations

import base64
import binascii
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from jsonschema import Draft202012Validator, FormatChecker

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.p02.extract_help import (
    ExtractionError,
    publish_no_overwrite,
    read_regular_file,
    resolve_output,
)
from tools.p02.verify_runtime_probe import ProbeVerificationConfig, verify as verify_probe


SCHEMA_ROOT = Path(__file__).with_name("schemas")
ENVELOPE_SCHEMA = SCHEMA_ROOT / "signed-registry-envelope-v1.schema.json"
DRIFT_SCHEMA = SCHEMA_ROOT / "registry-drift-v1.schema.json"
VERIFICATION_SCHEMA = SCHEMA_ROOT / "signed-registry-verification-v1.schema.json"
REGISTRY_SCHEMA = (
    REPOSITORY_ROOT
    / "protocol"
    / "json-schema"
    / "automation-binding-registry-v1.schema.json"
)
PRIVATE_OUTPUT_ROOT = REPOSITORY_ROOT / "implementation" / "p02" / "evidence"
PRIVATE_KEY_ROOT = PRIVATE_OUTPUT_ROOT / "signing-keys"
TRUST_OUTPUT_ROOT = REPOSITORY_ROOT / "implementation" / "p02" / "trust"

EXPECTED_PROFILE_ID = "hancom-hangul-2020-secondary"
EXPECTED_PRODUCT = "Hancom Hangul 2020"
EXPECTED_RELEASE = "2020"
EXPECTED_BUILD = "11.0.0.9136"
EXPECTED_LOCALE = "ko-KR"
EXPECTED_ARCHITECTURE = "x86"
EXPECTED_EXECUTABLE_SHA256 = (
    "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
)
GENERATOR_ID = "p02-registry-signer"
GENERATOR_VERSION = "0.1.0"

MAX_REGISTRY_BYTES = 32 * 1024 * 1024
MAX_EVIDENCE_BYTES = 8 * 1024 * 1024
MAX_ENVELOPE_BYTES = 64 * 1024 * 1024
MAX_KEY_BYTES = 64 * 1024


@dataclass(frozen=True)
class SigningConfig:
    registry: Path
    registry_sha256: str
    target_profile: Path
    profile_sha256: str
    contracts: Path
    contracts_sha256: str
    request: Path
    request_sha256: str
    trace: Path
    trace_sha256: str
    receipt: Path
    receipt_sha256: str
    private_key: Path
    source_commit: str
    output_root: Path
    output_relative: str


@dataclass(frozen=True)
class SignedRegistryVerificationConfig:
    signed_registry: Path
    signed_registry_sha256: str
    public_key: Path
    public_key_sha256: str
    registry: Path
    registry_sha256: str
    target_profile: Path
    profile_sha256: str
    contracts: Path
    contracts_sha256: str
    request: Path
    request_sha256: str
    trace: Path
    trace_sha256: str
    receipt: Path
    receipt_sha256: str


@dataclass(frozen=True)
class VerifiedEnvelope:
    envelope: dict[str, Any]
    payload: dict[str, Any]
    registry: dict[str, Any]
    registry_bytes: bytes
    envelope_sha256: str


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def serialize_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def parse_json(content: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ExtractionError(f"{label} is not valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ExtractionError(f"{label} root is not an object")
    return value


def validate_schema(value: object, schema_path: Path, label: str) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        detail = "; ".join(
            f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors[:20]
        )
        raise ExtractionError(f"{label} schema invalid: {detail}")


def read_locked(path: Path, expected_sha256: str, maximum: int, label: str) -> bytes:
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ExtractionError(f"{label} expected SHA-256 is invalid")
    content = read_regular_file(path, maximum)
    if sha256_bytes(content) != expected_sha256:
        raise ExtractionError(f"{label} SHA-256 mismatch")
    return content


def scalar_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in scalar_strings(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in scalar_strings(child)]
    return []


def public_key_material(public_key: Ed25519PublicKey) -> tuple[bytes, str]:
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return pem, "ed25519-sha256-" + sha256_bytes(der)


def create_key_pair_material() -> tuple[bytes, bytes, str]:
    private_key = Ed25519PrivateKey.generate()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem, key_id = public_key_material(private_key.public_key())
    return private_pem, public_pem, key_id


def parse_private_key(content: bytes) -> Ed25519PrivateKey:
    try:
        key = serialization.load_pem_private_key(content, password=None)
    except (TypeError, ValueError) as error:
        raise ExtractionError("signing private key is not valid unencrypted PEM") from error
    if not isinstance(key, Ed25519PrivateKey):
        raise ExtractionError("signing private key is not Ed25519")
    return key


def parse_public_key(content: bytes) -> Ed25519PublicKey:
    try:
        key = serialization.load_pem_public_key(content)
    except (TypeError, ValueError) as error:
        raise ExtractionError("trusted public key is not valid PEM") from error
    if not isinstance(key, Ed25519PublicKey):
        raise ExtractionError("trusted public key is not Ed25519")
    return key


def generate_key_pair(
    private_output_root: Path,
    private_output_relative: str,
    public_output_root: Path,
    public_output_relative: str,
) -> dict[str, object]:
    private_pem, public_pem, key_id = create_key_pair_material()
    private_output = resolve_output(private_output_root, private_output_relative)
    public_output = resolve_output(public_output_root, public_output_relative)
    if private_output.exists() or public_output.exists():
        raise ExtractionError("signing key output already exists")
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
        "schema_version": "hwpx-agent.signing-key-generation-receipt/v1",
        "algorithm": "Ed25519",
        "key_id": key_id,
        "public_key_sha256": sha256_bytes(public_pem),
        "private_key_material_printed": False,
        "production_trust": False,
    }


def expected_qualification(
    registry: dict[str, Any],
    trace: dict[str, Any],
    request_sha256: str,
    trace_sha256: str,
    receipt_sha256: str,
) -> dict[str, Any]:
    trace_rows = trace.get("probe_results", [])
    trace_map = {
        row.get("capability_id"): row for row in trace_rows if isinstance(row, dict)
    }
    if len(trace_map) != len(trace_rows):
        raise ExtractionError("runtime trace contains duplicate or invalid capability rows")
    overlay: list[dict[str, Any]] = []
    for binding in registry.get("bindings", []):
        capability_id = binding.get("capability_id")
        if binding.get("status") == "unavailable_with_reason":
            overlay.append(
                {
                    "binding_key": binding.get("binding_key"),
                    "feature_id": binding.get("feature_id"),
                    "capability_id": capability_id,
                    "source_status": "unavailable_with_reason",
                    "runtime_support_state": "unavailable",
                    "probe_disposition": None,
                    "routing_enabled": False,
                    "evidence": None,
                }
            )
            continue
        result = trace_map.get(capability_id)
        if result is None:
            raise ExtractionError(f"runtime trace is missing candidate: {capability_id}")
        disposition = result.get("disposition")
        support_state = {
            "verified": "verified_current_target",
            "failed": "failed_current_target",
            "blocked_by_risk": "blocked_by_policy",
            "not_run": "unverified_not_run",
        }.get(disposition)
        if support_state is None:
            raise ExtractionError(f"runtime disposition is invalid: {capability_id}")
        if disposition == "verified" and not (
            result.get("execute_state") == "pass"
            and result.get("expected_effect_observed") is True
        ):
            raise ExtractionError(f"verified runtime evidence is incomplete: {capability_id}")
        evidence = {
            "request_sha256": request_sha256,
            "trace_sha256": trace_sha256,
            "receipt_sha256": receipt_sha256,
            "execute_state": result.get("execute_state"),
            "default_read_state": result.get("default_read_state"),
            "expected_effect_observed": result.get("expected_effect_observed"),
            "pre_snapshot_sha256": result.get("pre_snapshot_sha256"),
            "post_snapshot_sha256": result.get("post_snapshot_sha256"),
            "default_shape_sha256": result.get("default_shape_sha256"),
            "error_type": result.get("error_type"),
            "error_hresult": result.get("error_hresult"),
            "error_message_sha256": result.get("error_message_sha256"),
        }
        overlay.append(
            {
                "binding_key": binding.get("binding_key"),
                "feature_id": binding.get("feature_id"),
                "capability_id": capability_id,
                "source_status": "candidate_unverified",
                "runtime_support_state": support_state,
                "probe_disposition": disposition,
                "routing_enabled": False,
                "evidence": evidence,
            }
        )
    capability_ids = [row["capability_id"] for row in overlay]
    if len(capability_ids) != len(set(capability_ids)):
        raise ExtractionError("qualification overlay contains duplicate capabilities")
    dispositions = Counter(
        row["probe_disposition"] for row in overlay if row["probe_disposition"] is not None
    )
    source_states = Counter(row["source_status"] for row in overlay)
    coverage = {
        "binding_count": len(overlay),
        "candidate_count": source_states["candidate_unverified"],
        "unavailable_count": source_states["unavailable_with_reason"],
        "verified_count": dispositions["verified"],
        "failed_count": dispositions["failed"],
        "blocked_by_risk_count": dispositions["blocked_by_risk"],
        "not_run_count": dispositions["not_run"],
        "routing_enabled_count": 0,
    }
    if coverage["candidate_count"] != len(trace_rows):
        raise ExtractionError("qualification candidate/trace coverage mismatch")
    return {
        "state": "partially_qualified_scoped_current_target",
        "bindings": overlay,
        "coverage": coverage,
        "routing_enabled": False,
    }


def build_payload(
    registry_bytes: bytes,
    registry: dict[str, Any],
    request: dict[str, Any],
    trace: dict[str, Any],
    receipt: dict[str, Any],
    profile_sha256: str,
    request_sha256: str,
    trace_sha256: str,
    receipt_sha256: str,
    source_commit: str,
) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ExtractionError("source commit must be 40 lowercase hexadecimal characters")
    target = registry.get("target", {})
    expected_target = {
        "profile_id": EXPECTED_PROFILE_ID,
        "product": EXPECTED_PRODUCT,
        "major_release": EXPECTED_RELEASE,
        "exact_build": EXPECTED_BUILD,
        "locale": EXPECTED_LOCALE,
        "architecture": EXPECTED_ARCHITECTURE,
        "profile_sha256": profile_sha256,
    }
    for key, value in expected_target.items():
        if target.get(key) != value:
            raise ExtractionError(f"source registry target {key} mismatch")
    observed_target = receipt.get("target", {})
    if not (
        observed_target.get("profile_id") == EXPECTED_PROFILE_ID
        and observed_target.get("observed_file_version") == EXPECTED_BUILD
        and observed_target.get("observed_executable_sha256")
        == EXPECTED_EXECUTABLE_SHA256
        and observed_target.get("identity_match") is True
        and observed_target.get("client_apartment_state") == "STA"
    ):
        raise ExtractionError("runtime receipt exact target identity mismatch")
    qualification = expected_qualification(
        registry,
        trace,
        request_sha256,
        trace_sha256,
        receipt_sha256,
    )
    payload = {
        "schema_version": "hwpx-agent.signed-automation-registry-payload/v1",
        "restricted_derivative": True,
        "source_registry": {
            "encoding": "base64",
            "sha256": sha256_bytes(registry_bytes),
            "bytes_base64": base64.b64encode(registry_bytes).decode("ascii"),
        },
        "target": {
            **expected_target,
            "executable_sha256": EXPECTED_EXECUTABLE_SHA256,
        },
        "runtime_evidence": {
            "request_id": request.get("request_id"),
            "request_sha256": request_sha256,
            "trace_sha256": trace_sha256,
            "receipt_sha256": receipt_sha256,
            "independent_verification_state": "pass",
        },
        "qualification": qualification,
        "release_policy": {
            "use_scope": "personal_noncommercial_local_development",
            "target_scope": "current_pc_exact_identity_only",
            "production_release_state": "disabled",
            "provider_release_state": "disabled",
            "routing_enabled": False,
        },
        "drift_baseline": {
            "state": "baseline_unavailable",
            "baseline_registry_sha256": None,
            "baseline_exact_build": None,
        },
        "lineage": {
            "registry_sequence": 1,
            "parent_payload_sha256": None,
        },
        "provenance": {
            "generator_id": GENERATOR_ID,
            "generator_version": GENERATOR_VERSION,
            "source_commit": source_commit,
        },
    }
    return payload


def create_envelope(payload: dict[str, Any], private_key: Ed25519PrivateKey) -> dict[str, Any]:
    payload_bytes = canonical_json(payload)
    public_pem, key_id = public_key_material(private_key.public_key())
    signature = private_key.sign(payload_bytes)
    envelope = {
        "schema_version": "hwpx-agent.signed-automation-registry-envelope/v1",
        "algorithm": "Ed25519",
        "key_id": key_id,
        "public_key_sha256": sha256_bytes(public_pem),
        "payload_sha256": sha256_bytes(payload_bytes),
        "payload": payload,
        "signature_base64": base64.b64encode(signature).decode("ascii"),
    }
    validate_schema(envelope, ENVELOPE_SCHEMA, "signed registry envelope")
    return envelope


def run_signing(config: SigningConfig) -> dict[str, Any]:
    if config.output_root.resolve() != PRIVATE_OUTPUT_ROOT.resolve():
        raise ExtractionError("signed registry may publish only under private P02 evidence")
    if not config.private_key.resolve().is_relative_to(PRIVATE_KEY_ROOT.resolve()):
        raise ExtractionError("signing private key must stay under private P02 evidence")
    registry_bytes = read_locked(
        config.registry, config.registry_sha256, MAX_REGISTRY_BYTES, "binding registry"
    )
    profile_bytes = read_locked(
        config.target_profile, config.profile_sha256, MAX_EVIDENCE_BYTES, "target profile"
    )
    contracts_bytes = read_locked(
        config.contracts, config.contracts_sha256, MAX_REGISTRY_BYTES, "capability contracts"
    )
    request_bytes = read_locked(
        config.request, config.request_sha256, MAX_EVIDENCE_BYTES, "runtime request"
    )
    trace_bytes = read_locked(
        config.trace, config.trace_sha256, MAX_EVIDENCE_BYTES, "runtime trace"
    )
    receipt_bytes = read_locked(
        config.receipt, config.receipt_sha256, MAX_EVIDENCE_BYTES, "runtime receipt"
    )
    private_key_bytes = read_regular_file(config.private_key, MAX_KEY_BYTES)
    registry = parse_json(registry_bytes, "binding registry")
    request = parse_json(request_bytes, "runtime request")
    trace = parse_json(trace_bytes, "runtime trace")
    receipt = parse_json(receipt_bytes, "runtime receipt")
    validate_schema(registry, REGISTRY_SCHEMA, "binding registry")
    probe_result = verify_probe(
        ProbeVerificationConfig(
            registry=config.registry,
            registry_sha256=config.registry_sha256,
            target_profile=config.target_profile,
            profile_sha256=config.profile_sha256,
            contracts=config.contracts,
            contracts_sha256=config.contracts_sha256,
            request=config.request,
            trace=config.trace,
            receipt=config.receipt,
        )
    )
    if probe_result.get("state") != "pass":
        raise ExtractionError("runtime evidence did not pass independent verification")
    payload = build_payload(
        registry_bytes,
        registry,
        request,
        trace,
        receipt,
        config.profile_sha256,
        config.request_sha256,
        config.trace_sha256,
        config.receipt_sha256,
        config.source_commit,
    )
    private_key = parse_private_key(private_key_bytes)
    envelope = create_envelope(payload, private_key)
    envelope_bytes = serialize_json(envelope)
    locked_inputs = (
        (config.registry, registry_bytes, MAX_REGISTRY_BYTES, "binding registry"),
        (config.target_profile, profile_bytes, MAX_EVIDENCE_BYTES, "target profile"),
        (config.contracts, contracts_bytes, MAX_REGISTRY_BYTES, "capability contracts"),
        (config.request, request_bytes, MAX_EVIDENCE_BYTES, "runtime request"),
        (config.trace, trace_bytes, MAX_EVIDENCE_BYTES, "runtime trace"),
        (config.receipt, receipt_bytes, MAX_EVIDENCE_BYTES, "runtime receipt"),
        (config.private_key, private_key_bytes, MAX_KEY_BYTES, "signing private key"),
    )
    for path, original, maximum, label in locked_inputs:
        if read_regular_file(path, maximum) != original:
            raise ExtractionError(f"{label} changed during signing")
    output = resolve_output(config.output_root, config.output_relative)
    publish_no_overwrite(output, envelope_bytes)
    coverage = payload["qualification"]["coverage"]
    return {
        "schema_version": "hwpx-agent.registry-signing-receipt/v1",
        "state": "pass",
        "target_profile_id": EXPECTED_PROFILE_ID,
        "exact_build": EXPECTED_BUILD,
        "key_id": envelope["key_id"],
        "public_key_sha256": envelope["public_key_sha256"],
        "source_registry_sha256": config.registry_sha256,
        "payload_sha256": envelope["payload_sha256"],
        "signed_registry_sha256": sha256_bytes(envelope_bytes),
        "coverage": coverage,
        "routing_enabled": False,
        "private_key_material_printed": False,
        "raw_identifiers_in_receipt": False,
    }


def verify_envelope_content(
    envelope_content: bytes,
    public_key_content: bytes,
    expected_public_key_sha256: str,
) -> VerifiedEnvelope:
    if sha256_bytes(public_key_content) != expected_public_key_sha256:
        raise ExtractionError("trusted public key SHA-256 mismatch")
    envelope = parse_json(envelope_content, "signed registry")
    validate_schema(envelope, ENVELOPE_SCHEMA, "signed registry envelope")
    payload = envelope["payload"]
    payload_bytes = canonical_json(payload)
    if sha256_bytes(payload_bytes) != envelope["payload_sha256"]:
        raise ExtractionError("signed registry payload SHA-256 mismatch")
    public_key = parse_public_key(public_key_content)
    public_pem, key_id = public_key_material(public_key)
    if key_id != envelope["key_id"]:
        raise ExtractionError("signed registry key ID mismatch")
    if sha256_bytes(public_pem) != envelope["public_key_sha256"]:
        raise ExtractionError("signed registry public key identity mismatch")
    try:
        signature = base64.b64decode(envelope["signature_base64"], validate=True)
    except (ValueError, binascii.Error) as error:
        raise ExtractionError("signed registry signature is not valid Base64") from error
    try:
        public_key.verify(signature, payload_bytes)
    except InvalidSignature as error:
        raise ExtractionError("signed registry signature verification failed") from error
    try:
        registry_bytes = base64.b64decode(
            payload["source_registry"]["bytes_base64"], validate=True
        )
    except (ValueError, binascii.Error) as error:
        raise ExtractionError("embedded source registry is not valid Base64") from error
    if len(registry_bytes) > MAX_REGISTRY_BYTES:
        raise ExtractionError("embedded source registry exceeds size limit")
    if sha256_bytes(registry_bytes) != payload["source_registry"]["sha256"]:
        raise ExtractionError("embedded source registry SHA-256 mismatch")
    registry = parse_json(registry_bytes, "embedded source registry")
    validate_schema(registry, REGISTRY_SCHEMA, "embedded source registry")
    target = payload["target"]
    source_target = registry["target"]
    for key in (
        "profile_id",
        "product",
        "major_release",
        "exact_build",
        "locale",
        "architecture",
        "profile_sha256",
    ):
        if target[key] != source_target[key]:
            raise ExtractionError(f"signed/source registry target {key} mismatch")
    overlay = payload["qualification"]["bindings"]
    source_bindings = registry["bindings"]
    overlay_ids = [row["capability_id"] for row in overlay]
    source_ids = [row["capability_id"] for row in source_bindings]
    if (
        len(overlay_ids) != len(set(overlay_ids))
        or len(source_ids) != len(set(source_ids))
        or set(overlay_ids) != set(source_ids)
    ):
        raise ExtractionError("signed registry qualification coverage mismatch")
    overlay_map = {row["capability_id"]: row for row in overlay}
    for binding in source_bindings:
        row = overlay_map[binding["capability_id"]]
        for key in ("binding_key", "feature_id", "capability_id"):
            if row[key] != binding[key]:
                raise ExtractionError(
                    f"signed registry qualification projection mismatch: {binding['capability_id']}/{key}"
                )
        if row["routing_enabled"] is not False:
            raise ExtractionError("signed registry attempted to enable routing")
    if payload["qualification"]["routing_enabled"] is not False:
        raise ExtractionError("signed registry qualification routing is enabled")
    return VerifiedEnvelope(
        envelope=envelope,
        payload=payload,
        registry=registry,
        registry_bytes=registry_bytes,
        envelope_sha256=sha256_bytes(envelope_content),
    )


def verify_signed_registry(config: SignedRegistryVerificationConfig) -> dict[str, Any]:
    envelope_content = read_locked(
        config.signed_registry,
        config.signed_registry_sha256,
        MAX_ENVELOPE_BYTES,
        "signed registry",
    )
    public_key_content = read_locked(
        config.public_key,
        config.public_key_sha256,
        MAX_KEY_BYTES,
        "trusted public key",
    )
    verified = verify_envelope_content(
        envelope_content, public_key_content, config.public_key_sha256
    )
    registry_bytes = read_locked(
        config.registry, config.registry_sha256, MAX_REGISTRY_BYTES, "binding registry"
    )
    request_bytes = read_locked(
        config.request, config.request_sha256, MAX_EVIDENCE_BYTES, "runtime request"
    )
    trace_bytes = read_locked(
        config.trace, config.trace_sha256, MAX_EVIDENCE_BYTES, "runtime trace"
    )
    receipt_bytes = read_locked(
        config.receipt, config.receipt_sha256, MAX_EVIDENCE_BYTES, "runtime receipt"
    )
    profile_bytes = read_locked(
        config.target_profile, config.profile_sha256, MAX_EVIDENCE_BYTES, "target profile"
    )
    contracts_bytes = read_locked(
        config.contracts, config.contracts_sha256, MAX_REGISTRY_BYTES, "capability contracts"
    )
    if verified.registry_bytes != registry_bytes:
        raise ExtractionError("signed registry does not embed the locked source registry bytes")
    probe_result = verify_probe(
        ProbeVerificationConfig(
            registry=config.registry,
            registry_sha256=config.registry_sha256,
            target_profile=config.target_profile,
            profile_sha256=config.profile_sha256,
            contracts=config.contracts,
            contracts_sha256=config.contracts_sha256,
            request=config.request,
            trace=config.trace,
            receipt=config.receipt,
        )
    )
    if probe_result.get("state") != "pass":
        raise ExtractionError("runtime evidence did not pass independent verification")
    request = parse_json(request_bytes, "runtime request")
    trace = parse_json(trace_bytes, "runtime trace")
    receipt = parse_json(receipt_bytes, "runtime receipt")
    expected_payload = build_payload(
        registry_bytes,
        verified.registry,
        request,
        trace,
        receipt,
        config.profile_sha256,
        config.request_sha256,
        config.trace_sha256,
        config.receipt_sha256,
        verified.payload["provenance"]["source_commit"],
    )
    if expected_payload != verified.payload:
        raise ExtractionError("signed registry payload differs from independently projected evidence")
    coverage = verified.payload["qualification"]["coverage"]
    result: dict[str, Any] = {
        "schema_version": "hwpx-agent.signed-registry-verification/v1",
        "state": "pass",
        "target_profile_id": verified.payload["target"]["profile_id"],
        "exact_build": verified.payload["target"]["exact_build"],
        "key_id": verified.envelope["key_id"],
        "envelope_sha256": verified.envelope_sha256,
        "payload_sha256": verified.envelope["payload_sha256"],
        "source_registry_sha256": verified.payload["source_registry"]["sha256"],
        "signature_valid": True,
        "runtime_evidence_valid": True,
        "coverage": coverage,
        "routing_enabled": False,
        "raw_identifier_value_leak_count": 0,
        "errors": [],
    }
    raw_values = {
        value
        for binding in verified.registry["bindings"]
        for value in (
            (binding.get("invocation") or {}).get("action_id"),
            (binding.get("invocation") or {}).get("parameter_set_id"),
        )
        if isinstance(value, str)
    }
    leaked = raw_values & set(scalar_strings(result))
    result["raw_identifier_value_leak_count"] = len(leaked)
    if leaked:
        result["state"] = "failed"
        result["errors"].append("verification receipt contains raw identifier values")
    validate_schema(result, VERIFICATION_SCHEMA, "signed registry verification")
    for path, original, maximum, label in (
        (config.signed_registry, envelope_content, MAX_ENVELOPE_BYTES, "signed registry"),
        (config.public_key, public_key_content, MAX_KEY_BYTES, "trusted public key"),
        (config.registry, registry_bytes, MAX_REGISTRY_BYTES, "binding registry"),
        (config.target_profile, profile_bytes, MAX_EVIDENCE_BYTES, "target profile"),
        (config.contracts, contracts_bytes, MAX_REGISTRY_BYTES, "capability contracts"),
        (config.request, request_bytes, MAX_EVIDENCE_BYTES, "runtime request"),
        (config.trace, trace_bytes, MAX_EVIDENCE_BYTES, "runtime trace"),
        (config.receipt, receipt_bytes, MAX_EVIDENCE_BYTES, "runtime receipt"),
    ):
        if read_regular_file(path, maximum) != original:
            raise ExtractionError(f"{label} changed during signed-registry verification")
    return result


def registry_identity(verified: VerifiedEnvelope) -> dict[str, Any]:
    return {
        "profile_id": verified.payload["target"]["profile_id"],
        "exact_build": verified.payload["target"]["exact_build"],
        "source_registry_sha256": verified.payload["source_registry"]["sha256"],
        "payload_sha256": verified.envelope["payload_sha256"],
        "key_id": verified.envelope["key_id"],
        "registry_sequence": verified.payload["lineage"]["registry_sequence"],
    }


def behavior_view(row: dict[str, Any] | None) -> object:
    if row is None:
        return None
    evidence = row.get("evidence")
    if not isinstance(evidence, dict):
        evidence_view = None
    else:
        evidence_view = {
            key: evidence.get(key)
            for key in (
                "execute_state",
                "default_read_state",
                "expected_effect_observed",
                "pre_snapshot_sha256",
                "post_snapshot_sha256",
                "default_shape_sha256",
                "error_type",
                "error_hresult",
                "error_message_sha256",
            )
        }
    return {
        "runtime_support_state": row.get("runtime_support_state"),
        "probe_disposition": row.get("probe_disposition"),
        "evidence": evidence_view,
    }


def compare_registry_drift(
    current: VerifiedEnvelope,
    baseline: VerifiedEnvelope | None,
) -> dict[str, Any]:
    policy = {
        "changed_bindings_auto_promoted": False,
        "production_route_changed": False,
        "raw_identifiers_present": False,
    }
    if baseline is None:
        report = {
            "schema_version": "hwpx-agent.registry-drift/v1",
            "state": "pass",
            "baseline_state": "baseline_unavailable",
            "baseline": None,
            "current": registry_identity(current),
            "summary": {
                "compared_capability_count": 0,
                "added_count": 0,
                "removed_count": 0,
                "binding_changed_count": 0,
                "parameter_changed_count": 0,
                "behavior_changed_count": 0,
                "unchanged_count": 0,
                "unverified_for_build_count": 0,
            },
            "changes": [],
            "policy": policy,
        }
        validate_schema(report, DRIFT_SCHEMA, "registry drift report")
        return report
    current_sequence = current.payload["lineage"]["registry_sequence"]
    baseline_sequence = baseline.payload["lineage"]["registry_sequence"]
    if current_sequence <= baseline_sequence:
        raise ExtractionError("registry lineage sequence is not monotonic")
    if current.payload["lineage"]["parent_payload_sha256"] != baseline.envelope[
        "payload_sha256"
    ]:
        raise ExtractionError("registry lineage parent payload mismatch")
    current_bindings = {
        row["capability_id"]: row for row in current.registry["bindings"]
    }
    baseline_bindings = {
        row["capability_id"]: row for row in baseline.registry["bindings"]
    }
    current_overlay = {
        row["capability_id"]: row
        for row in current.payload["qualification"]["bindings"]
    }
    baseline_overlay = {
        row["capability_id"]: row
        for row in baseline.payload["qualification"]["bindings"]
    }
    all_ids = sorted(set(current_bindings) | set(baseline_bindings))
    changes: list[dict[str, Any]] = []
    unchanged = 0
    type_counts: Counter[str] = Counter()
    for capability_id in all_ids:
        current_binding = current_bindings.get(capability_id)
        baseline_binding = baseline_bindings.get(capability_id)
        change_types: list[str] = []
        if baseline_binding is None:
            change_types.append("added")
        elif current_binding is None:
            change_types.append("removed")
        else:
            current_invocation = current_binding.get("invocation") or {}
            baseline_invocation = baseline_binding.get("invocation") or {}
            current_action = {
                "kind": current_invocation.get("kind"),
                "action_id": current_invocation.get("action_id"),
            }
            baseline_action = {
                "kind": baseline_invocation.get("kind"),
                "action_id": baseline_invocation.get("action_id"),
            }
            if canonical_json(current_action) != canonical_json(baseline_action):
                change_types.append("binding_changed")
            current_parameters = {
                key: current_invocation.get(key)
                for key in (
                    "parameter_set_id",
                    "parameter_set_state",
                    "parameter_map",
                    "parameter_map_state",
                )
            }
            baseline_parameters = {
                key: baseline_invocation.get(key)
                for key in (
                    "parameter_set_id",
                    "parameter_set_state",
                    "parameter_map",
                    "parameter_map_state",
                )
            }
            if canonical_json(current_parameters) != canonical_json(baseline_parameters):
                change_types.append("parameter_changed")
            if canonical_json(behavior_view(current_overlay.get(capability_id))) != canonical_json(
                behavior_view(baseline_overlay.get(capability_id))
            ):
                change_types.append("behavior_changed")
        if change_types:
            type_counts.update(change_types)
            changes.append(
                {
                    "capability_id": capability_id,
                    "change_types": change_types,
                    "support_state": "unverified_for_build",
                }
            )
        else:
            unchanged += 1
    report = {
        "schema_version": "hwpx-agent.registry-drift/v1",
        "state": "pass",
        "baseline_state": "available",
        "baseline": registry_identity(baseline),
        "current": registry_identity(current),
        "summary": {
            "compared_capability_count": len(all_ids),
            "added_count": type_counts["added"],
            "removed_count": type_counts["removed"],
            "binding_changed_count": type_counts["binding_changed"],
            "parameter_changed_count": type_counts["parameter_changed"],
            "behavior_changed_count": type_counts["behavior_changed"],
            "unchanged_count": unchanged,
            "unverified_for_build_count": len(changes),
        },
        "changes": changes,
        "policy": policy,
    }
    validate_schema(report, DRIFT_SCHEMA, "registry drift report")
    return report


def clone_and_resign(
    envelope: dict[str, Any],
    private_key: Ed25519PrivateKey,
    payload_mutator: Any,
) -> dict[str, Any]:
    """Test helper: clone a valid payload, mutate it and return a fresh valid signature."""
    payload = deepcopy(envelope["payload"])
    payload_mutator(payload)
    return create_envelope(payload, private_key)
