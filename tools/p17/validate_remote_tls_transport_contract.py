"""Validate the P17 certificate-pinned TLS transport contract and component evidence."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re
import sys
import tomllib
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = "protocol/private/p17-remote-tls-transport-v1.json"
EVIDENCE_RELATIVE = (
    "implementation/p17/evidence/remote-tls/"
    "p17-remote-tls-transport.current-20260911.v1.json"
)
SOURCE_RELATIVE = "crates/remote-tls-transport/src/lib.rs"
TEST_RELATIVE = "crates/remote-tls-transport/tests/pinned_tls.rs"
EXPECTED_IMPLEMENTATION_FILES = [
    "Cargo.toml",
    "Cargo.lock",
    "crates/remote-tls-transport/Cargo.toml",
    SOURCE_RELATIVE,
    TEST_RELATIVE,
    "implementation/p17/P17-06_REMOTE_TLS_TRANSPORT_V19.md",
    EVIDENCE_RELATIVE,
    "protocol/migrations/p17-remote-tls-transport-v1.md",
    "tools/p17/tests/test_remote_tls_transport_contract.py",
    "tools/p17/validate_remote_tls_transport_contract.py",
]
EXPECTED_CHECKS = {
    "exact_pin_name_tls13_exchange": True,
    "normal_webpki_verification": True,
    "post_handshake_exact_leaf_sha256": True,
    "request_not_dispatched_on_wrong_pin_or_name": True,
    "remote_statuses_preserved": True,
    "trailing_plaintext_rejected": True,
    "ordinary_unavailable_endpoint_typed": True,
    "configuration_and_debug_bounded": True,
    "public_and_loopback_scopes_separated": True,
    "ip_literal_server_name_rejected": True,
    "malformed_certificate_and_frames_fail_closed": True,
}
EXPECTED_CLAIMS = {
    "current_pc_loopback_tls13_component": True,
    "synthetic_certificate_only": True,
    "actual_external_remote_network": False,
    "real_service_certificate": False,
    "real_service_credential": False,
    "credential_issuance_or_rotation": False,
    "registered_host": False,
    "production": False,
    "actual_hangul": False,
    "p17_06_complete": False,
    "product_complete": False,
}
EXPECTED_TESTS = {
    "exact_pin_name_and_tls13_exchange_succeeds",
    "wrong_pin_and_wrong_name_fail_before_request_dispatch",
    "remote_status_trailing_data_and_unavailable_endpoint_are_typed",
    "configuration_and_debug_are_bounded_and_redacted",
    "endpoint_scope_and_dns_identity_are_exact",
    "malformed_certificate_and_frame_inputs_fail_closed",
}


class ContractError(ValueError):
    """Bounded fail-closed validation error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ContractError(code)


def load_json_strict(path: Path, code: str) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    require(0 < len(raw) <= 131_072, f"{code}.size")

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            require(key not in value, f"{code}.duplicate")
            value[key] = item
        return value

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError(f"{code}.json") from error
    require(isinstance(value, dict), f"{code}.object")
    return value, raw


def validate_relative(relative: str) -> None:
    require(
        isinstance(relative, str)
        and 0 < len(relative) <= 240
        and "\\" not in relative
        and ":" not in relative
        and "\0" not in relative,
        "path.shape",
    )
    value = PurePosixPath(relative)
    require(
        not value.is_absolute()
        and value.as_posix() == relative
        and all(part not in ("", ".", "..") for part in value.parts),
        "path.escape",
    )


def bounded_file(root: Path, relative: str) -> Path:
    validate_relative(relative)
    resolved_root = root.resolve(strict=True)
    cursor = resolved_root
    for part in relative.split("/"):
        cursor /= part
        require(
            not cursor.is_symlink()
            and not (hasattr(cursor, "is_junction") and cursor.is_junction()),
            "path.link",
        )
    path = cursor.resolve(strict=True)
    require(
        resolved_root in path.parents
        and path.is_file()
        and 0 < path.stat().st_size <= 4_000_000,
        "path.file",
    )
    return path


