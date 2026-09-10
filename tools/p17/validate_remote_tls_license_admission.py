"""Validate exact-version ISC admission for the pinned TLS dependency chain."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tomllib
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = "protocol/private/p17-remote-tls-license-admission-v1.json"
EVIDENCE_RELATIVE = (
    "implementation/p17/evidence/remote-tls/"
    "p17-remote-tls-license-admission.current-20260911.v1.json"
)
EXPECTED_ALLOW = [
    "Apache-2.0",
    "Apache-2.0 WITH LLVM-exception",
    "BSD-3-Clause",
    "MIT",
    "MIT-0",
    "Unicode-3.0",
    "Zlib",
]
EXPECTED_PACKAGES = [
    {
        "crate": "ring@0.17.14",
        "name": "ring",
        "version": "0.17.14",
        "allow": ["ISC"],
        "license": "Apache-2.0 AND ISC",
        "checksum": "a4689e6c2294d81e88dc6261c768b63bc4fcdb852be6d1352498b114f61383b7",
        "license_file": "LICENSE",
        "license_file_bytes": 499,
        "license_file_sha256": (
            "b3d734001a94efff3579978d953391aa7115f877657d25eb54037a43875d078a"
        ),
    },
    {
        "crate": "rustls-webpki@0.103.15",
        "name": "rustls-webpki",
        "version": "0.103.15",
        "allow": ["ISC"],
        "license": "ISC",
        "checksum": "f3c3cf1d8b1e7d4927e2d154c3fcb02979afb9939629c62cd9048d4f07b60ac2",
        "license_file": "LICENSE",
        "license_file_bytes": 916,
        "license_file_sha256": (
            "5b698ca13897be3afdb7174256fa1574f8c6892b8bea1a66dd6469d3fe27885a"
        ),
    },
    {
        "crate": "untrusted@0.9.0",
        "name": "untrusted",
        "version": "0.9.0",
        "allow": ["ISC"],
        "license": "ISC",
        "checksum": "8ecb6da28b8a351d773b68d5825ac39017e680750f980f3a1a85cd8dd28a47c1",
        "license_file": "LICENSE.txt",
        "license_file_bytes": 769,
        "license_file_sha256": (
            "7abd9b6960dcf7d4d0a48606a5b71bfe37d472db68d70637f3a58a56785f1621"
        ),
    },
]
EXPECTED_IMPLEMENTATION_FILES = [
    "Cargo.lock",
    "Cargo.toml",
    "deny.toml",
    "implementation/p17/P17-06_REMOTE_TLS_LICENSE_ADMISSION_V20.md",
    EVIDENCE_RELATIVE,
    "protocol/migrations/p17-remote-tls-license-admission-v1.md",
    CONTRACT_RELATIVE,
    "tools/p17/tests/test_remote_tls_license_admission.py",
    "tools/p17/validate_remote_tls_license_admission.py",
]
REGISTRY = "registry+https://github.com/rust-lang/crates.io-index"


class LicenseAdmissionError(ValueError):
    """Bounded fail-closed validation error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise LicenseAdmissionError(code)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "json.duplicate")
        result[key] = value
    return result


def load_json_bytes(raw: bytes, code: str, maximum: int = 262_144) -> dict[str, Any]:
    require(0 < len(raw) <= maximum, f"{code}.size")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise LicenseAdmissionError(f"{code}.json") from error
    require(isinstance(value, dict), f"{code}.object")
    return value


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


def bounded_file(root: Path, relative: str, maximum: int = 4_000_000) -> Path:
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
        and 0 < path.stat().st_size <= maximum,
        "path.file",
    )
    return path


def load_json(root: Path, relative: str, code: str) -> tuple[dict[str, Any], bytes]:
    raw = bounded_file(root, relative).read_bytes()
    return load_json_bytes(raw, code), raw


def public_package(package: dict[str, Any]) -> dict[str, Any]:
    return {
        "crate": package["crate"],
        "allow": package["allow"],
        "package_license_expression": package["license"],
        "cargo_lock_checksum": package["checksum"],
        "license_file": package["license_file"],
        "license_file_bytes": package["license_file_bytes"],
        "license_file_sha256": package["license_file_sha256"],
    }


def evidence_package(package: dict[str, Any]) -> dict[str, Any]:
    return {
        "crate": package["crate"],
        "license_expression": package["license"],
        "license_file": package["license_file"],
        "license_file_bytes": package["license_file_bytes"],
        "license_file_sha256": package["license_file_sha256"],
    }


def validate_contract(contract: dict[str, Any]) -> None:
    require(
        set(contract)
        == {
            "schema_version",
            "contract_id",
            "scope",
            "policy",
            "exceptions",
            "implementation_files",
            "external_authorities",
            "gate_decision",
        },
        "contract.shape",
    )
    require(
        contract.get("schema_version")
        == "hwpx-agent.remote-tls-license-admission-contract/v1",
        "contract.schema",
    )
    require(
        contract.get("contract_id") == "p17.remote-tls-license-admission.v1",
        "contract.id",
    )
    require(
        contract.get("scope")
        == "exact_version_isc_admission_for_certificate_pinned_tls_dependency_chain",
        "contract.scope",
    )
    require(
        contract.get("policy")
        == {
            "confidence_threshold": 0.93,
            "global_allowlist_contains_isc": False,
            "exception_matching": "exact_crate_name_and_version",
            "wildcard_dependencies": "deny",
            "unknown_registry": "deny",
            "unknown_git": "deny",
            "allowed_registry": "https://github.com/rust-lang/crates.io-index",
        },
        "contract.policy",
    )
    require(
        contract.get("exceptions")
        == [public_package(package) for package in EXPECTED_PACKAGES],
        "contract.exceptions",
    )
    require(
        contract.get("implementation_files") == EXPECTED_IMPLEMENTATION_FILES,
        "contract.files",
    )
    authorities = contract.get("external_authorities")
    require(
        isinstance(authorities, list)
        and len(authorities) == 2
        and authorities[0].get("url")
        == "https://embarkstudios.github.io/cargo-deny/checks/licenses/cfg.html"
        and authorities[1].get("url")
        == "https://github.com/EmbarkStudios/cargo-deny/blob/main/deny.template.toml",
        "contract.authorities",
    )
    require(
        contract.get("gate_decision")
        == {
            "license_policy_component": "pass",
            "cargo_deny_all_current_locked_graph": True,
            "exact_package_license_files_current_pc": True,
            "global_isc_allowance": False,
            "actual_external_remote_network": False,
            "real_service_certificate": False,
            "real_service_credential": False,
            "credential_issuance_or_rotation": False,
            "production": False,
            "p17_06_complete": False,
            "product_complete": False,
        },
        "contract.gate",
    )


def validate_evidence(evidence: dict[str, Any], raw: bytes) -> None:
    require(
        set(evidence)
        == {
            "schema_version",
            "scope",
            "target",
            "command",
            "result",
            "packages",
            "privacy",
            "claims",
        },
        "evidence.shape",
    )
    require(
        evidence.get("schema_version")
        == "hwpx-agent.remote-tls-license-admission-evidence/v1",
        "evidence.schema",
    )
    require(
        evidence.get("scope")
        == "current_pc_exact_locked_tls_dependency_license_policy",
        "evidence.scope",
    )
    require(
        evidence.get("target")
        == {
            "operating_system": "Windows",
            "dependency_resolution": "Cargo.lock",
            "network": "offline",
            "cargo_deny_mode": "frozen",
        },
        "evidence.target",
    )
    require(evidence.get("command") == "cargo deny --frozen check all", "evidence.command")
    require(
        evidence.get("result")
        == {
            "state": "pass",
            "advisories": "pass",
            "bans": "pass",
            "licenses": "pass",
            "sources": "pass",
        },
        "evidence.result",
    )
    require(
        evidence.get("packages")
        == [evidence_package(package) for package in EXPECTED_PACKAGES],
        "evidence.packages",
    )
    require(
        evidence.get("privacy")
        == {
            "absolute_registry_path_recorded": False,
            "license_file_content_copied": False,
            "credential_recorded": False,
            "remote_endpoint_recorded": False,
            "secret_recorded": False,
        },
        "evidence.privacy",
    )
    require(
        evidence.get("claims")
        == {
            "current_locked_dependency_license_policy": True,
            "exact_version_exceptions_only": True,
            "global_isc_allowance": False,
            "actual_external_remote_network": False,
            "real_service_certificate": False,
            "real_service_credential": False,
            "credential_issuance_or_rotation": False,
            "production": False,
            "p17_06_complete": False,
            "product_complete": False,
        },
        "evidence.claims",
    )
    lowered = raw.lower()
    for forbidden in (b"bearer ", b"begin certificate", b"authorization:"):
        require(forbidden not in lowered, "evidence.secret")


def validate_deny_document(document: dict[str, Any]) -> None:
    require(
        set(document) == {"graph", "advisories", "licenses", "bans", "sources"},
        "deny.shape",
    )
    require(document.get("graph") == {"all-features": True}, "deny.graph")
    require(document.get("advisories") == {"yanked": "deny"}, "deny.advisories")
    licenses = document.get("licenses")
    require(isinstance(licenses, dict), "deny.licenses")
    require(
        set(licenses) == {"confidence-threshold", "allow", "exceptions", "private"},
        "deny.licenses_shape",
    )
    require(licenses.get("confidence-threshold") == 0.93, "deny.confidence")
    require(licenses.get("allow") == EXPECTED_ALLOW, "deny.allow")
    require("ISC" not in licenses.get("allow", []), "deny.global_isc")
    require(
        licenses.get("exceptions")
        == [
            {"allow": package["allow"], "crate": package["crate"]}
            for package in EXPECTED_PACKAGES
        ],
        "deny.exceptions",
    )
    require(licenses.get("private") == {"ignore": True}, "deny.private")
    require(
        document.get("bans")
        == {"multiple-versions": "warn", "wildcards": "deny", "highlight": "all"},
        "deny.bans",
    )
    require(
        document.get("sources")
        == {
            "unknown-registry": "deny",
            "unknown-git": "deny",
            "allow-registry": ["https://github.com/rust-lang/crates.io-index"],
        },
        "deny.sources",
    )