def validate_contract_document(contract: dict[str, Any]) -> None:
    require(
        contract.get("schema_version") == "hwpx-agent.remote-tls-transport-contract/v1",
        "contract.schema",
    )
    require(
        contract.get("scope") == "current_pc_loopback_tls13_transport_component",
        "contract.scope",
    )
    require(
        contract.get("dependencies")
        == {
            "rustls": "0.23.43",
            "rustls_default_features": False,
            "rustls_features": ["ring", "std"],
            "rcgen_dev_only": "0.14.10",
            "rcgen_default_features": False,
            "rcgen_features": ["crypto", "ring"],
        },
        "contract.dependencies",
    )
    require(
        contract.get("configuration")
        == {
            "endpoint_is_exact_socket_address": True,
            "dns_resolution": False,
            "server_name_is_canonical_lowercase_dns_only": True,
            "ip_literal_server_name": False,
            "endpoint_scopes": ["public_remote", "loopback_qualification"],
            "public_remote_rejects_special_use_addresses": True,
            "loopback_qualification_requires_loopback_address": True,
            "timeout_milliseconds_minimum": 1,
            "timeout_milliseconds_maximum": 60000,
            "certificate_der_bytes_maximum": 32768,
            "debug_discloses_endpoint_name_or_pin": False,
        },
        "contract.configuration",
    )
    require(
        contract.get("tls")
        == {
            "protocol_versions": ["TLS1.3"],
            "crypto_provider": "ring",
            "ambient_system_or_bundled_roots": False,
            "pinned_der_is_only_root": True,
            "normal_webpki_name_validity_signature_verification": True,
            "post_handshake_exact_leaf_sha256_match": True,
            "custom_accept_all_verifier": False,
            "request_written_before_handshake_and_leaf_pin": False,
        },
        "contract.tls",
    )
    require(
        contract.get("wire")
        == {
            "trait": "local_sync::RemoteTransport",
            "framing": "remote-sync-wire/v1",
            "bounded_authorization_request_and_response": True,
            "unexpected_trailing_plaintext": "rejected",
            "tls_or_certificate_failure": "rejected",
            "ordinary_connect_or_io_failure": "unavailable",
            "remote_statuses_preserved": True,
        },
        "contract.wire",
    )
    require(
        contract.get("implementation_files") == EXPECTED_IMPLEMENTATION_FILES,
        "contract.implementation_files",
    )
    authorities = contract.get("external_authorities")
    require(
        isinstance(authorities, list)
        and len(authorities) == 2
        and authorities[0].get("url")
        == "https://docs.rs/rustls/0.23.43/rustls/struct.ConfigBuilder.html"
        and authorities[1].get("url")
        == "https://docs.rs/rustls/0.23.43/rustls/struct.RootCertStore.html",
        "contract.authorities",
    )
    require(
        contract.get("gate_decision")
        == {
            "component": "pass",
            "current_pc_loopback_tls13": True,
            "actual_external_remote_network": False,
            "real_service_certificate": False,
            "real_service_credential": False,
            "credential_issuance_or_rotation": False,
            "registered_host": False,
            "production": False,
            "p17_06_complete": False,
            "product_complete": False,
        },
        "contract.gate",
    )


def validate_evidence_document(evidence: dict[str, Any], raw: bytes) -> None:
    require(
        evidence.get("schema_version") == "hwpx-agent.remote-tls-transport-evidence/v1",
        "evidence.schema",
    )
    require(
        evidence.get("scope") == "current_pc_ephemeral_loopback_tls13_component",
        "evidence.scope",
    )
    require(
        evidence.get("target")
        == {
            "operating_system": "Windows",
            "rust_version": "1.96.0",
            "rustls_version": "0.23.43",
            "crypto_provider": "ring",
            "tls_versions": ["TLS1.3"],
            "network": "ephemeral_ipv4_loopback_only",
            "certificate": "per_test_synthetic_self_signed",
        },
        "evidence.target",
    )
    require(
        evidence.get("command")
        == "cargo test -p remote-tls-transport --all-targets --locked --offline",
        "evidence.command",
    )
    require(
        evidence.get("result")
        == {"state": "pass", "passed": 6, "failed": 0, "ignored": 0},
        "evidence.result",
    )
    require(evidence.get("checks") == EXPECTED_CHECKS, "evidence.checks")
    require(
        evidence.get("cleanup")
        == {
            "persistent_listener_created": False,
            "certificate_installed": False,
            "credential_created": False,
            "user_document_accessed": False,
        },
        "evidence.cleanup",
    )
    require(
        evidence.get("privacy")
        == {
            "raw_certificate_der_recorded": False,
            "certificate_pin_recorded": False,
            "authorization_header_recorded": False,
            "remote_endpoint_recorded": False,
            "secret_recorded": False,
        },
        "evidence.privacy",
    )
    require(evidence.get("claims") == EXPECTED_CLAIMS, "evidence.claims")
    lowered = raw.lower()
    for forbidden in (b"bearer ", b"begin certificate", b"aaa.bbb.ccc"):
        require(forbidden not in lowered, "evidence.secret")


def validate_source_text(source: str, tests: str) -> None:
    required_source = [
        "pub enum EndpointScope",
        "EndpointScope::PublicRemote => !is_public_remote_ip(endpoint.ip())",
        "EndpointScope::LoopbackQualification => !endpoint.ip().is_loopback()",
        "ServerName::DnsName(_)",
        "RootCertStore::empty()",
        ".add(certificate)",
        "with_protocol_versions(&[&version::TLS13])",
        "rustls::crypto::ring::default_provider()",
        "TcpStream::connect_timeout(&self.endpoint, self.timeout)",
        ".complete_io(&mut socket)",
        ".peer_certificates()",
        "actual_leaf_sha256 != self.expected_leaf_sha256",
        "write_request(&mut stream, authorization_header, request)",
        "read_response(&mut stream)",
        "Ok(_) => return Err(TransportFailure::Rejected)",
    ]
    for index, token in enumerate(required_source):
        require(token in source, f"source.required.{index}")
    for forbidden in (
        "with_custom_certificate_verifier",
        ".dangerous()",
        "ToSocketAddrs",
        "TcpStream::connect(",
        "TLS12",
    ):
        require(forbidden not in source, "source.forbidden")
    require(
        source.index("actual_leaf_sha256 != self.expected_leaf_sha256")
        < source.index("write_request(&mut stream, authorization_header, request)"),
        "source.dispatch_order",
    )
    names = set(re.findall(r"#\[test\]\s*fn\s+([a-z0-9_]+)", tests))
    require(names == EXPECTED_TESTS, "tests.coverage")


def validate_manifests(root: Path) -> None:
    root_manifest = tomllib.loads(bounded_file(root, "Cargo.toml").read_text("utf-8"))
    require(
        root_manifest["workspace"]["members"].count("crates/remote-tls-transport") == 1,
        "manifest.member",
    )
    dependencies = root_manifest["workspace"]["dependencies"]
    require(
        dependencies.get("rustls")
        == {"version": "=0.23.43", "default-features": False, "features": ["ring", "std"]},
        "manifest.rustls",
    )
    require(
        dependencies.get("rcgen")
        == {
            "version": "=0.14.10",
            "default-features": False,
            "features": ["crypto", "ring"],
        },
        "manifest.rcgen",
    )
    crate = tomllib.loads(
        bounded_file(root, "crates/remote-tls-transport/Cargo.toml").read_text("utf-8")
    )
    require(
        crate["dependencies"]
        == {
            "local-sync": {"version": "0.1.0", "path": "../local-sync"},
            "remote-credential-broker": {
                "version": "0.1.0",
                "path": "../remote-credential-broker",
            },
            "remote-credential-wire": {
                "version": "0.1.0",
                "path": "../remote-credential-wire",
            },
            "remote-sync-wire": {
                "version": "0.1.0",
                "path": "../remote-sync-wire",
            },
            "rustls": {"workspace": True},
            "sha2": {"workspace": True},
        },
        "crate.dependencies",
    )
    require(
        crate["dev-dependencies"]
        == {"hex": {"workspace": True}, "rcgen": {"workspace": True}},
        "crate.dev",
    )

    lock = tomllib.loads(bounded_file(root, "Cargo.lock").read_text("utf-8"))
    versions = {
        package["name"]: package["version"]
        for package in lock["package"]
        if package["name"] in {"rcgen", "rustls", "rustls-pki-types", "rustls-webpki", "ring"}
    }
    require(
        versions
        == {
            "rcgen": "0.14.10",
            "ring": "0.17.14",
            "rustls": "0.23.43",
            "rustls-pki-types": "1.15.1",
            "rustls-webpki": "0.103.15",
        },
        "lock.versions",
    )


def verify(root: Path = ROOT) -> dict[str, Any]:
    contract, _ = load_json_strict(bounded_file(root, CONTRACT_RELATIVE), "contract")
    evidence, evidence_raw = load_json_strict(
        bounded_file(root, EVIDENCE_RELATIVE), "evidence"
    )
    validate_contract_document(contract)
    validate_evidence_document(evidence, evidence_raw)
    for relative in EXPECTED_IMPLEMENTATION_FILES:
        bounded_file(root, relative)
    validate_manifests(root)
    source = bounded_file(root, SOURCE_RELATIVE).read_text("utf-8")
    tests = bounded_file(root, TEST_RELATIVE).read_text("utf-8")
    validate_source_text(source, tests)
    return {
        "state": "pass",
        "rust_tests": 6,
        "current_pc_loopback_tls13": True,
        "actual_external_remote_network": False,
        "production": False,
        "p17_06_complete": False,
        "product_complete": False,
    }


def main() -> int:
    try:
        result = verify()
    except (ContractError, OSError, KeyError, TypeError, tomllib.TOMLDecodeError) as error:
        print(f"P17_REMOTE_TLS_TRANSPORT_CONTRACT_FAIL code={error}", file=sys.stderr)
        return 1
    print(
        "P17_REMOTE_TLS_TRANSPORT_CONTRACT_PASS "
        f"rust_tests={result['rust_tests']} "
        f"external_remote={str(result['actual_external_remote_network']).lower()} "
        f"production={str(result['production']).lower()} "
        f"p17_06_complete={str(result['p17_06_complete']).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