def validate_lock(document: dict[str, Any]) -> None:
    packages = document.get("package")
    require(isinstance(packages, list), "lock.packages")
    for expected in EXPECTED_PACKAGES:
        matches = [
            package
            for package in packages
            if isinstance(package, dict) and package.get("name") == expected["name"]
        ]
        require(len(matches) == 1, "lock.package_count")
        package = matches[0]
        require(package.get("version") == expected["version"], "lock.version")
        require(package.get("source") == REGISTRY, "lock.source")
        require(package.get("checksum") == expected["checksum"], "lock.checksum")


def cargo_metadata(root: Path) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["CARGO_TERM_COLOR"] = "never"
    try:
        result = subprocess.run(
            ["cargo", "metadata", "--locked", "--offline", "--format-version", "1"],
            cwd=root,
            env=environment,
            capture_output=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise LicenseAdmissionError("metadata.unavailable") from error
    require(result.returncode == 0, "metadata.exit")
    require(len(result.stderr) <= 131_072, "metadata.stderr")
    return load_json_bytes(result.stdout, "metadata", 16_000_000)


def validate_metadata_and_license_files(metadata: dict[str, Any]) -> None:
    packages = metadata.get("packages")
    require(isinstance(packages, list), "metadata.packages")
    for expected in EXPECTED_PACKAGES:
        matches = [
            package
            for package in packages
            if isinstance(package, dict) and package.get("name") == expected["name"]
        ]
        require(len(matches) == 1, "metadata.package_count")
        package = matches[0]
        require(package.get("version") == expected["version"], "metadata.version")
        require(package.get("source") == REGISTRY, "metadata.source")
        require(package.get("license") == expected["license"], "metadata.license")
        manifest = package.get("manifest_path")
        require(isinstance(manifest, str) and len(manifest) <= 4096, "metadata.manifest")
        license_path = Path(manifest).parent / expected["license_file"]
        require(
            license_path.name == expected["license_file"]
            and license_path.is_file()
            and not license_path.is_symlink(),
            "license_file.path",
        )
        raw = license_path.read_bytes()
        require(len(raw) == expected["license_file_bytes"], "license_file.bytes")
        require(digest(raw) == expected["license_file_sha256"], "license_file.digest")


def run_cargo_deny(root: Path) -> None:
    environment = os.environ.copy()
    environment["CARGO_TERM_COLOR"] = "never"
    try:
        result = subprocess.run(
            ["cargo", "deny", "--frozen", "check", "all"],
            cwd=root,
            env=environment,
            capture_output=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise LicenseAdmissionError("cargo_deny.unavailable") from error
    require(len(result.stdout) <= 1_000_000, "cargo_deny.stdout")
    require(len(result.stderr) <= 4_000_000, "cargo_deny.stderr")
    require(result.returncode == 0, "cargo_deny.exit")


def verify(root: Path = ROOT, *, execute_cargo_deny: bool = True) -> dict[str, Any]:
    contract, _ = load_json(root, CONTRACT_RELATIVE, "contract")
    evidence, evidence_raw = load_json(root, EVIDENCE_RELATIVE, "evidence")
    validate_contract(contract)
    validate_evidence(evidence, evidence_raw)
    for relative in EXPECTED_IMPLEMENTATION_FILES:
        bounded_file(root, relative)
    deny_document = tomllib.loads(bounded_file(root, "deny.toml").read_text("utf-8"))
    lock_document = tomllib.loads(bounded_file(root, "Cargo.lock").read_text("utf-8"))
    validate_deny_document(deny_document)
    validate_lock(lock_document)
    validate_metadata_and_license_files(cargo_metadata(root))
    if execute_cargo_deny:
        run_cargo_deny(root)
    return {
        "state": "pass",
        "package_count": len(EXPECTED_PACKAGES),
        "cargo_deny_all": execute_cargo_deny,
        "global_isc_allowance": False,
        "actual_external_remote_network": False,
        "production": False,
        "p17_06_complete": False,
        "product_complete": False,
    }


def main() -> int:
    try:
        result = verify()
    except (
        LicenseAdmissionError,
        OSError,
        KeyError,
        TypeError,
        tomllib.TOMLDecodeError,
    ) as error:
        print(f"P17_REMOTE_TLS_LICENSE_ADMISSION_FAIL code={error}", file=sys.stderr)
        return 1
    print(
        "P17_REMOTE_TLS_LICENSE_ADMISSION_PASS "
        f"packages={result['package_count']} "
        f"cargo_deny_all={str(result['cargo_deny_all']).lower()} "
        f"global_isc={str(result['global_isc_allowance']).lower()} "
        f"production={str(result['production']).lower()} "
        f"p17_06_complete={str(result['p17_06_complete']).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
